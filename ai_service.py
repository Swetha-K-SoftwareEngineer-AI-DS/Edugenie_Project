import os
import logging
import json
import time
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.utils.security import clean_and_extract_json, sanitize_input_text

logger = logging.getLogger("edugenie.ai_service")

# Try importing the new google-genai client or the classic SDK
HAS_NEW_GENAI = False
HAS_CLASSIC_GENAI = False

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    try:
        import google.generativeai as genai_classic
        HAS_CLASSIC_GENAI = True
    except ImportError:
        pass


class EduGenieAIService:
    """
    Centralized AI Service for EduGenie educational features.
    Interfaces securely with Google Gemini API using controlled prompts.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemma-4-31b-it"
        self._is_configured = False
        self._new_client = None
        self._setup_client()

    def _setup_client(self):
        """Initialize Google Generative AI client."""
        key = self.api_key.strip() if self.api_key else ""
        self.model_name = os.getenv("GEMINI_MODEL", settings.GEMINI_MODEL) or "gemma-4-31b-it"
        if key and key != "your_gemini_api_key_here":
            try:
                if HAS_NEW_GENAI:
                    self._new_client = genai.Client(api_key=key)
                    self._is_configured = True
                    logger.info("Google Gemini AI client (google-genai) configured with model %s.", self.model_name)
                elif HAS_CLASSIC_GENAI:
                    genai_classic.configure(api_key=key)
                    self._is_configured = True
                    logger.info("Google Gemini AI client (classic) configured with model %s.", self.model_name)
                else:
                    logger.warning("No Google GenAI package found in environment.")
                    self._is_configured = False
            except Exception as e:
                logger.error("Failed to configure Google Gemini AI client: %s", str(e))
                self._is_configured = False
        else:
            logger.warning("GEMINI_API_KEY is not set or using placeholder.")
            self._is_configured = False

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def _call_gemini(self, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> str:
        """Internal helper to call Gemini with controlled parameters."""
        self.model_name = os.getenv("GEMINI_MODEL", settings.GEMINI_MODEL) or "gemma-4-31b-it"
        if not self._is_configured:
            # Re-check in case user updated .env at runtime
            self.api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
            self._setup_client()

        if not self._is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please set a valid GEMINI_API_KEY in the .env file."
            )

        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt

        max_retries = 3
        delays = [2, 4, 8]

        for attempt in range(max_retries):
            try:
                if HAS_NEW_GENAI and self._new_client:
                    # Explicitly disable automatic function calling (AFC)
                    config = types.GenerateContentConfig(
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    ) if hasattr(types, 'AutomaticFunctionCallingConfig') else None

                    response = self._new_client.models.generate_content(
                        model=self.model_name,
                        contents=full_prompt,
                        config=config
                    )
                    if not response or not response.text:
                        raise ValueError("AI service returned an empty response.")
                    return response.text.strip()

                elif HAS_CLASSIC_GENAI:
                    # Classic google.generativeai client fallback
                    model = genai_classic.GenerativeModel(
                        model_name=self.model_name
                    )
                    response = model.generate_content(full_prompt)
                    if not response or not response.text:
                        raise ValueError("AI service returned an empty response.")
                    return response.text.strip()
                else:
                    raise RuntimeError("No Google Generative AI SDK is installed.")

            except Exception as e:
                err_msg = str(e)
                # Check specifically for temporary 503 / UNAVAILABLE / high demand or 500 / INTERNAL
                is_retryable = (
                    "503" in err_msg or 
                    "UNAVAILABLE" in err_msg or 
                    "high demand" in err_msg.lower() or
                    getattr(e, "code", None) == 503 or
                    "500" in err_msg or
                    "INTERNAL" in err_msg or
                    getattr(e, "code", None) == 500
                )

                if is_retryable and attempt < max_retries - 1:
                    wait_time = delays[attempt]
                    logger.warning(
                        "Gemini service temporarily unavailable (500/503). Retrying in %ds (attempt %d/%d)...",
                        wait_time,
                        attempt + 1,
                        max_retries
                    )
                    time.sleep(wait_time)
                    continue

                logger.error("Gemini API error during generation: %s", err_msg, exc_info=True)
                raise RuntimeError(f"AI service error: {err_msg}")


    # =========================================================================
    # 1. Ask AI (Chat Feature)
    # =========================================================================
    def generate_chat_answer(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Answers student queries with simple, concise, and educational language.
        """
        clean_q = sanitize_input_text(question, max_chars=1000)
        system_prompt = (
            "You are EduGenie, an educational AI assistant. Answer the student's question accurately and concisely. "
            "Explain difficult concepts in simple language suitable for students. Do not invent facts. "
            "If the question is ambiguous, ask for clarification. Avoid unnecessarily long answers. "
            "Return valid JSON with exactly these keys:\n"
            "- 'answer': A direct, accurate, concise answer (1-3 sentences).\n"
            "- 'explanation': A student-friendly conceptual breakdown or analogy (2-4 sentences).\n"
            "- 'key_takeaways': A list of 2 to 4 concise bullet points of essential facts."
        )

        user_prompt = f"Student Question: {clean_q}"
        if context:
            user_prompt += f"\nPrevious Context: {sanitize_input_text(context, 1000)}"

        try:
            raw_response = self._call_gemini(user_prompt, system_instruction=system_prompt, json_mode=True)
            data = clean_and_extract_json(raw_response)
            return {
                "question": clean_q,
                "answer": data.get("answer", "No direct answer generated."),
                "explanation": data.get("explanation", ""),
                "key_takeaways": data.get("key_takeaways", [])
            }
        except Exception as e:
            logger.warning("Falling back for chat answer: %s", str(e))
            if "GEMINI_API_KEY" in str(e) or not self._is_configured:
                raise ValueError("AI service is not configured. Please add your GEMINI_API_KEY in the .env file.")
            raise RuntimeError("AI service is temporarily unavailable. Please try again.")

    # =========================================================================
    # 2. Quiz Generator
    # =========================================================================
    def generate_quiz(self, topic: str, difficulty: str = "beginner", question_count: int = 5, text_content: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generates structured multiple-choice quiz questions with 4 options, correct answer, and explanation.
        """
        clean_topic = sanitize_input_text(topic, max_chars=150)
        clean_text = sanitize_input_text(text_content, max_chars=8000) if text_content else None
        
        system_prompt = (
            "You are an educational quiz generator. Generate the requested number of high quality multiple-choice questions "
            "suitable for the specified academic difficulty level. Return valid structured JSON. "
            "Output a JSON object with a single key 'questions' containing a list of objects. Each object must have:\n"
            "- 'id': Integer starting from 1\n"
            "- 'question': Clear, unambiguous question text\n"
            "- 'options': Array of exactly 4 distinct answer choices\n"
            "- 'correct_answer': The string that EXACTLY matches one of the 4 options\n"
            "- 'explanation': Short 1-2 sentence explanation of why this answer is correct"
        )

        user_prompt = (
            f"Topic: {clean_topic}\n"
            f"Difficulty Level: {difficulty}\n"
            f"Number of Questions: {question_count}\n"
        )
        if clean_text:
            user_prompt += f"\nPassage/Reference Text:\n{clean_text}\n"

        try:
            raw_response = self._call_gemini(user_prompt, system_instruction=system_prompt, json_mode=True)
            data = clean_and_extract_json(raw_response)
            
            questions = []
            if isinstance(data, dict) and "questions" in data:
                questions = data["questions"]
            elif isinstance(data, list):
                questions = data
            else:
                raise ValueError("Quiz response format invalid from AI.")

            # Validate each question
            validated = []
            for idx, q in enumerate(questions, start=1):
                opts = q.get("options", [])
                correct = q.get("correct_answer", "")
                if len(opts) < 4:
                    opts.extend([f"Option {i}" for i in range(len(opts) + 1, 5)])
                elif len(opts) > 4:
                    opts = opts[:4]
                    
                if correct not in opts:
                    opts[0] = correct

                validated.append({
                    "id": idx,
                    "question": q.get("question", f"Question {idx}"),
                    "options": opts,
                    "correct_answer": correct,
                    "explanation": q.get("explanation", "The selected option is correct based on the core concept.")
                })

            return validated
        except Exception as e:
            logger.error("Error in generate_quiz - Type: %s, Message: %s", type(e).__name__, str(e), exc_info=True)
            raise e

    # =========================================================================
    # 3. Smart Summarizer
    # =========================================================================
    def generate_summary(self, text: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Summarizes educational passage into concise summary, key bullet points, and defined terms.
        """
        clean_text = sanitize_input_text(text, max_chars=18000)
        system_prompt = (
            "You are an educational summarization assistant. Summarize the supplied content accurately and objectively. "
            "Preserve important facts, dates, definitions, and concepts. Return valid JSON containing:\n"
            "- 'title': A short, clear title for this passage\n"
            "- 'summary': A well-structured, concise summary of the core message (1-3 paragraphs)\n"
            "- 'key_points': A list of 4 to 8 crisp, informative bullet points highlighting vital takeaways\n"
            "- 'important_terms': A list of 3 to 6 key terminology objects with 'term' and 'definition'"
        )

        user_prompt = f"Educational Passage to Summarize:\n{clean_text}"
        if title:
            user_prompt = f"Topic Title: {title}\n" + user_prompt

        raw_response = self._call_gemini(user_prompt, system_instruction=system_prompt, json_mode=True)
        data = clean_and_extract_json(raw_response)

        original_words = len(clean_text.split())
        summary_text = data.get("summary", "")
        summary_words = len(summary_text.split())

        return {
            "title": data.get("title", title or "Passage Summary"),
            "summary": summary_text,
            "key_points": data.get("key_points", []),
            "important_terms": data.get("important_terms", []),
            "word_count_original": original_words,
            "word_count_summary": summary_words
        }

    # =========================================================================
    # 4. Personalized Learning Path
    # =========================================================================
    def generate_learning_path(self, topic: str, level: str, goal: str, daily_time: int, duration: str) -> Dict[str, Any]:
        """
        Creates a custom progressive learning roadmap adapted to time and level.
        """
        clean_topic = sanitize_input_text(topic, max_chars=150)
        clean_goal = sanitize_input_text(goal, max_chars=250)
        clean_duration = sanitize_input_text(duration, max_chars=50)

        system_prompt = (
            "You are an educational planning assistant. Create a structured, realistic, step-by-step learning roadmap "
            "based on the student's topic, current level, career/academic goal, available daily study time, and duration. "
            "Progress systematically from fundamentals to advanced mastery. "
            "Return valid JSON with:\n"
            "- 'overview': A 2-sentence motivating overview of what the student will achieve\n"
            "- 'roadmap': A list of milestones/weekly stages. Each stage object MUST contain:\n"
            "   - 'period': e.g., 'Week 1', 'Week 2' or 'Module 1'\n"
            "   - 'title': Stage theme title\n"
            "   - 'topics': List of 3 to 5 specific concepts to learn\n"
            "   - 'learning_objectives': List of 2 to 3 practical skills gained\n"
            "   - 'suggested_practice': Concrete hands-on practice exercise\n"
            "   - 'mini_project': A small project or problem to build/solve\n"
            "   - 'recommended_next_step': Guidance on moving forward to the next stage"
        )

        user_prompt = (
            f"Topic/Subject: {clean_topic}\n"
            f"Current Level: {level}\n"
            f"Target Goal: {clean_goal}\n"
            f"Available Time: {daily_time} minutes per day\n"
            f"Duration / Horizon: {clean_duration}\n"
        )

        raw_response = self._call_gemini(user_prompt, system_instruction=system_prompt, json_mode=True)
        data = clean_and_extract_json(raw_response)

        return {
            "topic": clean_topic,
            "level": level,
            "goal": clean_goal,
            "daily_time": daily_time,
            "duration": clean_duration,
            "overview": data.get("overview", f"Comprehensive {clean_duration} roadmap to master {clean_topic} for {clean_goal}."),
            "roadmap": data.get("roadmap", [])
        }


# Singleton instance
ai_service = EduGenieAIService()
