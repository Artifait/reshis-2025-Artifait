from datetime import datetime
from domain.entities.student import Student
from domain.repositories.student_repository import IStudentRepository
from infrastructure.database.connection import DatabaseConnection


class StudentRepository(IStudentRepository):
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, student: Student) -> Student:
        query = """
        INSERT INTO students (name, class_name, user_id, created_at)
        VALUES (?, ?, ?, ?)
        """
        student_id = self.db.execute_update(
            query,
            (student.name, student.class_name, student.user_id, datetime.utcnow())
        )
        student.id = student_id
        return student
    
    def get_by_id(self, student_id: int) -> Student | None:
        query = "SELECT * FROM students WHERE id = ?"
        rows = self.db.execute_query(query, (student_id,))
        if rows:
            return self._row_to_student(rows[0])
        return None
    
    def get_all(self) -> list[Student]:
        query = "SELECT * FROM students ORDER BY name"
        rows = self.db.execute_query(query)
        return [self._row_to_student(row) for row in rows]
    
    def get_by_class(self, class_name: str) -> list[Student]:
        query = "SELECT * FROM students WHERE class_name = ? ORDER BY name"
        rows = self.db.execute_query(query, (class_name,))
        return [self._row_to_student(row) for row in rows]
    
    def get_by_user_id(self, user_id: int) -> Student | None:
        query = "SELECT * FROM students WHERE user_id = ?"
        rows = self.db.execute_query(query, (user_id,))
        if rows:
            return self._row_to_student(rows[0])
        return None
    
    def update(self, student: Student) -> Student:
        query = """
        UPDATE students 
        SET name = ?, class_name = ?, user_id = ?
        WHERE id = ?
        """
        self.db.execute_update(
            query,
            (student.name, student.class_name, student.user_id, student.id)
        )
        return student
    
    def delete(self, student_id: int) -> bool:
        query = "DELETE FROM students WHERE id = ?"
        self.db.execute_update(query, (student_id,))
        return True
    
    def _row_to_student(self, row) -> Student:
        return Student(
            id=row['id'],
            name=row['name'],
            class_name=row['class_name'],
            user_id=row['user_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
