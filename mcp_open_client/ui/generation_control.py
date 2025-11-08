"""
Módulo para control de generación y estado del sistema.
Extraído de chat_handlers.py para mejorar modularidad.
"""
from typing import Optional, Callable


# Generation control variables
generation_active = False
stop_generation = False


def set_stop_generation():
    """Set the stop generation flag"""
    global stop_generation
    stop_generation = True


def is_generation_stopped():
    """Check if generation should be stopped"""
    return stop_generation


def reset_generation_state():
    """Reset generation state"""
    global generation_active, stop_generation
    generation_active = False
    stop_generation = False


def set_generation_active(active: bool):
    """Set the generation active state"""
    global generation_active
    generation_active = active


def is_generation_active():
    """Check if generation is currently active"""
    return generation_active


# Callback management
stats_update_callback: Optional[Callable] = None
conversations_refresh_callback: Optional[Callable] = None


def set_stats_update_callback(callback: Callable) -> None:
    """Set the callback function to update stats"""
    global stats_update_callback
    stats_update_callback = callback


def set_conversations_refresh_callback(callback: Callable) -> None:
    """Set the callback function to refresh conversations list"""
    global conversations_refresh_callback
    conversations_refresh_callback = callback


def trigger_stats_update():
    """Trigger stats update if callback is available"""
    if stats_update_callback:
        stats_update_callback()


def trigger_conversations_refresh():
    """Trigger conversations refresh if callback is available"""
    if conversations_refresh_callback:
        conversations_refresh_callback()


def safe_delete_spinner(spinner):
    """Safely delete spinner and return None"""
    if spinner is not None:
        try:
            spinner.delete()
        except (ValueError, AttributeError) as e:
            # Spinner already deleted or not in parent list
            pass
        except Exception as e:
            print(f"Unexpected error deleting spinner: {e}")
    return None