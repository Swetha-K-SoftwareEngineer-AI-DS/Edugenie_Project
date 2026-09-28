import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    chats = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    summaries = relationship("SummaryItem", back_populates="user", cascade="all, delete-orphan")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="chats")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    topic = Column(String(255), nullable=False)
    difficulty = Column(String(50), nullable=False, default="beginner")
    question_count = Column(Integer, nullable=False, default=5)
    score = Column(Integer, nullable=False, default=0)
    feedback = Column(Text, nullable=True)
    quiz_data = Column(JSON, nullable=True)       # The full questions + choices
    user_answers = Column(JSON, nullable=True)    # The selected choices
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="quizzes")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    topic = Column(String(255), nullable=False)
    level = Column(String(50), nullable=False, default="beginner")
    goal = Column(String(255), nullable=False)
    daily_time = Column(Integer, nullable=False, default=60) # minutes
    duration = Column(String(100), nullable=False, default="4 weeks")
    roadmap_data = Column(JSON, nullable=False)  # List of milestones/weeks
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="learning_paths")


class SummaryItem(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=True)
    important_terms = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="summaries")
