import streamlit as st
import joblib
from statistics import mean
import pandas as pd

# ---------- CONFIG ----------
st.set_page_config(page_title="Story Scale", page_icon="📈", layout="wide")

# ---------- LOAD MODEL ----------
model = joblib.load("model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# ---------- STYLE ----------
st.markdown("""
<style>
    body { background-color: #0E1117; }
    .card {
        background: linear-gradient(180deg, #0F1720 0%, #0B1116 100%);
        border-radius: 12px;
        padding: 18px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 6px 18px rgba(2,6,23,0.6);
        margin-bottom: 14px;
    }
    .card-title { font-weight:700; font-size:16px; color:#E6EEF3; }
    .big-metric { font-size:40px; font-weight:800; color:#7EF2A7; }
    .small { font-size:13px; color:#9FA6B2; }
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
FIB = [1,2,3,5,8,13,21,40]

def round_to_fib(x: float) -> int:
    return int(min(FIB, key=lambda v: abs(v - x)))

def get_complexity(sp: int) -> str:
    if sp <= 3:
        return "Low"
    elif sp <= 8:
        return "Medium"
    else:
        return "High"

def sprint_classification(sp: int, velocity: int) -> str:
    if sp <= velocity:
        return "Fits in current sprint"
    elif sp <= velocity * 1.5:
        return "Consider next sprint or split"
    else:
        return "Split across 2+ sprints"

def parse_votes(vote_str: str):
    votes = {}
    try:
        pairs = [p.strip() for p in vote_str.split(",") if p.strip()]
        for p in pairs:
            role, val = p.split(":")
            votes[role.strip()] = int(val.strip())
    except:
        st.error("⚠️ Invalid vote format. Use FE:8,BE:13,QA:5")
    return votes

def finalize_by_team_votes(ai_sp: int, team_votes: dict):
    if not team_votes:
        return {"final": ai_sp, "rationale": "No team votes entered – AI estimate used."}

    avg = mean(team_votes.values())
    rounded = round_to_fib(avg)
    if abs(rounded - ai_sp) <= 2:
        return {"final": ai_sp, "rationale": "Team votes close to AI → kept AI estimate."}
    else:
        return {"final": rounded, "rationale": "Team consensus accepted (rounded)."}

# ---------- SESSION STATE ----------
if "result" not in st.session_state:
    st.session_state.result = None
if "final_result" not in st.session_state:
    st.session_state.final_result = None

# ---------- MAIN HEADER ----------
st.markdown("<h1 style='color:white;'>📈 Story Scale</h1>", unsafe_allow_html=True)
st.caption("AI-based User Story Effort Estimator for Agile Teams")

# ---------- INPUT ----------
story = st.text_area("✍️ Enter your User Story", placeholder="As a user, I want to login using Google OAuth so I can sign in faster.")
team_velocity = st.number_input("🏃‍♂️ Team velocity (Story Points)", min_value=5, max_value=100, value=20)

if st.button("Estimate Effort 🚀"):
    if story.strip() == "":
        st.warning("Please enter a story first.")
    else:
        vec = vectorizer.transform([story])
        raw_pred = float(model.predict(vec)[0])
        rounded = round_to_fib(raw_pred)
        complexity = get_complexity(rounded)
        sprint_msg = sprint_classification(rounded, team_velocity)
        st.session_state.result = {
            "story": story,
            "raw_pred": raw_pred,
            "rounded": rounded,
            "complexity": complexity,
            "sprint_msg": sprint_msg
        }
        st.session_state.final_result = None  # reset finalization

# ---------- DISPLAY RESULT ----------
if st.session_state.result:
    res = st.session_state.result

    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>🎯 Estimated Effort</div>
        <div class='big-metric'>{res['rounded']}</div>
        <div class='small'>Raw model output: {res['raw_pred']:.3f}</div>
        <br>
        <b>🧩 Complexity:</b> {res['complexity']}<br>
        <b>🚦 Sprint Suggestion:</b> {res['sprint_msg']}
    </div>
    """, unsafe_allow_html=True)

    # ---------- TEAM VOTES ----------
    st.markdown("<div class='card'><div class='card-title'>🧮 Team Voting (Planning Poker)</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Enter votes as comma-separated Role:points (e.g. FE:8,BE:13,QA:5)</div>", unsafe_allow_html=True)

    votes_input = st.text_input("Team Votes", value=st.session_state.get("votes_input", ""), key="votes_input")

    if st.button("Finalize by Scrum Master 🔨"):
        st.session_state.votes_input = votes_input
        votes = parse_votes(votes_input)
        final = finalize_by_team_votes(res["rounded"], votes)
        st.session_state.final_result = final

    # ---------- SHOW FINAL RESULT ----------
    if st.session_state.final_result:
        final = st.session_state.final_result
        st.success(f"✅ Final Effort: **{final['final']} Story Points**")
        st.caption(final["rationale"])

