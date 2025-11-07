from dataclasses import dataclass
from datetime import date



@dataclass
class Attendance:
    id: int | None
    student_id: int
    subject_id: int
    date: date
    present: bool
    reason: str | None = None
    
    def __repr__(self):
        return f'<Attendance {self.present} for student {self.student_id}>'
