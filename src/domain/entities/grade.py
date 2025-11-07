from dataclasses import dataclass
from datetime import date



@dataclass
class Grade:
    id: int | None
    student_id: int
    subject_id: int
    grade: int
    date: date
    comment: str | None = None
    
    def __repr__(self):
        return f'<Grade {self.grade} for student {self.student_id}>'
