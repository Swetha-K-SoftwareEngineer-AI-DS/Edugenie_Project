import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import QuizRequest, QuizResponse, QuizSubmission, QuizResultResponse, QuizQuestionReview
from backend.models import QuizAttempt
from backend.ai_service import ai_service

logger = logging.getLogger("edugenie.routes.quiz")
router = APIRouter(prefix="/api/quiz", tags=["Quiz Generator"])


@router.post("", response_model=QuizResponse, status_code=status.HTTP_200_OK)
def generate_quiz(payload: QuizRequest, db: Session = Depends(get_db)):
    """
    Generate educational multiple-choice quiz questions based on a topic or provided text.
    """
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid topic for the quiz."
        )

    try:
        questions = ai_service.generate_quiz(
            topic=topic,
            difficulty=payload.difficulty,
            question_count=payload.question_count,
            text_content=payload.text_content
        )

        return QuizResponse(
            topic=topic,
            difficulty=payload.difficulty,
            question_count=len(questions),
            questions=questions
        )

    except ValueError as ve:
        logger.warning("Quiz generation parameter error: %s", str(ve))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error("Error generating quiz - Type: %s, Message: %s", type(e).__name__, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again."
        )


@router.post("/evaluate", response_model=QuizResultResponse, status_code=status.HTTP_200_OK)
def evaluate_quiz_submission(payload: QuizSubmission, db: Session = Depends(get_db)):
    """
    Evaluates student's submitted quiz answers, computes score,
    generates encouraging feedback, and records the attempt in the database.
    """
    if not payload.questions or not payload.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete submission: questions and user answers are required."
        )

    answers_map = {a.question_id: a.selected_answer for a in payload.answers}
    reviews = []
    score = 0
    total = len(payload.questions)

    for q in payload.questions:
        user_choice = answers_map.get(q.id, "").strip()
        correct_choice = q.correct_answer.strip()
        is_correct = (user_choice.lower() == correct_choice.lower())

        if is_correct:
            score += 1

        reviews.append(QuizQuestionReview(
            question_id=q.id,
            question=q.question,
            options=q.options,
            selected_answer=user_choice or "Not answered",
            correct_answer=correct_choice,
            is_correct=is_correct,
            explanation=q.explanation
        ))

    percentage = round((score / total * 100), 1) if total > 0 else 0.0

    # Friendly feedback based on score
    if percentage >= 90:
        feedback = f"Outstanding work! You demonstrated mastery of {payload.topic} with a score of {score}/{total}."
    elif percentage >= 70:
        feedback = f"Great effort! You have a solid grasp of {payload.topic}. Review the explanations below to perfect your understanding."
    elif percentage >= 50:
        feedback = f"Good start! You scored {score}/{total}. Go through each explanation carefully to strengthen your core concepts."
    else:
        feedback = f"Keep practicing! Scoring {score}/{total} highlights great learning opportunities. Review the concept notes and try again."

    # Save to database
    saved_id = None
    try:
        attempt_record = QuizAttempt(
            user_id=payload.user_id,
            topic=payload.topic,
            difficulty=payload.difficulty,
            question_count=total,
            score=score,
            feedback=feedback,
            quiz_data=[q.model_dump() for q in payload.questions],
            user_answers=[a.model_dump() for a in payload.answers]
        )
        db.add(attempt_record)
        db.commit()
        db.refresh(attempt_record)
        saved_id = attempt_record.id
    except Exception as e:
        logger.warning("Could not save quiz attempt to database: %s", str(e))
        db.rollback()

    return QuizResultResponse(
        score=score,
        total_questions=total,
        percentage=percentage,
        feedback=feedback,
        reviews=reviews,
        saved_id=saved_id
    )
