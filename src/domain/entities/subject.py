from dataclasses import dataclass



@dataclass
class Subject:
    id: int | None
    name: str
    teacher: str
    
    def __repr__(self):
        return f'<Subject {self.name}>'
