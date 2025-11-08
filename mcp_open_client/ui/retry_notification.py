"""
Componente UI para mostrar notificaciones de reintentos automáticos.
"""
import asyncio
from typing import Optional, Callable
from nicegui import ui
import time


class RetryNotification:
    """Maneja notificaciones de reintentos en la UI"""

    def __init__(self):
        self.notification: Optional[ui.notification] = None
        self.retry_active = False
        self.retry_timer = None
        self.countdown_timer = None

    def show_retry_notification(self, attempt: int, max_attempts: int, next_retry_in: int, error_type: str = "Alto Tráfico"):
        """
        Muestra notificación de reintento con countdown.

        Args:
            attempt: Intento actual
            max_attempts: Máximo de intentos
            next_retry_in: Segundos hasta el próximo intento
            error_type: Tipo de error para mostrar
        """
        if self.notification:
            self.notification.dismiss()

        self.retry_active = True
        self.notification = ui.notification(
            f'{error_type}: Reintentando en {next_retry_in}s (Intento {attempt}/{max_attempts})',
            type='warning',
            timeout=next_retry_in * 1000,  # timeout en milliseconds
            icon='schedule'
        )

        # Start countdown timer
        self._start_countdown(next_retry_in, attempt, max_attempts, error_type)

    def _start_countdown(self, initial_seconds: int, attempt: int, max_attempts: int, error_type: str):
        """Inicia countdown en la notificación"""
        remaining = initial_seconds

        def update_countdown():
            nonlocal remaining
            if remaining > 0 and self.notification and self.retry_active:
                self.notification.message = f'{error_type}: Reintentando en {remaining}s (Intento {attempt}/{max_attempts})'
                remaining -= 1
                # Schedule next update
                if self.countdown_timer:
                    self.countdown_timer.cancel()
                self.countdown_timer = ui.timer(1.0, update_countdown, once=True)
            else:
                if self.notification and self.retry_active:
                    self.notification.message = f'{error_type}: Reintentando ahora... (Intento {attempt}/{max_attempts})'

        update_countdown()

    def show_retry_in_progress(self, attempt: int, max_attempts: int):
        """Muestra notificación de reintento en progreso"""
        if self.notification:
            self.notification.dismiss()

        self.notification = ui.notification(
            f'Reintentando solicitud... (Intento {attempt}/{max_attempts})',
            type='info',
            timeout=10000,  # 10 segundos
            icon='refresh'
        )

    def show_retry_success(self):
        """Muestra notificación de éxito después de reintento"""
        self.retry_active = False
        if self.countdown_timer:
            self.countdown_timer.cancel()
            self.countdown_timer = None

        if self.notification:
            self.notification.dismiss()

        ui.notification(
            'Conexión reestablecida exitosamente',
            type='positive',
            timeout=3000,
            icon='check_circle'
        )
        self.notification = None

    def show_retry_failed(self, max_attempts: int):
        """Muestra notificación de fallo después de todos los reintentos"""
        self.retry_active = False
        if self.countdown_timer:
            self.countdown_timer.cancel()
            self.countdown_timer = None

        if self.notification:
            self.notification.dismiss()

        self.notification = ui.notification(
            f'Error: No se pudo conectar después de {max_attempts} intentos. Revisa la configuración del servidor.',
            type='negative',
            timeout=8000,
            icon='error'
        )

    def dismiss(self):
        """Dismisses current notification"""
        self.retry_active = False
        if self.countdown_timer:
            self.countdown_timer.cancel()
            self.countdown_timer = None
        if self.notification:
            self.notification.dismiss()
            self.notification = None


# Global instance
retry_notification = RetryNotification()


def show_retry_notification(attempt: int, max_attempts: int, next_retry_in: int, error_type: str = "Alto Tráfico"):
    """Función global para mostrar notificación de reintento"""
    retry_notification.show_retry_notification(attempt, max_attempts, next_retry_in, error_type)


def show_retry_in_progress(attempt: int, max_attempts: int):
    """Función global para mostrar reintento en progreso"""
    retry_notification.show_retry_in_progress(attempt, max_attempts)


def show_retry_success():
    """Función global para mostrar éxito de reintento"""
    retry_notification.show_retry_success()


def show_retry_failed(max_attempts: int):
    """Función global para mostrar fallo de reintentos"""
    retry_notification.show_retry_failed(max_attempts)


def dismiss_retry_notification():
    """Función global para dismissar notificación"""
    retry_notification.dismiss()