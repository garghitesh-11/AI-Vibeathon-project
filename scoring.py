"""Scoring and validation for Pitch Pressure Test.

The AI gives 0-10 ratings per dimension. The final numbers are computed here
in Python with a fixed, documented formula, so the AI never invents the score.

Per-answer score (0-100) = 10 * (0.40*directness + 0.35*evidence + 0.25*clarity)
Readiness score (0-100)  = average of the three answer scores
Blank answers always score 0, regardless of what the AI says.
"""

WEIGHTS = {"directness": 0.40, "evidence": 0.35, "clarity": 0.25}


def _clamp(value, lo=0.0, hi=10.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    return max(lo, min(hi, value))


def validate_questions(data):
    """Return a clean list of 3 {'persona', 'question'} dicts or raise ValueError."""
    items = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(items, list) or len(items) != 3:
        raise ValueError("The AI did not return exactly 3 questions.")
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("A question was in the wrong format.")
        persona = str(item.get("persona", "")).strip()
        question = str(item.get("question", "")).strip()
        if not persona or not question:
            raise ValueError("A question or persona was empty.")
        cleaned.append({"persona": persona, "question": question})
    return cleaned


def validate_grades(data, count=3):
    """Return (grades, fix_first) or raise ValueError."""
    items = data.get("grades") if isinstance(data, dict) else None
    if not isinstance(items, list) or len(items) != count:
        raise ValueError(f"The AI did not return {count} grades.")
    grades = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("A grade was in the wrong format.")
        grade = {key: _clamp(item.get(key)) for key in WEIGHTS}
        grade["critique"] = str(item.get("critique", "")).strip()
        grade["stronger_answer"] = str(item.get("stronger_answer", "")).strip()
        grades.append(grade)
    fix_first = str(data.get("fix_first", "")).strip()
    return grades, fix_first


def apply_blank_rule(grades, answers):
    """Force zero scores for blank answers."""
    for grade, answer in zip(grades, answers):
        if not answer.strip():
            for key in WEIGHTS:
                grade[key] = 0.0
            grade["critique"] = "No answer was given, so this scores zero."
    return grades


def answer_score(grade):
    return round(10 * sum(grade[key] * w for key, w in WEIGHTS.items()))


def overall_score(grades):
    return round(sum(answer_score(g) for g in grades) / len(grades))


def readiness_label(score):
    if score >= 80:
        return "Investor-ready"
    if score >= 60:
        return "Getting there"
    if score >= 40:
        return "Needs work"
    return "Not ready yet"
