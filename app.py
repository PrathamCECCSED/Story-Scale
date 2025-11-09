import streamlit as st
import joblib
from statistics import mean
import pandas as pd
import math

# ---------- CONFIG ----------
st.set_page_config(page_title="Story Scale", page_icon="📈", layout="wide")

# ---------- LOAD MODEL ----------
model = joblib.load("model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# ---------- STYLE ----------
st.markdown("""
<style>
body { background-color: #0E1117; color: #E6EEF3; font-family: 'Inter', sans-serif; }
.card {
    background: linear-gradient(180deg, #111827 0%, #0B1116 100%);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 6px 18px rgba(2,6,23,0.6);
    margin-bottom: 18px;
}
.card-title { font-weight:700; font-size:18px; color:#E6EEF3; margin-bottom:8px; }
.big-metric { font-size:42px; font-weight:800; color:#7EF2A7; }
.subtle { color:#9FA6B2; font-size:13px; }
.reason { margin-left:6px; color:#D8E6F0; }
.badge { background:#1F2937; border-radius:8px; padding:4px 10px; color:#93C5FD; margin-right:6px; }
.task-table { width:100%; border-collapse: collapse; }
.task-table td { padding:6px 4px; vertical-align: top; }
.task-epic { color:#FACC15; font-weight:700; }
.task-feature { color:#A5B4FC; padding-left:10px; }
.task-task { color:#7DD3FC; padding-left:30px; }
.task-sub { color:#86EFAC; padding-left:50px; }
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
FIB = [1, 2, 3, 5, 8, 13, 21, 40]

def round_to_fib(x: float) -> int:
    return int(min(FIB, key=lambda v: abs(v - x)))

def get_complexity(sp: int) -> str:
    if sp <= 3: return "Low"
    if sp <= 8: return "Medium"
    return "High"

def sprint_weeks(sp: int, velocity: int):
    weeks = math.ceil((sp / velocity) * 2)
    if weeks < 1:
        weeks = 1
    return f"{weeks} week(s)"

def factual_reasoning(story_points: int, roles: list, category: str):
    facts = []
    if story_points > 13:
        facts.append("High story points suggest multiple integrations or major refactor.")
    elif story_points <= 3:
        facts.append("Low story points — likely UI enhancement or small bug fix.")
    else:
        facts.append("Moderate scope — involves 2–3 major dev roles.")
    facts.append(f"Involves {len(roles)} team roles ({', '.join(roles[:3])}...).")
    facts.append(f"Category: {category.title()} module, estimated effort scales with backend dependencies.")
    return facts

def generate_backlog(category: str):
    backlog = []
    if category == 'payment':
        backlog = [
            ["Epic", "Online Payments Integration"],
            ["Feature", "Integrate Razorpay API"],
            ["Task", "Setup payment gateway keys"],
            ["Subtask", "Add transaction logs and error handling"],
            ["Feature", "Implement payment confirmation UI"],
            ["Task", "Design payment success & failure screens"]
        ]
    elif category == 'auth':
        backlog = [
            ["Epic", "User Authentication"],
            ["Feature", "OAuth 2.0 Login Implementation"],
            ["Task", "Setup Google & Email Auth"],
            ["Subtask", "Store and refresh tokens securely"],
            ["Feature", "Password Reset Flow"],
            ["Task", "Create email OTP verification module"]
        ]
    elif category == 'analytics':
        backlog = [
            ["Epic", "Analytics Dashboard"],
            ["Feature", "Design Data Visualization UI"],
            ["Task", "Integrate Chart.js for visualization"],
            ["Subtask", "Implement filtering & export functionality"],
            ["Feature", "Backend Aggregation API"],
            ["Task", "Setup data warehouse queries"]
        ]
    else:
        backlog = [
            ["Epic", "Core Product Enhancement"],
            ["Feature", "Add new modular feature"],
            ["Task", "Implement API routes & UI"],
            ["Subtask", "Write test cases & documentation"]
        ]
    return backlog

def predict_and_explain(text: str, team_velocity: int = 20):
    vec = vectorizer.transform([text])
    raw_pred = float(model.predict(vec)[0])
    rounded_sp = round_to_fib(raw_pred)
    complexity = get_complexity(rounded_sp)
    category = "default"
    if any(k in text.lower() for k in ["payment", "upi", "checkout"]): category = "payment"
    elif any(k in text.lower() for k in ["login", "auth", "password", "oauth"]): category = "auth"
    elif any(k in text.lower() for k in ["dashboard", "analytics", "report"]): category = "analytics"
    
    roles = ["Frontend Developer", "Backend Developer", "QA Engineer"]
    if category == "analytics": roles.append("Data Engineer")
    if category == "payment": roles.append("Security/DevOps")

    reasons = factual_reasoning(rounded_sp, roles, category)
    backlog = generate_backlog(category)
    sprint_duration = sprint_weeks(rounded_sp, team_velocity)

    return {
        "predicted_raw": raw_pred,
        "story_points": rounded_sp,
        "complexity": complexity,
        "reasons": reasons,
        "roles": roles,
        "backlog": backlog,
        "sprint_duration": sprint_duration,
        "category": category
    }

def finalize_by_team_votes(ai_sp: int, team_votes: dict):
    if not team_votes:
        return {"final": ai_sp, "rationale": "No team votes provided — AI estimate retained."}
    avg = mean(team_votes.values())
    rounded = round_to_fib(avg)
    if abs(rounded - ai_sp) <= 2:
        return {"final": ai_sp, "rationale": "Consensus close to AI — accepted AI estimate."}
    return {"final": rounded, "rationale": "Scrum Master accepted team consensus."}

# ---------- SESSION ----------
if "cache" not in st.session_state:
    st.session_state.cache = None
if "votes" not in st.session_state:
    st.session_state.votes = ""

# ---------- UI ----------
st.markdown("<h1>📈 Story Scale</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#9FA6B2'>AI-based Agile Effort Estimator with Backlog Breakdown & Sprint Logic</p>", unsafe_allow_html=True)

story = st.text_area("✍️ Enter User Story", height=140, placeholder="As a user, I want to login using Google OAuth so I can sign in faster.")
team_velocity = st.number_input("🏃 Team Velocity (Story Points per Sprint)", min_value=5, max_value=200, value=20)

if st.button("Estimate Effort 🚀"):
    if story.strip():
        st.session_state.cache = predict_and_explain(story, team_velocity)
    else:
        st.warning("Please enter a story first.")

if st.session_state.cache:
    out = st.session_state.cache

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='card'><div class='card-title'>🎯 Effort Estimate</div><div class='big-metric'>{out['story_points']}</div><div class='subtle'>Raw: {out['predicted_raw']:.2f}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='card-title'>🧩 Complexity</div><b>{out['complexity']}</b></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='card-title'>🗓 Sprint Duration</div><b>{out['sprint_duration']}</b><div class='subtle'>Velocity impact applied</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='card'><div class='card-title'>📊 Category</div><b>{out['category'].title()}</b></div>", unsafe_allow_html=True)

    # ----- Reason for Effort -----
    st.markdown("<div class='card'><div class='card-title'>🧠 Reasons for Effort (Facts)</div>", unsafe_allow_html=True)
    for r in out['reasons']:
        st.markdown(f"- {r}")
    st.markdown("</div>", unsafe_allow_html=True)

    # ----- Professional Backlog Breakdown -----
    st.markdown("<div class='card'><div class='card-title'>🗂 Professional Backlog Breakdown</div>", unsafe_allow_html=True)
    st.markdown("<table class='task-table'>", unsafe_allow_html=True)
    for level, text in out["backlog"]:
        if level == "Epic":
            st.markdown(f"<tr><td class='task-epic'>🧱 {text}</td></tr>", unsafe_allow_html=True)
        elif level == "Feature":
            st.markdown(f"<tr><td class='task-feature'>📘 {text}</td></tr>", unsafe_allow_html=True)
        elif level == "Task":
            st.markdown(f"<tr><td class='task-task'>🛠️ {text}</td></tr>", unsafe_allow_html=True)
        else:
            st.markdown(f"<tr><td class='task-sub'>🔹 {text}</td></tr>", unsafe_allow_html=True)
    st.markdown("</table></div>", unsafe_allow_html=True)

    # ----- Team Voting -----
    st.markdown("<div class='card'><div class='card-title'>🧮 Team Voting (Planning Poker)</div><div class='subtle'>Enter votes like FE:8,BE:13,QA:5</div>", unsafe_allow_html=True)
    votes_raw = st.text_input("Team votes", value=st.session_state.votes)
    if st.button("Finalize by Scrum Master 🔨"):
        st.session_state.votes = votes_raw
        votes = {}
        try:
            for part in votes_raw.split(","):
                if ":" in part:
                    k, v = part.split(":")
                    votes[k.strip()] = int(v.strip())
        except:
            st.error("Invalid format! Use FE:8,BE:13")
            votes = {}
        final = finalize_by_team_votes(out['story_points'], votes)
        st.session_state.final = final

    if "final" in st.session_state:
        final = st.session_state.final
        st.markdown("<div class='card'><div class='card-title'>🔒 Scrum Master Final Decision</div>", unsafe_allow_html=True)
        st.success(f"✅ Final Effort: {final['final']} SP")
        st.caption(final["rationale"])
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br><br><center style='color:#9FA6B2'>Made with 💛 by Story Scale — Advanced Scrum AI Estimator</center>", unsafe_allow_html=True)

