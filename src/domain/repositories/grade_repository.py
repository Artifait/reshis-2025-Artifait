from datetime import date
from domain.entities.grade import Grade
from domain.repositories.base_repository import BaseRepository


class IGradeRepository(BaseRepository[Grade]):
    
    def get_by_student(self, student_id: int) -> list[Grade]:
        raise NotImplementedError
    
    def get_by_student_and_subject(self, student_id: int, subject_id: int) -> list[Grade]:
        raise NotImplementedError
    
    def get_by_date_range(self, start_date: date, end_date: date) -> list[Grade]:
        raise NotImplementedError
