from domain.entities.schedule import Schedule
from domain.repositories.base_repository import BaseRepository


class IScheduleRepository(BaseRepository[Schedule]):
    
    def get_by_day(self, day_of_week: int) -> list[Schedule]:
        raise NotImplementedError
    
    def get_by_subject(self, subject_id: int) -> list[Schedule]:
        raise NotImplementedError
