import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import SummaryRequest, SummaryResponse, ImportantTerm
from backend.models import SummaryItem
from backend.ai_service import ai_service

logger = logging.getLogger("edugenie.routes.summary")
router = APIRouter(prefix="/api/summarize", tags=["Smart Summarizer"])


@router.post("", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
def summarize_educational_text(payload: SummaryRequest, db: Session = Depends(get_db)):
    """
    Summarize large educational passages into a concise summary, key takeaways, and definitions.
    """
    text = payload.text.strip()
    if not text or len(text) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an educational passage of at least 20 characters to summarize."
        )

    try:
        summary_result = ai_service.generate_summary(
            text=text,
            title=payload.title
        )

        # Parse important terms
        terms = [
            ImportantTerm(
                term=t.get("term", ""),
                definition=t.get("definition", "")
            )
            for t in summary_result.get("important_terms", [])
            if isinstance(t, dict) and "term" in t
        ]

        # Save to database
        saved_id = None
        created_at = None
        try:
            summary_record = SummaryItem(
                user_id=payload.user_id,
                title=summary_result.get("title"),
                original_text=text,
                summary=summary_result["summary"],
                key_points=summary_result.get("key_points", []),
                important_terms=[t.model_dump() for t in terms]
            )
            db.add(summary_record)
            db.commit()
            db.refresh(summary_record)
            saved_id = summary_record.id
            created_at = summary_record.created_at
        except Exception as db_err:
            logger.warning("Could not persist summary to database: %s", str(db_err))
            db.rollback()

        return SummaryResponse(
            title=summary_result.get("title"),
            summary=summary_result["summary"],
            key_points=summary_result.get("key_points", []),
            important_terms=terms,
            word_count_original=summary_result.get("word_count_original", len(text.split())),
            word_count_summary=summary_result.get("word_count_summary", len(summary_result["summary"].split())),
            saved_id=saved_id,
            created_at=created_at
        )

    except ValueError as ve:
        logger.warning("Summarizer validation error: %s", str(ve))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error("Error creating summary: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again."
        )
