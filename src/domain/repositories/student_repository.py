from domain.entities.student import Student
from domain.repositories.base_repository import BaseRepository


class IStudentRepository(BaseRepository[Student]):
    
    def get_by_class(self, class_name: str) -> list[Student]:
        raise NotImplementedError
    
    def get_by_user_id(self, user_id: int) -> Student | None:
        raise NotImplementedError
