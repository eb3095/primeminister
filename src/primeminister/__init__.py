"""
PrimeMinister - AI Council Decision System

A CLI tool that uses a council of AI personalities with different perspectives
to provide well-rounded advice and decision-making support.
"""

__version__ = "1.0.0"
__author__ = "Eric Benner"
__email__ = "ebennerit@gmail.com"

from .config_manager import ConfigManager
from .logger import PrimeMinisterLogger

# Optional imports that require external dependencies
try:
    from .core import PrimeMinister, CouncilMember
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False
    PrimeMinister = None
    CouncilMember = None

__all__ = [
    'ConfigManager',
    'PrimeMinisterLogger'
]

if _CORE_AVAILABLE:
    __all__.extend(['PrimeMinister', 'CouncilMember'])
