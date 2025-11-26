from datetime import datetime
from domain.entities.user import User, UserRole
from domain.repositories.user_repository import IUserRepository
from infrastructure.database.connection import DatabaseConnection


class UserRepository(IUserRepository):
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, user: User) -> User:
        query = """
        INSERT INTO users (username, email, password_hash, role, first_name, last_name, is_active, created_at, telegram_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        user_id = self.db.execute_update(
            query,
            (user.username, user.email, user.password_hash, user.role.value,
             user.first_name, user.last_name, user.is_active, datetime.utcnow(), getattr(user, 'telegram_id', None))
        )
        user.id = user_id
        return user
    
    def get_by_id(self, user_id: int) -> User | None:
        query = "SELECT * FROM users WHERE id = ?"
        rows = self.db.execute_query(query, (user_id,))
        if rows:
            return self._row_to_user(rows[0])
        return None
    
    def get_by_username(self, username: str) -> User | None:
        query = "SELECT * FROM users WHERE username = ?"
        rows = self.db.execute_query(query, (username,))
        if rows:
            return self._row_to_user(rows[0])
        return None
    
    def get_by_email(self, email: str) -> User | None:
        query = "SELECT * FROM users WHERE email = ?"
        rows = self.db.execute_query(query, (email,))
        if rows:
            return self._row_to_user(rows[0])
        return None
    
    def get_all(self) -> list[User]:
        query = "SELECT * FROM users ORDER BY created_at DESC"
        rows = self.db.execute_query(query)
        return [self._row_to_user(row) for row in rows]
    
    def get_by_role(self, role: UserRole) -> list[User]:
        query = "SELECT * FROM users WHERE role = ? ORDER BY created_at DESC"
        rows = self.db.execute_query(query, (role.value,))
        return [self._row_to_user(row) for row in rows]
    
    def update(self, user: User) -> User:
        query = """
        UPDATE users 
        SET username = ?, email = ?, password_hash = ?, role = ?, 
            first_name = ?, last_name = ?, is_active = ?, telegram_id = ?
        WHERE id = ?
        """
        self.db.execute_update(
            query,
            (user.username, user.email, user.password_hash, user.role.value,
             user.first_name, user.last_name, user.is_active, getattr(user, 'telegram_id', None), user.id)
        )
        return user
    
    def delete(self, user_id: int) -> bool:
        query = "DELETE FROM users WHERE id = ?"
        self.db.execute_update(query, (user_id,))
        return True
    
    def _row_to_user(self, row) -> User:
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=UserRole(row['role']),
            first_name=row['first_name'],
            last_name=row['last_name'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            telegram_id=row['telegram_id']
        )
