"""
UI configuration manager
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UIManager:
    """Manages UI configuration settings"""

    def __init__(self, config_data: Dict[str, Any]):
        self._config = config_data

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self._config.get('ui', {})

    def update_ui_config(self, **kwargs) -> bool:
        """Update UI configuration"""
        ui_config = self._config.setdefault('ui', {})

        for key, value in kwargs.items():
            if key in ['left_sidebar_collapsed', 'right_sidebar_collapsed',
                      'bottom_panel_collapsed', 'theme_mode']:
                ui_config[key] = value

        return True

    def get_default_ui_config(self) -> Dict[str, Any]:
        """Get default UI configuration"""
        return {
            "left_sidebar_collapsed": False,
            "right_sidebar_collapsed": False,
            "bottom_panel_collapsed": True,
            "theme_mode": "dark"
        }