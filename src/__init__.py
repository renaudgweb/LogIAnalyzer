"""
Log Analyzer with AI
~~~~~~~~~~~~~~~~~~~~

Système de surveillance et d'analyse automatique des logs Linux
avec intelligence artificielle (Mistral AI).

:copyright: (c) 2025
:license: MIT
"""

__version__ = "1.0.0"
__author__ = "renaudG"
__email__ = "your.email@example.com"

# Imports principaux pour faciliter l'utilisation du package
from .log_monitor import monitor_logs, analyze_logs_with_ai
from .config_loader import load_configuration
from .email_sender import send_email, send_daily_report

__all__ = [
    'monitor_logs',
    'analyze_logs_with_ai',
    'load_configuration',
    'send_email',
    'send_daily_report'
]