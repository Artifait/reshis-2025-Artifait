from datetime import date
from domain.entities.attendance import Attendance
from domain.repositories.base_repository import BaseRepository


class IAttendanceRepository(BaseRepository[Attendance]):
    
    def get_by_student(self, student_id: int) -> list[Attendance]:
        raise NotImplementedError
    
    def get_by_student_and_subject(self, student_id: int, subject_id: int) -> list[Attendance]:
        raise NotImplementedError
    
    def get_by_date_range(self, start_date: date, end_date: date) -> list[Attendance]:
        raise NotImplementedError
