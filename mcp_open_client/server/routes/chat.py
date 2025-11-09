"""
Chat completion API routes
"""
import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from mcp_open_client.config import config_manager
from mcp_open_client.server.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """Chat completion endpoint - sends user message to configured LLM provider"""
    try:
        # Get current configuration
        config = config_manager.get_config()
        selected = config.get('selected_configuration', {})

        provider_id = selected.get('provider_id')
        main_model = selected.get('main_model')

        if not provider_id:
            raise HTTPException(status_code=400, detail="No provider configured")

        if not main_model:
            raise HTTPException(status_code=400, detail="No main model configured")

        # Get provider configuration
        provider = config_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

        # Get API key
        api_key = config_manager.get_provider_api_key(provider_id)
        if not api_key:
            raise HTTPException(status_code=400, detail=f"No API key configured for {provider_id}")

        logger.info(f"🤖 Chat request: {len(request.messages)} messages to {provider_id}/{main_model}")

        # Import here to avoid circular dependencies
        from mcp_open_client.services.chat_client import ChatClient

        # Convert ChatMessage objects to dictionaries
        messages_dict = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        # Make chat completion request to provider using async context manager
        async with ChatClient() as client:
            response_text = await client.create_completion(
                provider_id=provider_id,
                model=main_model,
                messages=messages_dict,
                api_key=api_key,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

        if not response_text:
            raise HTTPException(status_code=500, detail="Empty response from LLM provider")

        logger.info(f"✅ Chat response received: {len(response_text)} characters")

        return ChatCompletionResponse(
            response=response_text,
            model=main_model,
            provider=provider_id,
            message_count=len(request.messages)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions/stream")
async def chat_completions_stream(request: ChatCompletionRequest):
    """Streaming chat completion endpoint - sends user message to LLM provider with real-time streaming"""

    async def generate_stream():
        try:
            # Get current configuration
            config = config_manager.get_config()
            selected = config.get('selected_configuration', {})

            provider_id = selected.get('provider_id')
            main_model = selected.get('main_model')

            if not provider_id:
                yield f"data: {json.dumps({'error': 'No provider configured'})}\n\n"
                return

            if not main_model:
                yield f"data: {json.dumps({'error': 'No main model configured'})}\n\n"
                return

            # Get provider configuration
            provider = config_manager.get_provider(provider_id)
            if not provider:
                yield f"data: {json.dumps({'error': f'Provider {provider_id} not found'})}\n\n"
                return

            # Get API key
            api_key = config_manager.get_provider_api_key(provider_id)
            if not api_key:
                yield f"data: {json.dumps({'error': f'No API key configured for {provider_id}'})}\n\n"
                return

            logger.info(f"🤖 Streaming chat request: {len(request.messages)} messages to {provider_id}/{main_model}")

            # Import here to avoid circular dependencies
            from mcp_open_client.services.chat_client import ChatClient

            # Convert ChatMessage objects to dictionaries with tool call support
            messages_dict = []
            for msg in request.messages:
                msg_dict = {"role": msg.role}
                if msg.content:
                    msg_dict["content"] = msg.content
                if msg.tool_calls:
                    msg_dict["tool_calls"] = [tc.dict() for tc in msg.tool_calls]
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                if msg.name:
                    msg_dict["name"] = msg.name
                messages_dict.append(msg_dict)

            # Prepare tools for the request if provided
            tools_dict = None
            if request.tools:
                tools_dict = [tool.dict() for tool in request.tools]

            # Start streaming response
            yield "data: {\"type\": \"start\"}\n\n"

            # Make streaming chat completion request to provider
            async with ChatClient() as client:
                accumulated_content = ""
                accumulated_reasoning = ""
                active_tool_calls = {}

                async for data_chunk in client.create_streaming_completion(
                    provider_id=provider_id,
                    model=main_model,
                    messages=messages_dict,
                    api_key=api_key,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    tools=tools_dict,
                    tool_choice=request.tool_choice
                ):
                    if isinstance(data_chunk, dict):
                        # Handle structured data with separate reasoning/content/tool_calls
                        chunk_type = data_chunk.get("type", "content")
                        chunk_content = data_chunk.get("content", "")

                        if chunk_type == "reasoning":
                            accumulated_reasoning += chunk_content
                            chunk_data = {
                                "type": "reasoning_chunk",
                                "content": chunk_content,
                                "accumulated_reasoning": accumulated_reasoning
                            }
                        elif chunk_type == "tool_call_start":
                            # Start accumulating a new tool call
                            tool_call_id = data_chunk.get("tool_call_id")
                            function_name = data_chunk.get("function_name")
                            active_tool_calls[tool_call_id] = {
                                "id": tool_call_id,
                                "function_name": function_name,
                                "arguments": ""
                            }
                            chunk_data = {
                                "type": "tool_call_start",
                                "tool_call_id": tool_call_id,
                                "function_name": function_name
                            }
                        elif chunk_type == "tool_call_arguments":
                            # Add arguments to existing tool call
                            tool_call_id = data_chunk.get("tool_call_id")
                            arguments = data_chunk.get("arguments", "")
                            if tool_call_id in active_tool_calls:
                                active_tool_calls[tool_call_id]["arguments"] += arguments
                            chunk_data = {
                                "type": "tool_call_arguments",
                                "tool_call_id": tool_call_id,
                                "arguments": arguments,
                                "full_arguments": active_tool_calls.get(tool_call_id, {}).get("arguments", "")
                            }
                        else:  # content
                            accumulated_content += chunk_content
                            chunk_data = {
                                "type": "content_chunk",
                                "content": chunk_content,
                                "accumulated_content": accumulated_content
                            }
                    else:
                        # Handle legacy string chunks
                        accumulated_content += data_chunk
                        chunk_data = {
                            "type": "content_chunk",
                            "content": data_chunk,
                            "accumulated_content": accumulated_content
                        }

                    yield f"data: {json.dumps(chunk_data)}\n\n"

            # Execute tool calls if any were detected
            tool_results = []
            if active_tool_calls:
                logger.info(f"🔧 Executing {len(active_tool_calls)} tool calls")

                # Import tool simulator
                from mcp_open_client.services.tool_simulator import tool_simulator

                for tool_call_id, tool_call in active_tool_calls.items():
                    # Signal tool execution start
                    yield f"data: {json.dumps({'type': 'tool_execution_start', 'tool_call_id': tool_call_id, 'function_name': tool_call['function_name']})}\n\n"

                    # Execute the tool
                    try:
                        result = await tool_simulator.execute_tool(
                            tool_call_id=tool_call_id,
                            name=tool_call['function_name'],
                            arguments=tool_call['arguments']
                        )
                        tool_results.append(result)

                        # Signal tool execution completion
                        yield f"data: {json.dumps({'type': 'tool_execution_complete', 'tool_result': result})}\n\n"

                    except Exception as e:
                        error_result = {
                            "tool_call_id": tool_call_id,
                            "name": tool_call['function_name'],
                            "content": f"Error executing tool: {str(e)}",
                            "status": "error"
                        }
                        tool_results.append(error_result)
                        yield f"data: {json.dumps({'type': 'tool_execution_error', 'tool_result': error_result})}\n\n"

            # Send completion signal
            completion_data = {
                "type": "complete",
                "final_content": accumulated_content,
                "final_reasoning": accumulated_reasoning,
                "tool_calls": list(active_tool_calls.values()) if active_tool_calls else None,
                "tool_results": tool_results if tool_results else None,
                "model": main_model,
                "provider": provider_id,
                "message_count": len(request.messages)
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

            logger.info(f"✅ Streaming chat completed: {len(accumulated_content)} content chars, {len(accumulated_reasoning)} reasoning chars, {len(tool_results)} tool results")

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {e}")
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

        # End the stream
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )