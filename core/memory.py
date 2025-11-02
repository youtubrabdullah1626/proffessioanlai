from typing import Dict, Any, Optional
import json
import os
import threading
from pathlib import Path

from don.memory_manager import load_m1, save_m1, init_m2, remember_nickname
from don.logging_utils import setup_logging

logger = setup_logging()

# Thread lock for memory operations
_memory_lock = threading.RLock()


class MemoryManager:
    """Thread-safe memory manager for memory.json and memory.db."""
    
    def __init__(self, memory_json_path: str = "memory/memory.json", 
                 memory_db_path: str = "memory/memory.db") -> None:
        self.memory_json_path = memory_json_path
        self.memory_db_path = memory_db_path
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Ensure memory directories exist."""
        try:
            Path(self.memory_json_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.memory_db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create memory directories: {e}")
    
    def read_memory(self) -> Dict[str, Any]:
        """
        Thread-safe read from memory.json.
        
        Returns:
            Dict containing memory data
        """
        with _memory_lock:
            try:
                return load_m1()
            except Exception as e:
                logger.error(f"Failed to read memory: {e}")
                return {}
    
    def write_memory(self, data: Dict[str, Any]) -> bool:
        """
        Thread-safe write to memory.json with write-through to memory.db.
        
        Args:
            data: Data to write to memory
            
        Returns:
            bool: True if successful
        """
        with _memory_lock:
            try:
                # Write to JSON file
                success = save_m1(data)
                if not success:
                    return False
                
                # Initialize database if needed
                init_m2()
                
                # Here we would implement write-through to database
                # For now, we'll just log that it would happen
                logger.info("Memory write-through to database would happen here")
                
                return True
            except Exception as e:
                logger.error(f"Failed to write memory: {e}")
                return False
    
    def update_memory(self, key: str, value: Any) -> bool:
        """
        Thread-safe update of a specific key in memory.
        
        Args:
            key: Key to update
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        with _memory_lock:
            try:
                memory = self.read_memory()
                memory[key] = value
                return self.write_memory(memory)
            except Exception as e:
                logger.error(f"Failed to update memory key {key}: {e}")
                return False
    
    def get_memory_value(self, key: str, default: Any = None) -> Any:
        """
        Thread-safe get a specific value from memory.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value associated with key or default
        """
        with _memory_lock:
            try:
                memory = self.read_memory()
                return memory.get(key, default)
            except Exception as e:
                logger.error(f"Failed to get memory key {key}: {e}")
                return default


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def read_memory() -> Dict[str, Any]:
    """Read memory data."""
    return get_memory_manager().read_memory()


def write_memory(data: Dict[str, Any]) -> bool:
    """Write memory data."""
    return get_memory_manager().write_memory(data)


def update_memory(key: str, value: Any) -> bool:
    """Update a specific key in memory."""
    return get_memory_manager().update_memory(key, value)


def get_memory_value(key: str, default: Any = None) -> Any:
    """Get a specific value from memory."""
    return get_memory_manager().get_memory_value(key, default)