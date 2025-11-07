from domain.entities.subject import Subject
from domain.repositories.subject_repository import ISubjectRepository
from infrastructure.database.connection import DatabaseConnection


class SubjectRepository(ISubjectRepository):
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, subject: Subject) -> Subject:
        query = "INSERT INTO subjects (name, teacher) VALUES (?, ?)"
        subject_id = self.db.execute_update(query, (subject.name, subject.teacher))
        subject.id = subject_id
        return subject
    
    def get_by_id(self, subject_id: int) -> Subject | None:
        query = "SELECT * FROM subjects WHERE id = ?"
        rows = self.db.execute_query(query, (subject_id,))
        if rows:
            return self._row_to_subject(rows[0])
        return None
    
    def get_all(self) -> list[Subject]:
        query = "SELECT * FROM subjects ORDER BY name"
        rows = self.db.execute_query(query)
        return [self._row_to_subject(row) for row in rows]
    
    def get_by_name(self, name: str) -> Subject | None:
        query = "SELECT * FROM subjects WHERE name = ?"
        rows = self.db.execute_query(query, (name,))
        if rows:
            return self._row_to_subject(rows[0])
        return None
    
    def update(self, subject: Subject) -> Subject:
        query = "UPDATE subjects SET name = ?, teacher = ? WHERE id = ?"
        self.db.execute_update(query, (subject.name, subject.teacher, subject.id))
        return subject
    
    def delete(self, subject_id: int) -> bool:
        query = "DELETE FROM subjects WHERE id = ?"
        self.db.execute_update(query, (subject_id,))
        return True
    
    def _row_to_subject(self, row) -> Subject:
        return Subject(
            id=row['id'],
            name=row['name'],
            teacher=row['teacher']
        )
