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

            # Convert ChatMessage objects to dictionaries
            messages_dict = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]

            # Start streaming response
            yield "data: {\"type\": \"start\"}\n\n"

            # Make streaming chat completion request to provider
            async with ChatClient() as client:
                accumulated_content = ""
                accumulated_reasoning = ""

                async for data_chunk in client.create_streaming_completion(
                    provider_id=provider_id,
                    model=main_model,
                    messages=messages_dict,
                    api_key=api_key,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    if isinstance(data_chunk, dict):
                        # Handle structured data with separate reasoning/content
                        chunk_type = data_chunk.get("type", "content")
                        chunk_content = data_chunk.get("content", "")

                        if chunk_type == "reasoning":
                            accumulated_reasoning += chunk_content
                            chunk_data = {
                                "type": "reasoning_chunk",
                                "content": chunk_content,
                                "accumulated_reasoning": accumulated_reasoning
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

            # Send completion signal
            completion_data = {
                "type": "complete",
                "final_content": accumulated_content,
                "final_reasoning": accumulated_reasoning,
                "model": main_model,
                "provider": provider_id,
                "message_count": len(request.messages)
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

            logger.info(f"✅ Streaming chat completed: {len(accumulated_content)} content chars, {len(accumulated_reasoning)} reasoning chars")

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