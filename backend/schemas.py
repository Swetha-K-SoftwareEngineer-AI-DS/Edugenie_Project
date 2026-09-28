from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr
import datetime


# ==========================================
# 1. Health & Status
# ==========================================
class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "EduGenie"
    version: str = "1.0.0"
    database_connected: bool = True
    gemini_configured: bool = True


# ==========================================
# 2. Chat / Ask AI
# ==========================================
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000, description="The educational question to ask")
    context: Optional[str] = Field(None, max_length=4000, description="Optional previous context")
    user_id: Optional[int] = Field(None, description="Optional user ID for history tracking")

class ChatResponse(BaseModel):
    question: str
    answer: str
    explanation: Optional[str] = None
    key_takeaways: Optional[List[str]] = Field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None


# ==========================================
# 3. Quiz Generator
# ==========================================
class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="Topic or subject for the quiz")
    text_content: Optional[str] = Field(None, max_length=10000, description="Optional text passage to base the quiz on")
    difficulty: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    question_count: int = Field(5, ge=1, le=20, description="Number of questions (1-20)")
    user_id: Optional[int] = None

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: str
    explanation: str

class QuizResponse(BaseModel):
    topic: str
    difficulty: str
    question_count: int
    questions: List[QuizQuestion]
    saved_attempt_id: Optional[int] = None

class QuizSubmissionItem(BaseModel):
    question_id: int
    selected_answer: str

class QuizSubmission(BaseModel):
    topic: str
    difficulty: str
    questions: List[QuizQuestion]
    answers: List[QuizSubmissionItem]
    user_id: Optional[int] = None

class QuizQuestionReview(BaseModel):
    question_id: int
    question: str
    options: List[str]
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str

class QuizResultResponse(BaseModel):
    score: int
    total_questions: int
    percentage: float
    feedback: str
    reviews: List[QuizQuestionReview]
    saved_id: Optional[int] = None


# ==========================================
# 4. Smart Summarizer
# ==========================================
class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=20000, description="Educational text or passage to summarize")
    title: Optional[str] = Field(None, max_length=200)
    user_id: Optional[int] = None

class ImportantTerm(BaseModel):
    term: str
    definition: str

class SummaryResponse(BaseModel):
    title: Optional[str] = None
    summary: str
    key_points: List[str]
    important_terms: List[ImportantTerm]
    word_count_original: int
    word_count_summary: int
    saved_id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None


# ==========================================
# 5. Personalized Learning Path
# ==========================================
class LearningPathRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="Subject to learn")
    level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    goal: str = Field(..., min_length=3, max_length=300, description="Target goal or career milestone")
    daily_time: int = Field(60, ge=15, le=480, description="Available study minutes per day")
    duration: str = Field("8 weeks", description="Target timeframe, e.g. 4 weeks, 8 weeks")
    user_id: Optional[int] = None

class LearningMilestone(BaseModel):
    period: str  # e.g. "Week 1", "Module 1"
    title: str
    topics: List[str]
    learning_objectives: List[str]
    suggested_practice: str
    mini_project: str
    recommended_next_step: str

class LearningPathResponse(BaseModel):
    topic: str
    level: str
    goal: str
    daily_time: int
    duration: str
    overview: str
    roadmap: List[LearningMilestone]
    saved_id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None


# ==========================================
# 6. Activity & Users
# ==========================================
class ActivityItem(BaseModel):
    id: int
    type: str # "chat", "quiz", "summary", "learning_path"
    title: str
    detail: str
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

class RecentActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total: int

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime.datetime
