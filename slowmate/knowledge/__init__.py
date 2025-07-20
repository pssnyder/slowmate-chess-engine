"""
SlowMate Chess Engine - Knowledge Base Module

This module provides opening book and endgame pattern knowledge to enhance
move selection beyond pure tactical calculation.

Architecture:
- Independent, fast-access move reference libraries
- Testing isolation with DEBUG_CONFIG toggles
- Comprehensive coverage with intelligent weighting
- Performance optimized for tournament play
"""

from .opening_book import OpeningBook
from .opening_weights import OpeningWeights
from .endgame_patterns import EndgamePatterns
from .endgame_tactics import EndgameTactics
from .middlegame_tactics import MiddlegameTactics
from .knowledge_base import KnowledgeBase

__version__ = "0.1.03"
__all__ = [
    'OpeningBook',
    'OpeningWeights', 
    'EndgamePatterns',
    'EndgameTactics',
    'MiddlegameTactics',
    'KnowledgeBase'
]
