"""Question generation for quizbot.

The real implementation calls OpenAI and asks for a JSON object describing a
multiple-choice question. If `OPENAI_API_KEY` is empty, we fall back to a stub
generator so that local dev and tests work without the network.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

DIFFICULTY_LABELS = {
    1: "very easy, suitable for a complete beginner",
    2: "easy, basic familiarity",
    3: "moderate, requires understanding key concepts",
    4: "hard, requires deeper knowledge",
    5: "expert-level, requires advanced expertise",
}

SYSTEM_PROMPT = (
    "You write multiple-choice quiz questions. "
    "Respond ONLY with a JSON object with keys: "
    'question (string), choices (object with keys "A","B","C","D" mapping to strings), '
    "correct (one of A/B/C/D), explanation (1-2 sentences explaining the correct answer). "
    "Do not include markdown fences or extra commentary."
)


class QuestionGenerationError(Exception):
    pass


def generate_question(topic, difficulty, previous_questions=None):
    """Return a dict: {text, choices, correct_answer, explanation}.

    `previous_questions` is a list of already-asked question texts so the model
    can avoid repeats within a single quiz.
    """
    previous_questions = previous_questions or []
    if not settings.OPENAI_API_KEY:
        return _stub_question(topic, difficulty, previous_questions)

    try:
        payload = _call_openai(topic, difficulty, previous_questions)
    except Exception as exc:  # network errors, rate limits, etc.
        logger.warning("OpenAI call failed, falling back to stub: %s", exc)
        return _stub_question(topic, difficulty, previous_questions)

    return _validate_payload(payload)


def _call_openai(topic, difficulty, previous_questions):
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    avoid_clause = ""
    if previous_questions:
        avoid_clause = (
            "\n\nDo not repeat any of these previously asked questions:\n- "
            + "\n- ".join(previous_questions)
        )
    user_prompt = (
        f"Topic: {topic}\n"
        f"Difficulty level: {difficulty}/5 ({DIFFICULTY_LABELS[difficulty]}).\n"
        "Write one multiple-choice question with exactly four plausible options "
        "labeled A, B, C, D, and indicate which letter is correct."
        f"{avoid_clause}"
    )
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    content = response.choices[0].message.content or ""
    return json.loads(content)


def _validate_payload(payload):
    try:
        question = str(payload["question"]).strip()
        choices = payload["choices"]
        correct = str(payload["correct"]).strip().upper()
        explanation = str(payload.get("explanation", "")).strip()
    except (KeyError, TypeError) as exc:
        raise QuestionGenerationError(f"Malformed payload: {exc}") from exc

    if not isinstance(choices, dict) or set(choices.keys()) != {"A", "B", "C", "D"}:
        raise QuestionGenerationError("choices must have exactly keys A,B,C,D")
    if correct not in {"A", "B", "C", "D"}:
        raise QuestionGenerationError("correct must be one of A/B/C/D")

    return {
        "text": question,
        "choices": {k: str(v) for k, v in choices.items()},
        "correct_answer": correct,
        "explanation": explanation,
    }


def _stub_question(topic, difficulty, previous_questions):
    """Deterministic placeholder used when OpenAI is unavailable."""
    n = len(previous_questions) + 1
    return {
        "text": (
            f"[stub] Difficulty {difficulty} question #{n} about {topic}. "
            "Which option is labeled A?"
        ),
        "choices": {
            "A": "Option A (the correct one)",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D",
        },
        "correct_answer": "A",
        "explanation": (
            "Stub generator: the correct answer is always A. "
            "Set OPENAI_API_KEY to get real questions."
        ),
    }
