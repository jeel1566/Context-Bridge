"""
Cosmos DB Service for Context Bridge

Provides persistent storage for memories, users, and shares.
Implements fallback to in-memory storage for local development.
"""

import os
import logging
from typing import Optional, Dict, List, Any, TypeVar, Generic
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Dict[str, Any])


class StorageService(ABC, Generic[T]):
    """Abstract base class for storage operations."""
    
    @abstractmethod
    async def create(self, item: T) -> T:
        """Create a new item."""
        pass
    
    @abstractmethod
    async def read(self, item_id: str, partition_key: Optional[str] = None) -> Optional[T]:
        """Read an item by ID."""
        pass
    
    @abstractmethod
    async def update(self, item_id: str, item: T, partition_key: Optional[str] = None) -> T:
        """Update an existing item."""
        pass
    
    @abstractmethod
    async def delete(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        """Delete an item."""
        pass
    
    @abstractmethod
    async def query(self, query: str, parameters: Optional[List[Dict]] = None) -> List[T]:
        """Query items."""
        pass


class InMemoryStorage(StorageService[T]):
    """
    In-memory storage implementation for local development.
    
    WARNING: Data is lost when the process restarts.
    Use only for development and testing.
    """
    
    def __init__(self, container_name: str):
        self._container_name = container_name
        self._store: Dict[str, T] = {}
        logger.warning(f"Using in-memory storage for '{container_name}' - data will not persist!")
    
    async def create(self, item: T) -> T:
        item_id = item.get('id')
        if not item_id:
            raise ValueError("Item must have an 'id' field")
        
        if item_id in self._store:
            raise ValueError(f"Item with id '{item_id}' already exists")
        
        self._store[item_id] = item
        return item
    
    async def read(self, item_id: str, partition_key: Optional[str] = None) -> Optional[T]:
        return self._store.get(item_id)
    
    async def update(self, item_id: str, item: T, partition_key: Optional[str] = None) -> T:
        if item_id not in self._store:
            raise ValueError(f"Item with id '{item_id}' not found")
        
        self._store[item_id] = item
        return item
    
    async def delete(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        if item_id in self._store:
            del self._store[item_id]
            return True
        return False
    
    async def query(self, query: str, parameters: Optional[List[Dict]] = None) -> List[T]:
        # Simple in-memory query simulation
        # Only supports basic filtering by partition key
        if parameters:
            for param in parameters:
                if param.get('name') == '@userId':
                    user_id = param.get('value')
                    return [
                        item for item in self._store.values()
                        if item.get('userId') == user_id
                    ]
        return list(self._store.values())
    
    async def find_by_field(self, field: str, value: Any) -> Optional[T]:
        """Find first item matching field value."""
        for item in self._store.values():
            if item.get(field) == value:
                return item
        return None


class CosmosDBStorage(StorageService[T]):
    """
    Azure Cosmos DB storage implementation for production.
    
    Uses the Azure Cosmos DB Python SDK for persistent storage.
    """
    
    def __init__(self, container_name: str, client, database_name: str):
        from azure.cosmos import ContainerProxy
        
        self._container_name = container_name
        self._client = client
        self._database = client.get_database_client(database_name)
        self._container: ContainerProxy = self._database.get_container_client(container_name)
        logger.info(f"Connected to Cosmos DB container: {container_name}")
    
    async def create(self, item: T) -> T:
        try:
            result = self._container.create_item(body=item)
            return result
        except Exception as e:
            logger.error(f"Cosmos DB create error: {e}")
            raise
    
    async def read(self, item_id: str, partition_key: Optional[str] = None) -> Optional[T]:
        try:
            pk = partition_key or item_id
            result = self._container.read_item(item=item_id, partition_key=pk)
            return result
        except Exception as e:
            if "NotFound" in str(e) or "404" in str(e):
                return None
            logger.error(f"Cosmos DB read error: {e}")
            raise
    
    async def update(self, item_id: str, item: T, partition_key: Optional[str] = None) -> T:
        try:
            pk = partition_key or item.get('userId') or item_id
            result = self._container.replace_item(item=item_id, body=item)
            return result
        except Exception as e:
            logger.error(f"Cosmos DB update error: {e}")
            raise
    
    async def delete(self, item_id: str, partition_key: Optional[str] = None) -> bool:
        try:
            pk = partition_key or item_id
            self._container.delete_item(item=item_id, partition_key=pk)
            return True
        except Exception as e:
            if "NotFound" in str(e):
                return False
            logger.error(f"Cosmos DB delete error: {e}")
            raise
    
    async def query(self, query: str, parameters: Optional[List[Dict]] = None) -> List[T]:
        try:
            items = self._container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            )
            return list(items)
        except Exception as e:
            logger.error(f"Cosmos DB query error: {e}")
            raise
    
    async def find_by_field(self, field: str, value: Any) -> Optional[T]:
        """Find first item matching field value."""
        query = f"SELECT * FROM c WHERE c.{field} = @value"
        parameters = [{"name": "@value", "value": value}]
        results = await self.query(query, parameters)
        return results[0] if results else None


class CosmosService:
    """
    Cosmos DB service manager for Context Bridge.
    
    Provides access to all containers:
    - memories: User memory blocks
    - users: User accounts
    - shares: Share links
    
    Automatically falls back to in-memory storage if Cosmos DB is not configured.
    """
    
    _instance: Optional['CosmosService'] = None
    
    def __init__(self):
        self._client = None
        self._memories: Optional[StorageService] = None
        self._users: Optional[StorageService] = None
        self._shares: Optional[StorageService] = None
        self._initialized = False
    
    @classmethod
    def get_instance(cls) -> 'CosmosService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize(self):
        """Initialize storage backends."""
        if self._initialized:
            return
        
        # Check for Cosmos DB configuration
        endpoint = os.environ.get('COSMOS_ENDPOINT')
        key = os.environ.get('COSMOS_KEY')
        connection_string = os.environ.get('COSMOS_CONNECTION')
        database_name = os.environ.get('COSMOS_DATABASE', 'contextbridge')
        
        if endpoint and key:
            self._initialize_cosmos_db(endpoint, key, database_name)
        elif connection_string:
            self._initialize_cosmos_db_from_connection(connection_string, database_name)
        else:
            self._initialize_in_memory()
        
        self._initialized = True
    
    def _initialize_cosmos_db(self, endpoint: str, key: str, database_name: str):
        """Initialize with Cosmos DB endpoint and key."""
        try:
            from azure.cosmos import CosmosClient
            
            self._client = CosmosClient(endpoint, key)
            self._memories = CosmosDBStorage('memories', self._client, database_name)
            self._users = CosmosDBStorage('users', self._client, database_name)
            self._shares = CosmosDBStorage('shares', self._client, database_name)
            
            logger.info(f"Cosmos DB initialized: {database_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            logger.warning("Falling back to in-memory storage")
            self._initialize_in_memory()
    
    def _initialize_cosmos_db_from_connection(self, connection_string: str, database_name: str):
        """Initialize with Cosmos DB connection string."""
        try:
            from azure.cosmos import CosmosClient
            
            self._client = CosmosClient.from_connection_string(connection_string)
            self._memories = CosmosDBStorage('memories', self._client, database_name)
            self._users = CosmosDBStorage('users', self._client, database_name)
            self._shares = CosmosDBStorage('shares', self._client, database_name)
            
            logger.info(f"Cosmos DB initialized from connection string: {database_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            logger.warning("Falling back to in-memory storage")
            self._initialize_in_memory()
    
    def _initialize_in_memory(self):
        """Initialize with in-memory storage."""
        self._memories = InMemoryStorage('memories')
        self._users = InMemoryStorage('users')
        self._shares = InMemoryStorage('shares')
        logger.warning("Using in-memory storage - data will not persist!")
    
    @property
    def memories(self) -> StorageService:
        """Get memories storage."""
        if not self._initialized:
            self.initialize()
        return self._memories
    
    @property
    def users(self) -> StorageService:
        """Get users storage."""
        if not self._initialized:
            self.initialize()
        return self._users
    
    @property
    def shares(self) -> StorageService:
        """Get shares storage."""
        if not self._initialized:
            self.initialize()
        return self._shares
    
    @property
    def is_cosmos_db(self) -> bool:
        """Check if using Cosmos DB (vs in-memory)."""
        return self._client is not None


def get_cosmos_service() -> CosmosService:
    """Get the Cosmos service singleton."""
    return CosmosService.get_instance()


# Export
__all__ = [
    'CosmosService',
    'StorageService',
    'InMemoryStorage',
    'CosmosDBStorage',
    'get_cosmos_service'
]
