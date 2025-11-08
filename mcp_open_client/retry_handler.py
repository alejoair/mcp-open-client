"""
Sistema de reintentos automáticos con backoff exponencial para errores de API.
Maneja errores 503 y otros errores temporales de manera inteligente.
"""
import asyncio
import logging
import time
from typing import Optional, Callable, Any, Dict
import openai

logger = logging.getLogger("RetryHandler")


class RetryConfig:
    """Configuración para sistema de reintentos"""

    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 10.0,
        max_delay: float = 120.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryState:
    """Estado actual de reintentos para mostrar en UI"""

    def __init__(self):
        self.attempt = 0
        self.max_attempts = 0
        self.next_retry_in = 0
        self.error_type = ""
        self.is_retrying = False
        self.last_error = ""


class RetryHandler:
    """Maneja reintentos automáticos con backoff exponencial"""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.state = RetryState()
        self.ui_callback: Optional[Callable[[RetryState], None]] = None

    def set_ui_callback(self, callback: Callable[[RetryState], None]):
        """Configura callback para actualizar UI con estado de reintentos"""
        self.ui_callback = callback

    def _update_ui(self):
        """Actualiza UI si hay callback configurado"""
        if self.ui_callback:
            try:
                self.ui_callback(self.state)
            except Exception as e:
                logger.warning(f"Error updating UI callback: {e}")

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determina si un error es reintentable"""
        if isinstance(error, openai.InternalServerError):
            # Error 503 y otros errores de servidor
            return True

        if isinstance(error, openai.RateLimitError):
            # Rate limiting
            return True

        if isinstance(error, openai.APITimeoutError):
            # Timeouts
            return True

        if isinstance(error, openai.APIConnectionError):
            # Problemas de conexión
            return True

        # Check for specific error codes in the message
        error_str = str(error).lower()
        retryable_indicators = [
            'too many requests',
            'high traffic',
            'queue exceeded',
            'service unavailable',
            'internal server error',
            'timeout',
            'connection error',
            'temporary failure'
        ]

        return any(indicator in error_str for indicator in retryable_indicators)

    def _get_retry_delay(self, attempt: int) -> float:
        """Calcula delay para el siguiente reintento con backoff exponencial"""
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)

        # Add jitter to avoid thundering herd
        if self.config.jitter:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(delay, 1.0)  # Minimum 1 second

    def _get_error_type(self, error: Exception) -> str:
        """Obtiene tipo de error para mostrar en UI"""
        if isinstance(error, openai.InternalServerError):
            if '503' in str(error):
                return "Alto Tráfico en Servidor"
            return "Error Interno del Servidor"

        if isinstance(error, openai.RateLimitError):
            return "Límite de Velocidad Excedido"

        if isinstance(error, openai.APITimeoutError):
            return "Timeout de Conexión"

        if isinstance(error, openai.APIConnectionError):
            return "Error de Conexión"

        return "Error Temporal"

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecuta una función con reintentos automáticos.

        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados

        Returns:
            Resultado de la función

        Raises:
            Exception: Si todos los reintentos fallan
        """
        self.state = RetryState()
        self.state.max_attempts = self.config.max_retries + 1

        last_error = None

        for attempt in range(self.config.max_retries + 1):
            self.state.attempt = attempt + 1
            self.state.is_retrying = attempt > 0

            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.config.max_retries}")

                result = await func(*args, **kwargs)

                # Success - reset state
                self.state.is_retrying = False
                self._update_ui()

                return result

            except Exception as e:
                last_error = e
                self.state.last_error = str(e)
                self.state.error_type = self._get_error_type(e)

                # Check if error is retryable
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error: {e}")
                    self.state.is_retrying = False
                    self._update_ui()
                    raise

                # Check if we've exhausted retries
                if attempt >= self.config.max_retries:
                    logger.error(f"Max retries ({self.config.max_retries}) exceeded")
                    self.state.is_retrying = False
                    self._update_ui()
                    raise

                # Calculate delay for next retry
                delay = self._get_retry_delay(attempt)
                self.state.next_retry_in = int(delay)

                logger.warning(f"Retryable error (attempt {attempt + 1}): {e}")
                logger.info(f"Retrying in {delay:.1f} seconds...")

                # Update UI with retry information
                self._update_ui()

                # Wait before retry
                await asyncio.sleep(delay)

        # This should never be reached, but just in case
        raise last_error or Exception("Unknown error in retry handler")


# Global retry handler instance
default_retry_handler = RetryHandler()


async def retry_on_api_errors(func: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Decorator function para reintentos automáticos.

    Usage:
        result = await retry_on_api_errors(api_client.chat_completion, messages, tools=tools)
    """
    return await default_retry_handler.execute_with_retry(func, *args, **kwargs)


def set_retry_ui_callback(callback: Callable[[RetryState], None]):
    """Configura callback global para actualizar UI"""
    default_retry_handler.set_ui_callback(callback)


def configure_retry_settings(
    max_retries: int = 5,
    initial_delay: float = 10.0,
    max_delay: float = 120.0
):
    """Configura settings globales de reintentos"""
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay
    )
    default_retry_handler.config = config
    logger.info(f"Retry settings updated: max_retries={max_retries}, initial_delay={initial_delay}s")