import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import ChatRequest, ChatResponse
from backend.models import ChatHistory
from backend.ai_service import ai_service

logger = logging.getLogger("edugenie.routes.chat")
router = APIRouter(prefix="/api/chat", tags=["Ask AI (Chat)"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def ask_educational_question(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Ask an educational question to EduGenie.
    Returns smart, concise answers with optional explanations and key points.
    Saves history to the database.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a question first."
        )

    try:
        # Generate response from Gemini
        ai_result = ai_service.generate_chat_answer(
            question=question,
            context=payload.context
        )

        # Store in database
        chat_record = ChatHistory(
            user_id=payload.user_id,
            question=question,
            answer=ai_result["answer"],
            explanation=ai_result.get("explanation", "")
        )
        db.add(chat_record)
        db.commit()
        db.refresh(chat_record)

        return ChatResponse(
            id=chat_record.id,
            question=question,
            answer=ai_result["answer"],
            explanation=ai_result.get("explanation"),
            key_takeaways=ai_result.get("key_takeaways", []),
            created_at=chat_record.created_at
        )

    except ValueError as ve:
        logger.warning("Validation or config error in chat: %s", str(ve))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error("Error processing chat question: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again."
        )
