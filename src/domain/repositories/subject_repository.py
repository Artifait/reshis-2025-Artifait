from domain.entities.subject import Subject
from domain.repositories.base_repository import BaseRepository


class ISubjectRepository(BaseRepository[Subject]):
    
    def get_by_name(self, name: str) -> Subject | None:
        raise NotImplementedError
