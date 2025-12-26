# backend/app/services/automation/__init__.py
"""
Automation services package
Contains browser automation and quick apply form automation
"""

from .browser_automation_service import BrowserAutomationService, get_browser_automation_config
from .quick_apply_service import QuickApplyService
from .automation_service import AutomationService

__all__ = ['BrowserAutomationService', 'QuickApplyService', 'get_browser_automation_config', 'AutomationService']
