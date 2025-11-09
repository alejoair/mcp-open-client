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
from mcp_open_client.services.default_tools import get_default_tools
from mcp_open_client.services.tool_call_handler import tool_call_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """Chat completion endpoint - sends user message to configured LLM provider"""
    try:
        # Get current configuration
        config = config_manager.get_config()
        selected_config = config.get('selected_configuration', {})

        if not selected_config.get('provider_id'):
            raise HTTPException(status_code=400, detail="No provider selected")
        if not selected_config.get('main_model'):
            raise HTTPException(status_code=400, detail="No model selected")

        logger.info(f"Chat completion request for {len(request.messages)} messages")
        logger.info(f"Using provider: {selected_config['provider_id']}, model: {selected_config['main_model']}")

        # Import here to avoid circular dependencies
        from mcp_open_client.services.chat_client import ChatClient

        async with ChatClient() as client:
            # Convert ChatMessage objects to dictionaries
            messages_dict = []
            for msg in request.messages:
                msg_dict = {"role": msg.role}
                if msg.content:
                    msg_dict["content"] = msg.content
                if msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": tc.function
                        } for tc in msg.tool_calls
                    ]
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                messages_dict.append(msg_dict)

            # Add tools to the request
            tools = get_default_tools()

            # Get API key for ChatClient
            api_key = config_manager.get_provider_api_key(selected_config['provider_id'])

            # Make request to provider
            response = await client.create_completion(
                provider_id=selected_config['provider_id'],
                model=selected_config['main_model'],
                api_key=api_key,
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=tools
            )

            return ChatCompletionResponse(
                id=response.get('id', 'chatcmpl-' + str(hash(str(messages_dict)))),
                object="chat.completion",
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.get('content', ''),
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": response.get('usage', {}).get('prompt_tokens', 0),
                    "completion_tokens": response.get('usage', {}).get('completion_tokens', 0),
                    "total_tokens": response.get('usage', {}).get('total_tokens', 0)
                }
            )

    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/completions/stream")
async def stream_chat_completions(request: ChatCompletionRequest):
    """Streaming chat completion endpoint with full tool call support"""

    async def generate():
        try:
            # Get current configuration
            config = config_manager.get_config()
            selected_config = config.get('selected_configuration', {})

            if not selected_config.get('provider_id'):
                yield f"data: {json.dumps({'type': 'error', 'error': 'No provider selected'})}\n\n"
                return
            if not selected_config.get('main_model'):
                yield f"data: {json.dumps({'type': 'error', 'error': 'No model selected'})}\n\n"
                return

            logger.info(f"Streaming chat completion for {len(request.messages)} messages")
            logger.info(f"Using provider: {selected_config['provider_id']}, model: {selected_config['main_model']}")

            # Import here to avoid circular dependencies
            from mcp_open_client.services.chat_client import ChatClient

            # Convert ChatMessage objects to dictionaries
            messages_dict = []
            for msg in request.messages:
                msg_dict = {"role": msg.role}
                if msg.content:
                    msg_dict["content"] = msg.content
                if msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": tc.function
                        } for tc in msg.tool_calls
                    ]
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                messages_dict.append(msg_dict)

            # Add tools to the request
            tools = get_default_tools()

            # Track tool calls and accumulated content
            active_tool_calls = {}
            accumulated_content = ""
            accumulated_reasoning = ""

            # Stream initial response from model
            async with ChatClient() as client:
                # Get API key for ChatClient
                api_key = config_manager.get_provider_api_key(selected_config['provider_id'])

                async for chunk in client.create_streaming_completion(
                    provider_id=selected_config['provider_id'],
                    model=selected_config['main_model'],
                    api_key=api_key,
                    messages=messages_dict,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    tools=tools
                ):
                    if chunk['type'] == 'reasoning':
                        accumulated_reasoning += chunk.get('content', '')
                        yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': chunk.get('content', ''), 'accumulated_reasoning': accumulated_reasoning})}\n\n"

                    elif chunk['type'] == 'content':
                        accumulated_content += chunk.get('content', '')
                        yield f"data: {json.dumps({'type': 'content_chunk', 'content': chunk.get('content', ''), 'accumulated_content': accumulated_content})}\n\n"

                    elif chunk['type'] == 'tool_call_start':
                        # Handle incremental tool call start
                        tool_call_id = chunk.get('tool_call_id', '')
                        function_name = chunk.get('function_name', '')

                        if tool_call_id:
                            active_tool_calls[tool_call_id] = {
                                'function_name': function_name,
                                'arguments': ''
                            }

                        # Yield tool call start event with initial arguments
                        yield f"data: {json.dumps({'type': 'tool_call_start', 'tool_call_id': tool_call_id, 'function_name': function_name, 'arguments': ''})}\n\n"

                    elif chunk['type'] == 'tool_call_arguments':
                        # Handle incremental tool call arguments
                        tool_call_id = chunk.get('tool_call_id', '')
                        arguments = chunk.get('arguments', '')

                        if tool_call_id in active_tool_calls:
                            active_tool_calls[tool_call_id]['arguments'] += arguments

                            # Yield tool call arguments update event to frontend
                            yield f"data: {json.dumps({'type': 'tool_call_arguments', 'tool_call_id': tool_call_id, 'arguments': arguments, 'accumulated_arguments': active_tool_calls[tool_call_id]['arguments']})}\n\n"

            # Handle tool execution and recursive followup
            if active_tool_calls:
                # Validate and cleanup tool calls before processing
                valid_tool_calls = {}
                for tool_call_id, tool_call in active_tool_calls.items():
                    # Ensure arguments is valid JSON
                    arguments = tool_call.get('arguments', '').strip()
                    if not arguments:
                        arguments = '{}'

                    # Validate JSON format
                    try:
                        json.loads(arguments)
                        valid_tool_calls[tool_call_id] = {
                            'function_name': tool_call.get('function_name', ''),
                            'arguments': arguments
                        }
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Invalid JSON arguments for tool {tool_call_id}: {arguments}")
                        # Use empty object for invalid JSON
                        valid_tool_calls[tool_call_id] = {
                            'function_name': tool_call.get('function_name', ''),
                            'arguments': '{}'
                        }

                if valid_tool_calls:
                    logger.info(f"🔧 Processing {len(valid_tool_calls)} valid tool calls with recursive followup")

                    # Log detailed tool call information
                    for tool_call_id, tool_call in valid_tool_calls.items():
                        function_name = tool_call.get('function_name', '')
                        arguments = tool_call.get('arguments', '{}')
                        logger.info(f"📋 Tool Call: {function_name} | ID: {tool_call_id} | Arguments: {arguments}")

                    # Get API key
                    api_key = config_manager.get_provider_api_key(selected_config['provider_id'])

                    async for event in tool_call_handler.execute_tool_calls_with_followup(
                        active_tool_calls=valid_tool_calls,
                        messages=messages_dict,
                        provider_id=selected_config['provider_id'],
                        model=selected_config['main_model'],
                        api_key=api_key,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    ):
                        yield event

            else:
                # No tool calls, send completion signal
                completion_data = {
                    "type": "complete",
                    "final_content": accumulated_content,
                    "final_reasoning": accumulated_reasoning,
                    "tool_calls": [],
                    "tool_results": []
                }
                yield f"data: {json.dumps(completion_data)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")