from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


@dataclass
class User(UserMixin):
    id: int | None
    username: str
    email: str
    password_hash: str
    role: UserRole
    first_name: str
    last_name: str
    is_active: bool = True
    created_at: datetime | None = None
    student_profile: Student | None = None
    
    telegram_id: str | None = None
    telegram_2fa_enabled: bool = True
    last_login_ip: str | None = None

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT
    
    def is_parent(self) -> bool:
        return self.role == UserRole.PARENT
    
    def is_teacher(self) -> bool:
        return self.role == UserRole.TEACHER
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'


@dataclass
class ParentChild:
    id: int | None
    parent_id: int
    child_id: int
    relationship: str = 'parent'
    created_at: datetime | None = None
    
    def __repr__(self):
        return f'<ParentChild {self.parent_id} -> {self.child_id}>'


@dataclass
class TeacherSubject:
    id: int | None
    teacher_id: int
    subject_id: int
    is_primary: bool = True
    created_at: datetime | None = None
    
    def __repr__(self):
        return f'<TeacherSubject {self.teacher_id} -> {self.subject_id}>'


# Импорт для избежания циклических импортов
from .student import Student
