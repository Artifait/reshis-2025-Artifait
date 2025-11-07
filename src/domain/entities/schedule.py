from dataclasses import dataclass
from datetime import time



@dataclass
class Schedule:
    id: int | None
    subject_id: int
    day_of_week: int  # 0-6 (понедельник-воскресенье)
    time_start: time
    time_end: time
    classroom: str | None = None
    
    def __repr__(self):
        return f'<Schedule subject {self.subject_id} on day {self.day_of_week}>'
