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
.progress-bar {
    height: 10px; border-radius:8px; margin-top:8px;
    background: linear-gradient(90deg, #22C55E, #16A34A);
}
h1 { color:#E6EEF3; font-weight:800; margin-bottom:0; }
.highlight { color:#4ADE80; font-weight:700; }
.reason { margin-left:6px; color:#D8E6F0; }
.badge { background:#1F2937; border-radius:8px; padding:4px 10px; color:#93C5FD; margin-right:6px; }
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
FIB = [1, 2, 3, 5, 8, 13, 21, 40]

ROLE_RULES = {
    'payment': {
        'roles': ['Backend Developer','Frontend Developer','QA Engineer','Security/DevOps'],
        'reasons': ['Integration with 3rd party payment APIs','Complex data validation & security compliance','Transaction logging & audit trail','Error handling & retries'],
        'tasks': ['Setup payment gateway','Implement payment routes','UI payment flow','Automate payment tests']
    },
    'auth': {
        'roles': ['Frontend Developer','Backend Developer','QA Engineer'],
        'reasons': ['User authentication flow','Session & token management','OAuth complexity','Security testing'],
        'tasks': ['Create auth endpoints','Design login UI','Token refresh handling','Write test cases']
    },
    'analytics': {
        'roles': ['Backend Developer','Data Engineer','Frontend Developer','QA Engineer'],
        'reasons': ['Data aggregation & transformation','Chart rendering complexity','Filter and query optimization'],
        'tasks': ['Create analytics API','Design DB aggregates','Implement charts','Add analytics tests']
    },
    'default': {
        'roles': ['Frontend Developer','Backend Developer','QA Engineer'],
        'reasons': ['General feature complexity','Integration and testing effort'],
        'tasks': ['Define API contract','Implement UI','Write unit tests']
    }
}

ROLE_INNER_STEPS = {
    'Frontend Developer': [
        "Design and implement responsive UI components",
        "Integrate with backend APIs and manage state",
        "Add validation and error handling"
    ],
    'Backend Developer': [
        "Design database models and schema",
        "Implement business logic and APIs",
        "Integrate with external services if needed"
    ],
    'QA Engineer': [
        "Design manual test cases",
        "Implement automation suite",
        "Perform regression & performance testing"
    ],
    'Security/DevOps': [
        "Review API security",
        "Setup CI/CD pipelines",
        "Monitor and deploy securely"
    ]
}

def round_to_fib(x: float) -> int:
    return int(min(FIB, key=lambda v: abs(v - x)))

def get_complexity(sp: int) -> str:
    if sp <= 3: return "Low"
    if sp <= 8: return "Medium"
    return "High"

def sprint_weeks(sp: int, velocity: int):
    # assume 1 sprint = 2 weeks
    weeks = math.ceil(sp / velocity * 2)
    return f"{weeks} week(s)"

def predict_and_explain(text: str, team_velocity: int = 20):
    vec = vectorizer.transform([text])
    raw_pred = float(model.predict(vec)[0])
    rounded_sp = round_to_fib(raw_pred)
    complexity = get_complexity(rounded_sp)
    cat = 'default'
    for k in ROLE_RULES.keys():
        if k in text.lower():
            cat = k
    rules = ROLE_RULES[cat]
    sprint_time = sprint_weeks(rounded_sp, team_velocity)
    return {
        "predicted_raw": raw_pred,
        "story_points": rounded_sp,
        "complexity": complexity,
        "reasons": rules['reasons'],
        "roles": rules['roles'],
        "role_inner_steps": ROLE_INNER_STEPS,
        "recommended_tasks": rules['tasks'],
        "sprint_weeks": sprint_time,
        "category": cat
    }

def finalize_by_team_votes(ai_sp: int, team_votes: dict):
    votes = list(team_votes.values())
    if not votes:
        return {"final": ai_sp, "rationale": "No team votes provided — AI suggestion used."}
    avg = mean(votes)
    rounded = round_to_fib(avg)
    if abs(rounded - ai_sp) <= 2:
        final = ai_sp
        rationale = "Consensus aligns with AI — accepted AI estimate."
    else:
        final = rounded
        rationale = "Scrum Master accepted team consensus."
    return {"final": final, "rationale": rationale}

# ---------- SESSION ----------
if "cache" not in st.session_state:
    st.session_state.cache = None
if "votes" not in st.session_state:
    st.session_state.votes = ""

# ---------- UI ----------
st.markdown("<h1>📈 Story Scale</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#9FA6B2'>AI-driven Agile Estimation with Transparency, Reasoning, and Scrum Insights</p>", unsafe_allow_html=True)

story = st.text_area("✍️ Enter User Story", height=140, placeholder="As a user, I want to login using Google OAuth so I can sign in faster.")
team_velocity = st.number_input("🏃 Team Velocity (SP per Sprint)", min_value=5, max_value=200, value=20)

if st.button("Estimate Effort 🚀"):
    if story.strip():
        st.session_state.cache = predict_and_explain(story, team_velocity)
    else:
        st.warning("Please enter a user story.")

if st.session_state.cache:
    out = st.session_state.cache

    # --- Core metrics row ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='card'><div class='card-title'>🎯 Effort Estimate</div><div class='big-metric'>{out['story_points']}</div><div class='subtle'>Raw model: {out['predicted_raw']:.3f}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='card-title'>🧩 Complexity</div><b>{out['complexity']}</b><div class='progress-bar'></div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='card-title'>🗓 Sprint Duration</div><b>{out['sprint_weeks']}</b><div class='subtle'>Based on team velocity</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='card'><div class='card-title'>📊 Category</div><b>{out['category'].capitalize()}</b></div>", unsafe_allow_html=True)

    # --- Reason for Effort ---
    st.markdown("<div class='card'><div class='card-title'>🧠 Reasons for Effort</div>", unsafe_allow_html=True)
    for reason in out['reasons']:
        st.markdown(f"- {reason}")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Backlogs / Tasks ---
    st.markdown("<div class='card'><div class='card-title'>🗂 Recommended Backlog Tasks</div>", unsafe_allow_html=True)
    for i, task in enumerate(out['recommended_tasks'], 1):
        st.markdown(f"{i}. {task}")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Roles & Steps ---
    st.markdown("<div class='card'><div class='card-title'>👥 Roles & Inner Steps</div>", unsafe_allow_html=True)
    for role in out['roles']:
        st.markdown(f"<div class='badge'>{role}</div>", unsafe_allow_html=True)
        for step in out['role_inner_steps'].get(role, []):
            st.markdown(f"- {step}")
        st.markdown("")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Team Voting ---
    st.markdown("<div class='card'><div class='card-title'>🧮 Team Voting (Planning Poker)</div><div class='subtle'>Enter votes like FE:8,BE:13,QA:5</div>", unsafe_allow_html=True)
    votes_raw = st.text_input("Team votes", value=st.session_state.votes)
    if st.button("Finalize by Scrum Master 🔨"):
        st.session_state.votes = votes_raw
        votes = {}
        for v in votes_raw.split(","):
            if ":" in v:
                k, val = v.split(":")
                votes[k.strip()] = int(val.strip())
        final = finalize_by_team_votes(out['story_points'], votes)
        st.session_state.final = final

    if "final" in st.session_state:
        final = st.session_state.final
        st.markdown("<div class='card'><div class='card-title'>🔒 Scrum Master Final Decision</div>", unsafe_allow_html=True)
        st.success(f"Final Effort: **{final['final']} SP**")
        st.caption(final["rationale"])
        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<br><br><center style='color:#9FA6B2'>Made with 💛 by Story Scale — Advanced Scrum AI Estimator</center>", unsafe_allow_html=True)
