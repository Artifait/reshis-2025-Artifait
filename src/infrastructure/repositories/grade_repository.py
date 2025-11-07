from datetime import date
from domain.entities.grade import Grade
from domain.repositories.grade_repository import IGradeRepository
from infrastructure.database.connection import DatabaseConnection


class GradeRepository(IGradeRepository):
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, grade: Grade) -> Grade:
        query = """
        INSERT INTO grades (student_id, subject_id, grade, date, comment)
        VALUES (?, ?, ?, ?, ?)
        """
        grade_id = self.db.execute_update(
            query,
            (grade.student_id, grade.subject_id, grade.grade, grade.date, grade.comment)
        )
        grade.id = grade_id
        return grade
    
    def get_by_id(self, grade_id: int) -> Grade | None:
        query = "SELECT * FROM grades WHERE id = ?"
        rows = self.db.execute_query(query, (grade_id,))
        if rows:
            return self._row_to_grade(rows[0])
        return None
    
    def get_by_student(self, student_id: int) -> list[Grade]:
        query = "SELECT * FROM grades WHERE student_id = ? ORDER BY date DESC"
        rows = self.db.execute_query(query, (student_id,))
        return [self._row_to_grade(row) for row in rows]
    
    def get_by_student_and_subject(self, student_id: int, subject_id: int) -> list[Grade]:
        query = """
        SELECT * FROM grades 
        WHERE student_id = ? AND subject_id = ? 
        ORDER BY date DESC
        """
        rows = self.db.execute_query(query, (student_id, subject_id))
        return [self._row_to_grade(row) for row in rows]
    
    def get_by_date_range(self, start_date: date, end_date: date) -> list[Grade]:
        query = """
        SELECT * FROM grades 
        WHERE date BETWEEN ? AND ? 
        ORDER BY date DESC
        """
        rows = self.db.execute_query(query, (start_date, end_date))
        return [self._row_to_grade(row) for row in rows]
    
    def update(self, grade: Grade) -> Grade:
        query = """
        UPDATE grades 
        SET student_id = ?, subject_id = ?, grade = ?, date = ?, comment = ?
        WHERE id = ?
        """
        self.db.execute_update(
            query,
            (grade.student_id, grade.subject_id, grade.grade, grade.date, grade.comment, grade.id)
        )
        return grade
    
    def delete(self, grade_id: int) -> bool:
        query = "DELETE FROM grades WHERE id = ?"
        self.db.execute_update(query, (grade_id,))
        return True
    
    def _row_to_grade(self, row) -> Grade:
        return Grade(
            id=row['id'],
            student_id=row['student_id'],
            subject_id=row['subject_id'],
            grade=row['grade'],
            date=date.fromisoformat(row['date']),
            comment=row['comment']
        )
