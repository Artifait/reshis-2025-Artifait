from domain.entities.user import User, UserRole
from domain.repositories.base_repository import BaseRepository


class IUserRepository(BaseRepository[User]):
    
    def get_by_username(self, username: str) -> User | None:
        raise NotImplementedError
    
    def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError
    
    def get_by_role(self, role: UserRole) -> list[User]:
        raise NotImplementedError
