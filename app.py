import os
import streamlit as st
import pandas as pd
import random
from openai import OpenAI
from supabase import create_client




st.set_page_config(page_title="AI Pinball Quiz", page_icon="🕹️")
st.title("🕹️ AI Pinball Quiz")

def get_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        return None
    return OpenAI(api_key=api_key)
  # Connect to Supabase
def get_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)  

# High Scores (Supabase)
st.subheader("🏆 High Scores")

scores_df = pd.DataFrame(columns=["name", "score"])  # <-- add this

try:
    db = get_db()
    res = db.table("scores").select("*").order("score", desc=True).limit(10).execute()

    if res.data:
        scores_df = pd.DataFrame(res.data)[["name", "score"]]
        st.dataframe(scores_df, use_container_width=True, hide_index=True)
    else:
        st.info("No scores yet!")

except Exception as e:
    st.warning("High scores not available yet.")
# Game state
if "score" not in st.session_state:
    st.session_state.score = 0
if "mult" not in st.session_state:
    st.session_state.mult = 1
if "ball" not in st.session_state:
    st.session_state.ball = 0
if "question" not in st.session_state:
    st.session_state.question = None
if "player" not in st.session_state:
    st.session_state.player = "Player"
st.session_state.player = st.sidebar.text_input("Player Name", st.session_state.player)
if "recent_questions" not in st.session_state:
    st.session_state.recent_questions = []
topic = st.sidebar.selectbox(
    "Question topic",
    ["Fun trivia", "Electrical", "CNC/Controls", "Safety (NFPA/OSHA)", "AI basics"]
)

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"]
)



st.sidebar.write("Score:", st.session_state.score)
st.sidebar.write("Multiplier:", st.session_state.mult)

SCOREFILE = "highscores.csv"

def load_scores():
    if os.path.exists(SCOREFILE):
        return pd.read_csv(SCOREFILE)
    return pd.DataFrame(columns=["name","score"])

def save_scores(df):
    df.to_csv(SCOREFILE, index=False)

def generate_question(topic="Fun trivia", difficulty="Easy"):
    client = get_client()
    if client is None:
        return "Which unit measures resistance?", ["Volt", "Ohm", "Amp", "Watt"], "B"

    import json
    recent = st.session_state.get("recent_questions", [])[-5:]
    prompt = f"""
Create ONE multiple-choice question.

Topic: {topic}
Difficulty: {difficulty}

Return ONLY valid JSON in this exact schema:
{{
  "question": "text",
  "choices": ["A text","B text","C text","D text"],
  "answer": "A"  // must be A, B, C, or D
}}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = resp.choices[0].message.content.strip()

    # Safety: if model wraps JSON in code fences, strip them
    content = content.replace("```json", "").replace("```", "").strip()

    data = json.loads(content)

    q = data["question"]
    choices = data["choices"]
    ans = data["answer"].strip().upper()
# Prevent repeat questions (simple version)
recent = st.session_state.get("recent_questions", [])[-5:]
# (we removed recursion to keep things stable)

# Final guardrails
if ans not in ["A", "B", "C", "D"] or len(choices) != 4:
    return "Which unit measures resistance?", ["Volt", "Ohm", "Amp", "Watt"], "B"

st.session_state.recent_questions.append(q)
return q, choices, ans
