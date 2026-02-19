import os
import random
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI Pinball Quiz", page_icon="🕹️", layout="centered")
st.title("🕹️ AI Pinball Quiz")
st.caption("Hit bumpers ➜ answer AI trivia ➜ rack up score.")

def get_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

if "score" not in st.session_state:
    st.session_state.score = 0
if "mult" not in st.session_state:
    st.session_state.mult = 1
if "ball_pos" not in st.session_state:
    st.session_state.ball_pos = 0
if "question" not in st.session_state:
    st.session_state.question = None

st.sidebar.write(f"Score: {st.session_state.score}")
st.sidebar.write(f"Multiplier: x{st.session_state.mult}")

def generate_question():
    client = get_client()
    if client is None:
        return "Which unit measures resistance?", ["Volt","Ohm","Amp","Watt"], "B"

    import json
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role":"user",
            "content":"Create a simple multiple choice trivia question. Return JSON with question, choices, answer(A-D)"
        }]
    )
    data = json.loads(resp.choices[0].message.content)
    return data["question"], data["choices"], data["answer"]

if st.button("Launch Ball"):
    st.session_state.ball_pos = 0

if st.button("Advance Ball"):
    st.session_state.ball_pos += random.randint(10,20)
    if random.random() < 0.4:
        st.session_state.question = generate_question()

st.progress(st.session_state.ball_pos)

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
