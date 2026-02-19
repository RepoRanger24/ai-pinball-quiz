import random
import streamlit as st
from openai import OpenAI
import pandas as pd
import os

st.set_page_config(page_title="AI Pinball Quiz", page_icon="🕹️")
st.title("🕹️ AI Pinball Quiz")

def get_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

if "score" not in st.session_state:
    st.session_state.score = 0
if "mult" not in st.session_state:
    st.session_state.mult = 1
if "ball" not in st.session_state:
    st.session_state.ball = 0
if "question" not in st.session_state:
    st.session_state.question = None
# Player name
if "player" not in st.session_state:
    st.session_state.player = "Chip"

st.session_state.player = st.sidebar.text_input("Player name", st.session_state.player)

SCOREFILE = "highscores.csv"

def load_scores():
    if os.path.exists(SCOREFILE):
        return pd.read_csv(SCOREFILE)
    return pd.DataFrame(columns=["name", "score"])

def save_scores(df):
    df.to_csv(SCOREFILE, index=False)

scores_df = load_scores()

st.sidebar.write("Score:", st.session_state.score)
st.sidebar.write("Multiplier:", st.session_state.mult)

def generate_question():
    client = get_client()
    if client is None:
        return "Which unit measures resistance?", ["Volt","Ohm","Amp","Watt"], "B"
    import json
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":"Create a trivia question. Return JSON with question, choices, answer(A-D)"}]
    )
    data = json.loads(resp.choices[0].message.content)
    return data["question"], data["choices"], data["answer"]

if st.button("Launch Ball"):
    st.session_state.ball = 0

col1, col2, col3 = st.columns(3)

with col1:
    left = st.button("⬅️ Left Flipper")
with col2:
    advance = st.button("Advance Ball")
with col3:
    right = st.button("Right Flipper ➡️")

flipper_boost = 0.0
if left or right:
    flipper_boost = 0.20

if advance:
    st.session_state.ball += random.randint(10, 20)

    base_drain = 0.10 + (st.session_state.ball / 200)
    drain_chance = max(0.02, base_drain - flipper_boost)

      if random.random() < drain_chance:
        st.warning("🕳️ DRAIN! Game Over.")

        # Save score if it's good enough
        scores_df = load_scores()
        new_row = pd.DataFrame([{"name": st.session_state.player, "score": st.session_state.score}])
        scores_df = pd.concat([scores_df, new_row], ignore_index=True)
        scores_df = scores_df.sort_values("score", ascending=False).head(10)
        save_scores(scores_df)

        # Reset game
        st.session_state.ball = 0
        st.session_state.mult = 1
        st.session_state.score = 0
 
# Save score if it's good enough
scores_df = load_scores()
new_row = pd.DataFrame([{"name": st.session_state.player, "score": st.session_state.score}])
scores_df = pd.concat([scores_df, new_row], ignore_index=True)
scores_df = scores_df.sort_values("score", ascending=False).head(10)
save_scores(scores_df)

# Reset game state (keep highscores)
st.session_state.ball = 0
st.session_state.mult = 1
st.session_state.score = 0
   
    else:
        if random.random() < 0.45:
            st.session_state.question = generate_question()
        else:
            st.session_state.score += 10 * st.session_state.mult

st.progress(st.session_state.ball)

if st.session_state.question:
    q, choices, ans = st.session_state.question
    choice = st.radio(q, ["A "+choices[0],"B "+choices[1],"C "+choices[2],"D "+choices[3]])
    if st.button("Submit"):
        if choice.startswith(ans):
            st.session_state.score += 100 * st.session_state.mult
            st.session_state.mult += 1
            st.success("Correct!")
        else:
            st.session_state.mult = 1
            st.error("Wrong!")
        st.session_state.question = None
st.subheader("🏆 High Scores (Top 10)")
scores_df = load_scores()
if len(scores_df) == 0:
    st.info("No high scores yet. Play a round!")
else:
    st.dataframe(scores_df, use_container_width=True, hide_index=True)
