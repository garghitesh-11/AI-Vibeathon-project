"""All prompts live here so they can be improved without touching the UI."""

PERSONAS = {
    "Investor": "Cares about market size, business model, traction, and why this can become a real business.",
    "Customer": "Cares about whether they would actually use or pay for this, and what it replaces in their life.",
    "Rival": "A competitor who looks for how to copy, undercut, or out-execute this idea.",
}


def questions_prompt(pitch: str) -> str:
    persona_lines = "\n".join(f"- {name}: {desc}" for name, desc in PERSONAS.items())
    return f"""You are running a pitch pressure test. Read the pitch below and write exactly
three hard questions, one from each persona:

{persona_lines}

Rules:
- Each question must target a specific weakness or gap in THIS pitch. Use details from it.
- No generic questions such as "what is your business model?" unless the pitch gives a reason to ask.
- One question per persona, maximum 30 words each. No praise, no preamble.
- Order: Investor, Customer, Rival.

Return ONLY valid JSON in this exact shape:
{{"questions": [
  {{"persona": "Investor", "question": "..."}},
  {{"persona": "Customer", "question": "..."}},
  {{"persona": "Rival", "question": "..."}}
]}}

PITCH:
\"\"\"{pitch}\"\"\"
"""


def grading_prompt(pitch: str, qa_pairs: list) -> str:
    qa_text = "\n\n".join(
        f"[{i + 1}] {qa['persona']} asked: {qa['question']}\nUser answered: {qa['answer'] or '(no answer)'}"
        for i, qa in enumerate(qa_pairs)
    )
    return f"""You are a strict but fair pitch coach. Grade each answer the user gave to the
hard questions about their pitch.

Rate each answer from 0 to 10 on:
- directness: did it actually answer the question asked, rather than dodging?
- evidence: does it use specifics (numbers, examples, named users, a clear mechanism) instead of vague claims?
- clarity: is it easy to follow and concise?

Rules:
- Be honest. Do not inflate scores. Vague answers get low evidence scores.
- In "critique", point to the user's own words (2-3 sentences) and say what is missing.
- In "stronger_answer", write a better example answer in the user's voice. NEVER invent
  statistics, market data, or facts. Where a number is needed, use a placeholder like [your number].
- "fix_first" is one sentence naming the single most important thing to improve.
- Judge only what is written. Do not assume facts that are not in the pitch or answers.

Return ONLY valid JSON in this exact shape, with grades in the same order as the questions:
{{"grades": [
  {{"directness": 0, "evidence": 0, "clarity": 0, "critique": "...", "stronger_answer": "..."}},
  {{"directness": 0, "evidence": 0, "clarity": 0, "critique": "...", "stronger_answer": "..."}},
  {{"directness": 0, "evidence": 0, "clarity": 0, "critique": "...", "stronger_answer": "..."}}
],
"fix_first": "..."}}

PITCH:
\"\"\"{pitch}\"\"\"

QUESTIONS AND ANSWERS:
{qa_text}
"""
