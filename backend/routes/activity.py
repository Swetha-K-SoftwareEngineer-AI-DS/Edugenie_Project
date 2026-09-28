import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database import get_db
from backend.schemas import RecentActivityResponse, ActivityItem
from backend.models import ChatHistory, QuizAttempt, SummaryItem, LearningPath

logger = logging.getLogger("edugenie.routes.activity")
router = APIRouter(prefix="/api/activity", tags=["User Activity"])


@router.get("", response_model=RecentActivityResponse)
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve unified recent student learning activity across all tools:
    - Chat questions asked
    - Quizzes taken & scores
    - Summaries generated
    - Learning paths designed
    """
    activities: List[ActivityItem] = []

    try:
        # 1. Recent chats
        chat_q = db.query(ChatHistory)
        if user_id:
            chat_q = chat_q.filter(ChatHistory.user_id == user_id)
        chats = chat_q.order_by(desc(ChatHistory.created_at)).limit(limit).all()
        for c in chats:
            activities.append(ActivityItem(
                id=c.id,
                type="chat",
                title=f"Asked: {c.question[:60]}{'...' if len(c.question) > 60 else ''}",
                detail=c.answer[:120] + ("..." if len(c.answer) > 120 else ""),
                meta={"explanation": bool(c.explanation)},
                created_at=c.created_at
            ))

        # 2. Recent quizzes
        quiz_q = db.query(QuizAttempt)
        if user_id:
            quiz_q = quiz_q.filter(QuizAttempt.user_id == user_id)
        quizzes = quiz_q.order_by(desc(QuizAttempt.created_at)).limit(limit).all()
        for q in quizzes:
            activities.append(ActivityItem(
                id=q.id,
                type="quiz",
                title=f"Quiz on {q.topic} ({q.difficulty.title()})",
                detail=f"Score: {q.score}/{q.question_count} ({round(q.score/q.question_count*100 if q.question_count else 0)}%)",
                meta={"score": q.score, "total": q.question_count, "difficulty": q.difficulty},
                created_at=q.created_at
            ))

        # 3. Recent summaries
        sum_q = db.query(SummaryItem)
        if user_id:
            sum_q = sum_q.filter(SummaryItem.user_id == user_id)
        summaries = sum_q.order_by(desc(SummaryItem.created_at)).limit(limit).all()
        for s in summaries:
            activities.append(ActivityItem(
                id=s.id,
                type="summary",
                title=f"Summary: {s.title or 'Educational Passage'}",
                detail=s.summary[:120] + ("..." if len(s.summary) > 120 else ""),
                meta={"points_count": len(s.key_points) if s.key_points else 0},
                created_at=s.created_at
            ))

        # 4. Recent learning paths
        lp_q = db.query(LearningPath)
        if user_id:
            lp_q = lp_q.filter(LearningPath.user_id == user_id)
        lps = lp_q.order_by(desc(LearningPath.created_at)).limit(limit).all()
        for lp in lps:
            activities.append(ActivityItem(
                id=lp.id,
                type="learning_path",
                title=f"Roadmap: {lp.topic} ({lp.duration})",
                detail=f"Goal: {lp.goal} | Level: {lp.level.title()}",
                meta={"level": lp.level, "duration": lp.duration},
                created_at=lp.created_at
            ))

        # Sort combined activity chronologically descending
        activities.sort(key=lambda x: x.created_at, reverse=True)
        trimmed = activities[:limit]

        return RecentActivityResponse(
            activities=trimmed,
            total=len(trimmed)
        )

    except Exception as e:
        logger.error("Error fetching recent activity: %s", str(e), exc_info=True)
        return RecentActivityResponse(activities=[], total=0)
