# 🎤 Pitch Pressure Test

**Practice your pitch against the hardest questions before the real audience asks them.**

## The problem
Students and first-time founders rarely get honest, tough feedback on their pitch. Friends are polite, and practicing alone doesn't reveal the gaps. They find out in front of the real investor, judge, or customer.

## What it does
1. You paste a 60-second pitch.
2. Three AI personas each ask one hard question tailored to your pitch: an **Investor**, a **Customer**, and a **Rival**.
3. You type your answers.
4. An AI coach grades each answer on **directness, evidence, and clarity**, critiques it using your own words, and shows a stronger example answer.
5. You get a **Pitch Readiness Score** and the one thing to fix first. You can revise your answers and re-grade.

## How scoring works
The AI gives 0-10 ratings per dimension. The final score is computed in Python (`scoring.py`):
- Answer score = 10 × (0.40 × directness + 0.35 × evidence + 0.25 × clarity)
- Readiness score = average of the three answer scores
- Blank answers always score 0

The ratings are AI judgments (estimates), not objective measurements. The "stronger answer" is an example with placeholders, never fabricated statistics.

## Run locally
```bash
git clone https://github.com/garghitesh-11/AI-Vibeathon-project
cd AI-Vibeathon-project
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
# edit .env and paste your Gemini API key
streamlit run app.py
```
Get a free key at https://aistudio.google.com/apikey

## Deploy (Streamlit Community Cloud)
Push to GitHub, create an app at share.streamlit.io pointing at `app.py`, and add `GEMINI_API_KEY = "..."` under Settings → Secrets.

## Project structure
- `app.py` – Streamlit UI and flow
- `prompts.py` – persona and grader prompts
- `scoring.py` – validation and score formula

## Tech
Python, Streamlit, Google Gemini API (no custom model training).

## Limitations
- AI grading is subjective and can vary between runs.
- The app does not verify any market claims you make.
