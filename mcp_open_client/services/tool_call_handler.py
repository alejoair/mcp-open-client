"""
Tool Call Handler - Manages tool execution and recursive tool call loops
"""
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from mcp_open_client.services.chat_client import ChatClient
from mcp_open_client.services.tool_simulator import tool_simulator

logger = logging.getLogger(__name__)

class ToolCallHandler:
    """Handles tool call execution and recursive loops"""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations

    async def execute_tool_calls_with_followup(
        self,
        active_tool_calls: Dict[str, Any],
        messages: List[Dict[str, Any]],
        provider_id: str,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute tool calls and handle recursive followup calls with the model.

        Args:
            active_tool_calls: Dictionary of tool calls to execute
            messages: Original conversation messages
            temperature: Model temperature
            max_tokens: Maximum tokens for model response

        Yields:
            Server-sent event data strings
        """
        current_messages = list(messages)
        iteration = 0
        accumulated_content = ""
        accumulated_reasoning = ""

        # Execute initial tool calls
        tool_results = await self._execute_tools(active_tool_calls)

        # Special handling for respond_to_user tool
        for result in tool_results:
            if result.get('name') == 'respond_to_user' and result.get('status') == 'success':
                accumulated_content = result.get('content', '')
                logger.info(f"📝 respond_to_user result: {accumulated_content}")

        # Yield tool execution events
        for event in self._yield_tool_events(active_tool_calls, tool_results):
            yield event

        while tool_results and iteration < self.max_iterations:
            iteration += 1
            logger.info(f"🔄 Tool followup iteration {iteration}/{self.max_iterations}")

            # Add assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "content": accumulated_content if accumulated_content else None,
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call_data.get('function_name', tool_call_data.get('name')),
                            "arguments": tool_call_data.get('arguments', '{}')
                        }
                    }
                    for tool_call_id, tool_call_data in active_tool_calls.items()
                ]
            }
            current_messages.append(assistant_msg)

            # Add tool result messages
            for result in tool_results:
                tool_msg = {
                    "role": "tool",
                    "content": result['content'],
                    "tool_call_id": result['tool_call_id']
                }
                current_messages.append(tool_msg)

            # Signal followup start
            yield f"data: {json.dumps({'type': 'tool_followup_start', 'iteration': iteration})}\n\n"

            try:
                # Get model response to tool results
                new_tool_calls = {}
                response_content = ""
                response_reasoning = ""

                async with ChatClient() as client:
                    # Import default tools
                    from mcp_open_client.services.default_tools import get_default_tools
                    tools = get_default_tools()

                    async for chunk in client.create_streaming_completion(
                        provider_id=provider_id,
                        model=model,
                        messages=current_messages,
                        api_key=api_key,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=tools
                    ):
                        if chunk['type'] == 'reasoning':
                            response_reasoning += chunk.get('content', '')
                            yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': chunk.get('content', ''), 'accumulated_reasoning': response_reasoning})}\n\n"

                        elif chunk['type'] == 'content':
                            response_content += chunk.get('content', '')
                            yield f"data: {json.dumps({'type': 'content_chunk', 'content': chunk.get('content', ''), 'accumulated_content': response_content})}\n\n"

                        elif chunk['type'] == 'tool_calls':
                            # Handle new tool calls from model response
                            tool_calls = chunk.get('tool_calls', [])
                            for tool_call in tool_calls:
                                if 'id' in tool_call and 'function' in tool_call:
                                    new_tool_calls[tool_call['id']] = {
                                        'function_name': tool_call['function'].get('name', ''),
                                        'arguments': tool_call['function'].get('arguments', '{}')
                                    }

                            # Yield tool call start events
                            for tool_call_id, tool_data in new_tool_calls.items():
                                yield f"data: {json.dumps({'type': 'tool_call_start', 'tool_call_id': tool_call_id, 'function_name': tool_data['function_name']})}\n\n"

                # Update accumulated content
                accumulated_content = response_content
                accumulated_reasoning = response_reasoning

                # If no new tool calls, break the loop
                if not new_tool_calls:
                    logger.info("✅ No more tool calls, ending followup loop")
                    break

                # Execute new tool calls for next iteration
                logger.info(f"🔧 Executing {len(new_tool_calls)} new tool calls in iteration {iteration}")
                active_tool_calls = new_tool_calls
                tool_results = await self._execute_tools(active_tool_calls)

                # Yield tool execution events
                for event in self._yield_tool_events(active_tool_calls, tool_results):
                    yield event

            except Exception as e:
                logger.error(f"❌ Error in tool followup iteration {iteration}: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': f'Tool followup iteration {iteration} failed: {str(e)}'})}\n\n"
                break

        if iteration >= self.max_iterations:
            logger.warning(f"⚠️  Reached maximum tool call iterations ({self.max_iterations})")
            yield f"data: {json.dumps({'type': 'warning', 'message': f'Reached maximum tool call iterations ({self.max_iterations})'})}\n\n"

        # Send final completion
        yield f"data: {json.dumps({'type': 'tool_followup_complete', 'final_content': accumulated_content, 'final_reasoning': accumulated_reasoning, 'iterations': iteration})}\n\n"

        # Send complete event that frontend expects
        yield f"data: {json.dumps({'type': 'complete', 'final_content': accumulated_content, 'final_reasoning': accumulated_reasoning, 'tool_calls': [], 'tool_results': []})}\n\n"

    async def _execute_tools(self, tool_calls: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a batch of tool calls"""
        results = []

        for tool_call_id, tool_call in tool_calls.items():
            try:
                result = await tool_simulator.execute_tool(
                    tool_call_id=tool_call_id,
                    name=tool_call.get('function_name', tool_call.get('name')),
                    arguments=tool_call.get('arguments', '{}')
                )
                results.append(result)
            except Exception as e:
                error_result = {
                    "tool_call_id": tool_call_id,
                    "name": tool_call.get('function_name', tool_call.get('name')),
                    "content": f"Error executing tool: {str(e)}",
                    "status": "error"
                }
                results.append(error_result)

        return results

    def _yield_tool_events(self, tool_calls: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
        """Generate tool execution events"""
        events = []

        for tool_call_id, tool_call in tool_calls.items():
            # Tool execution start
            events.append(f"data: {json.dumps({'type': 'tool_execution_start', 'tool_call_id': tool_call_id, 'function_name': tool_call.get('function_name', tool_call.get('name'))})}\n\n")

        for result in results:
            if result.get('status') == 'error':
                # Tool execution error
                events.append(f"data: {json.dumps({'type': 'tool_execution_error', 'tool_result': result})}\n\n")
            else:
                # Tool execution complete
                events.append(f"data: {json.dumps({'type': 'tool_execution_complete', 'tool_result': result})}\n\n")

        return events

# Global instance
tool_call_handler = ToolCallHandler()