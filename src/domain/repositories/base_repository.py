from typing import TypeVar, Generic, Optional, List

T = TypeVar('T')


class BaseRepository(Generic[T]):
    
    def create(self, entity: T) -> T:
        raise NotImplementedError
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        raise NotImplementedError
    
    def get_all(self) -> List[T]:
        raise NotImplementedError
    
    def update(self, entity: T) -> T:
        raise NotImplementedError
    
    def delete(self, entity_id: int) -> bool:
        raise NotImplementedError
    
    def exists(self, entity_id: int) -> bool:
        return self.get_by_id(entity_id) is not None
