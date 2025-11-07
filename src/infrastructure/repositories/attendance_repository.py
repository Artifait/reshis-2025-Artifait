from datetime import date
from domain.entities.attendance import Attendance
from domain.repositories.attendance_repository import IAttendanceRepository
from infrastructure.database.connection import DatabaseConnection


class AttendanceRepository(IAttendanceRepository):
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, attendance: Attendance) -> Attendance:
        query = """
        INSERT INTO attendance (student_id, subject_id, date, present, reason)
        VALUES (?, ?, ?, ?, ?)
        """
        attendance_id = self.db.execute_update(
            query,
            (attendance.student_id, attendance.subject_id, attendance.date, 
             attendance.present, attendance.reason)
        )
        attendance.id = attendance_id
        return attendance
    
    def get_by_id(self, attendance_id: int) -> Attendance | None:
        query = "SELECT * FROM attendance WHERE id = ?"
        rows = self.db.execute_query(query, (attendance_id,))
        if rows:
            return self._row_to_attendance(rows[0])
        return None
    
    def get_by_student(self, student_id: int) -> list[Attendance]:
        query = "SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC"
        rows = self.db.execute_query(query, (student_id,))
        return [self._row_to_attendance(row) for row in rows]
    
    def get_by_student_and_subject(self, student_id: int, subject_id: int) -> list[Attendance]:
        query = """
        SELECT * FROM attendance 
        WHERE student_id = ? AND subject_id = ? 
        ORDER BY date DESC
        """
        rows = self.db.execute_query(query, (student_id, subject_id))
        return [self._row_to_attendance(row) for row in rows]
    
    def get_by_date_range(self, start_date: date, end_date: date) -> list[Attendance]:
        query = """
        SELECT * FROM attendance 
        WHERE date BETWEEN ? AND ? 
        ORDER BY date DESC
        """
        rows = self.db.execute_query(query, (start_date, end_date))
        return [self._row_to_attendance(row) for row in rows]
    
    def update(self, attendance: Attendance) -> Attendance:
        query = """
        UPDATE attendance 
        SET student_id = ?, subject_id = ?, date = ?, present = ?, reason = ?
        WHERE id = ?
        """
        self.db.execute_update(
            query,
            (attendance.student_id, attendance.subject_id, attendance.date,
             attendance.present, attendance.reason, attendance.id)
        )
        return attendance
    
    def delete(self, attendance_id: int) -> bool:
        query = "DELETE FROM attendance WHERE id = ?"
        self.db.execute_update(query, (attendance_id,))
        return True
    
    def _row_to_attendance(self, row) -> Attendance:
        return Attendance(
            id=row['id'],
            student_id=row['student_id'],
            subject_id=row['subject_id'],
            date=date.fromisoformat(row['date']),
            present=bool(row['present']),
            reason=row['reason']
        )
