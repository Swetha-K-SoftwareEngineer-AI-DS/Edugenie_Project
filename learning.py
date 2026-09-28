import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import LearningPathRequest, LearningPathResponse, LearningMilestone
from backend.models import LearningPath
from backend.ai_service import ai_service

logger = logging.getLogger("edugenie.routes.learning")
router = APIRouter(prefix="/api/learning-path", tags=["Personalized Learning Path"])


@router.post("", response_model=LearningPathResponse, status_code=status.HTTP_200_OK)
def create_personalized_learning_path(payload: LearningPathRequest, db: Session = Depends(get_db)):
    """
    Generate a personalized, progressive learning roadmap tailored to the student's topic, level, and time availability.
    """
    topic = payload.topic.strip()
    goal = payload.goal.strip()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid topic for your learning path."
        )

    try:
        lp_result = ai_service.generate_learning_path(
            topic=topic,
            level=payload.level,
            goal=goal,
            daily_time=payload.daily_time,
            duration=payload.duration
        )

        milestones = []
        for idx, m in enumerate(lp_result.get("roadmap", []), start=1):
            if isinstance(m, dict):
                milestones.append(LearningMilestone(
                    period=m.get("period", f"Week {idx}"),
                    title=m.get("title", f"Stage {idx}"),
                    topics=m.get("topics", []),
                    learning_objectives=m.get("learning_objectives", []),
                    suggested_practice=m.get("suggested_practice", "Practice the weekly concepts with exercises."),
                    mini_project=m.get("mini_project", "Build a small portfolio project applying these skills."),
                    recommended_next_step=m.get("recommended_next_step", "Review exercises and move to the next stage.")
                ))

        # Save to database
        saved_id = None
        created_at = None
        try:
            path_record = LearningPath(
                user_id=payload.user_id,
                topic=topic,
                level=payload.level,
                goal=goal,
                daily_time=payload.daily_time,
                duration=payload.duration,
                roadmap_data=[m.model_dump() for m in milestones]
            )
            db.add(path_record)
            db.commit()
            db.refresh(path_record)
            saved_id = path_record.id
            created_at = path_record.created_at
        except Exception as db_err:
            logger.warning("Could not persist learning path to database: %s", str(db_err))
            db.rollback()

        return LearningPathResponse(
            topic=topic,
            level=payload.level,
            goal=goal,
            daily_time=payload.daily_time,
            duration=payload.duration,
            overview=lp_result.get("overview", f"Structured roadmap for {topic}"),
            roadmap=milestones,
            saved_id=saved_id,
            created_at=created_at
        )

    except ValueError as ve:
        logger.warning("Learning path parameter error: %s", str(ve))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error("Error creating learning path: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again."
        )
