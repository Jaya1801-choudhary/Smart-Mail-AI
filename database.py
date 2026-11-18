from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# SQLite database setup (Bina kisi installation ke chalega)
DATABASE_URL = "sqlite:///smartmail.db"

# connect_args={"check_same_thread": False} SQLite ke liye zaroori hota hai
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Table Schema
class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, index=True)
    subject = Column(String)
    draft_text = Column(Text)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Database mein save karne ka function
def log_email_action(recipient, subject, draft_text, status):
    db = SessionLocal()
    try:
        new_log = EmailLog(
            recipient=recipient,
            subject=subject,
            draft_text=draft_text,
            status=status
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        db.close()