# data-access/repositories/base_repository.py

from typing import TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC, abstractmethod
import asyncpg
from engine.state.encryption import get_encryptor

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Base repository with encryption support
    
    All repositories inherit from this to get
    automatic state encryption/decryption
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        self.encryptor = get_encryptor()
    
    def _encrypt_algorithm_state(self, state: Dict[str, Any]) -> bytes:
        """Encrypt algorithm state before DB storage"""
        return self.encryptor.encrypt_state(state)
    
    def _decrypt_algorithm_state(self, encrypted: bytes) -> Dict[str, Any]:
        """Decrypt algorithm state from DB"""
        if not encrypted:
            return {}
        return self.encryptor.decrypt_state(encrypted)
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """Find entity by ID"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> str:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update entity"""
        pass
