from dataclasses import dataclass
from datetime import datetime



@dataclass
class Student:
    id: int | None
    name: str
    class_name: str
    user_id: int | None = None
    created_at: datetime | None = None
    
    def __repr__(self):
        return f'<Student {self.name}>'
