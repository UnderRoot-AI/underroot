from sqlalchemy.orm import Session
from app.models.user import User

def get_by_email(db: Session, email: str): return db.query(User).filter(User.email == email.lower()).first()
def get_by_id(db: Session, user_id: int): return db.get(User, user_id)
