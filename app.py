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
    st.caption(f"Debug: {type(e).__name__}: {e}")
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
        temperature=0.9,
    )

    content = resp.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(content)

        q = data["question"]
        choices = data["choices"]
        ans = data["answer"].strip().upper()

        # Final guardrails
        if ans not in ["A", "B", "C", "D"] or len(choices) != 4:
            return "Which unit measures resistance?", ["Volt", "Ohm", "Amp", "Watt"], "B"
# Prevent repeat questions (try a few times)
recent = st.session_state.get("recent_questions", [])[-8:]

tries = 0
while q in recent and tries < 3:
    tries += 1
    resp2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt + "\n\nMake it DIFFERENT from the recent questions list."}],
        temperature=1.0,
    )
    content2 = resp2.choices[0].message.content.strip()
    content2 = content2.replace("```json", "").replace("```", "").strip()
    data2 = json.loads(content2)

    q = data2["question"]
    choices = data2["choices"]
    ans = data2["answer"].strip().upper()

    if ans not in ["A", "B", "C", "D"] or len(choices) != 4:
        return "Which unit measures resistance?", ["Volt", "Ohm", "Amp", "Watt"], "B"
    
           
        st.session_state.recent_questions.append(q)
        return q, choices, ans

    except Exception:
        return "Which unit measures resistance?", ["Volt", "Ohm", "Amp", "Watt"], "B"
# ---------------- GAME UI ----------------

# Buttons
col1, col2, col3 = st.columns(3)
with col1:
    left = st.button("⬅️ Left Flipper")
with col2:
    advance = st.button("Advance Ball")
with col3:
    right = st.button("Right Flipper ➡️")

flipper_boost = 0.2 if left or right else 0.0

if st.button("Launch Ball"):
    st.session_state.ball = 0

if advance:
    st.session_state.ball += random.randint(10,20)

    base_drain = 0.05 + (st.session_state.ball / 400)
    drain_chance = max(0.01, base_drain - flipper_boost)

    if random.random() < drain_chance:
        st.warning("🕳️ DRAIN! Game Over.")
        st.session_state.ball = 0
        st.session_state.score = 0
        st.session_state.mult = 1
    else:
        if random.random() < 0.45:
            st.session_state.question = generate_question()
        else:
            st.session_state.score += 10 * st.session_state.mult

st.progress(min(100, st.session_state.ball))

if st.session_state.question:
    q, choices, ans = st.session_state.question
    choice = st.radio(q, ["A "+choices[0],"B "+choices[1],"C "+choices[2],"D "+choices[3]])
    if st.button("Submit Answer"):
        if choice.startswith(ans):
            st.success("Correct!")
            st.session_state.score += 100 * st.session_state.mult
            st.session_state.mult += 1
        else:
            st.error("Wrong!")
            st.session_state.mult = 1
        st.session_state.question = None
