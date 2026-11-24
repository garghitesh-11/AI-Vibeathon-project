import json
import os
import re
import time

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

import prompts
import scoring

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

st.set_page_config(page_title="Pitch Pressure Test", page_icon="🎤", layout="centered")

PERSONA_STYLE = {
    "Investor": ("💰", "#f5b942"),
    "Customer": ("🧑", "#4cc2ff"),
    "Rival": ("🥊", "#ff6b6b"),
}

st.markdown(
    """
    <style>
    .persona-card {border-left: 5px solid var(--c); padding: 0.6rem 1rem;
        margin: 1rem 0 0.4rem 0; background: rgba(128,128,128,0.10); border-radius: 6px;}
    .persona-name {font-weight: 700; margin-bottom: 0.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- AI helper ----------
def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None


def call_json(prompt, retries=2):
    """Call Gemini and return parsed JSON. Raises RuntimeError with a friendly message."""
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Add it to your .env file (local) or Streamlit secrets (deployed)."
        )
    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", temperature=0.7
                ),
            )
            text = (response.text or "").strip()
            text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        except Exception as exc:  # network, quota, bad JSON...
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"The AI request failed after several tries: {last_error}")


# ---------- State ----------
def reset():
    for k in ["stage", "pitch", "questions", "answers", "grades", "fix_first"]:
        st.session_state.pop(k, None)
    for i in range(3):
        st.session_state.pop(f"ans_{i}", None)


if "stage" not in st.session_state:
    st.session_state.stage = "pitch"

st.title("🎤 Pitch Pressure Test")
st.caption("Paste your pitch. An investor, a customer and a rival will ask the hard questions.")

# ---------- Stage 1: pitch ----------
if st.session_state.stage == "pitch":
    pitch = st.text_area(
        "Your 60-second pitch",
        height=220,
        placeholder="What is it, who is it for, what problem does it solve, and why you?",
        value=st.session_state.get("pitch", ""),
    )
    if st.button("Start the grilling", type="primary"):
        if len(pitch.strip()) < 40:
            st.warning("Please write at least a couple of sentences so the questions can be specific.")
        else:
            with st.spinner("The investor, customer and rival are reading your pitch..."):
                try:
                    data = call_json(prompts.questions_prompt(pitch.strip()))
                    st.session_state.questions = scoring.validate_questions(data)
                    st.session_state.pitch = pitch.strip()
                    st.session_state.stage = "answer"
                    st.rerun()
                except (RuntimeError, ValueError) as exc:
                    st.error(f"Could not generate questions: {exc}")

# ---------- Stage 2: answers ----------
elif st.session_state.stage == "answer":
    with st.expander("Your pitch", expanded=False):
        st.write(st.session_state.pitch)

    for i, q in enumerate(st.session_state.questions):
        icon, color = PERSONA_STYLE.get(q["persona"], ("❓", "#999999"))
        st.markdown(
            f'<div class="persona-card" style="--c:{color}"><div class="persona-name">{icon} {q["persona"]}</div>'
            f'{q["question"]}</div>',
            unsafe_allow_html=True,
        )
        st.text_area("Your answer", key=f"ans_{i}", height=110, label_visibility="collapsed",
                     placeholder="Answer as you would in a real pitch...")

    col1, col2 = st.columns([1, 1])
    if col2.button("← Edit pitch"):
        st.session_state.stage = "pitch"
        st.rerun()
    if col1.button("Grade my answers", type="primary"):
        answers = [st.session_state.get(f"ans_{i}", "").strip() for i in range(3)]
        if not any(answers):
            st.warning("Write at least one answer first.")
        else:
            qa = [
                {"persona": q["persona"], "question": q["question"], "answer": a}
                for q, a in zip(st.session_state.questions, answers)
            ]
            with st.spinner("The coach is grading your answers..."):
                try:
                    data = call_json(prompts.grading_prompt(st.session_state.pitch, qa))
                    grades, fix_first = scoring.validate_grades(data)
                    st.session_state.grades = scoring.apply_blank_rule(grades, answers)
                    st.session_state.fix_first = fix_first
                    st.session_state.answers = answers
                    st.session_state.stage = "results"
                    st.rerun()
                except (RuntimeError, ValueError) as exc:
                    st.error(f"Could not grade the answers: {exc}")

# ---------- Stage 3: results ----------
else:
    grades = st.session_state.grades
    score = scoring.overall_score(grades)
    st.header("Pitch Readiness Score")
    c1, c2 = st.columns([1, 2])
    c1.metric("Score", f"{score}/100")
    c2.progress(score / 100, text=scoring.readiness_label(score))
    st.caption(
        "Score = average of 3 answer scores; each answer = 40% directness + 35% evidence + 25% clarity. "
        "The 0-10 ratings are AI judgments (estimates), not objective measurements."
    )

    if st.session_state.fix_first:
        st.info(f"**Fix this first:** {st.session_state.fix_first}")

    for q, a, g in zip(st.session_state.questions, st.session_state.answers, grades):
        icon, _ = PERSONA_STYLE.get(q["persona"], ("❓", "#999999"))
        with st.expander(f"{icon} {q['persona']} — {scoring.answer_score(g)}/100", expanded=True):
            st.markdown(f"**Question:** {q['question']}")
            st.markdown(f"**Your answer:** {a or '_(blank)_'}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Directness", f"{g['directness']:.0f}/10")
            m2.metric("Evidence", f"{g['evidence']:.0f}/10")
            m3.metric("Clarity", f"{g['clarity']:.0f}/10")
            st.markdown(f"**Critique:** {g['critique']}")
            if g["stronger_answer"]:
                st.markdown(f"**A stronger answer (example, fill in your real numbers):** {g['stronger_answer']}")

    col1, col2 = st.columns(2)
    if col1.button("Revise my answers"):
        st.session_state.stage = "answer"
        st.rerun()
    if col2.button("Test a new pitch", type="primary"):
        reset()
        st.rerun()
