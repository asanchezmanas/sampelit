# engine/core/__init__.py

"""
Samplit Optimization Engine - Core Module

⚠️  CONFIDENTIAL - PROPRIETARY TECHNOLOGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This module contains Samplit's proprietary optimization algorithms.

UNAUTHORIZED ACCESS, USE, OR DISTRIBUTION IS STRICTLY PROHIBITED.

Copyright (c) 2024 Samplit Technologies. All rights reserved.

Trade Secret Protection:
- These algorithms are protected as trade secrets
- Reverse engineering is prohibited
- Implementation details are confidential

For licensing: licensing@samplit.com
"""

from typing import Dict, Any
from .allocators._registry import get_allocator as _get_allocator

__all__ = ['_get_allocator']

# Prevent inspection
def __dir__():
    return []
