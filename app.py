# Replace your app.py with this full file
import streamlit as st
import joblib
import re
from statistics import mean

# ---------- CONFIG ----------
st.set_page_config(page_title="Story Scale", page_icon="📈", layout="wide")

# ---------- LOAD MODEL ----------
# Must have model.joblib and vectorizer.joblib in repo root
model = joblib.load("model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# ---------- STYLING ----------
st.markdown("""
    <style>
        body { background-color: #0E1117; }
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        .title { font-size:42px; font-weight:800; color:white; padding-bottom:6px; }
        .sub { font-size:16px; color:#9FA6B2; padding-bottom:18px; }
        .card { background-color:#161B22; padding:18px 22px; border-radius:12px; border:1px solid #262E38; margin-bottom:12px; }
        .metric { font-size:28px; font-weight:700; color:#4ADE80; }
        .metric-label { font-size:14px; color:#9FA6B2; }
        .small { font-size:13px; color:#9FA6B2; }
        pre { background:#0E1117; color:#d0d6de; }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<div class='title'>📈 Story Scale</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>AI-based User Story Effort Estimator — explains why, who, and how to finish.</div>", unsafe_allow_html=True)

# ---------- Helper logic ----------
FIB = [1,2,3,5,8,13,21,40]

ROLE_RULES = {
    'payment': {
        'roles': ['Backend Developer','Frontend Developer','QA Engineer','Security/DevOps'],
        'reasons': ['payment API integration', 'validation & reconciliation', 'security + encryption', 'callback handling'],
        'tasks': ['Setup payment provider credentials','Implement payment API endpoints','UI payment flow','Add payment tests']
    },
    'auth': {
        'roles': ['Frontend Developer','Backend Developer','QA Engineer'],
        'reasons': ['authentication flow', 'token handling', 'session management', 'redirects'],
        'tasks': ['Create auth endpoints','Implement login UI','Token storage & refresh','Test auth flows']
    },
    'analytics': {
        'roles': ['Backend Developer','Data Engineer','Frontend Developer','QA Engineer'],
        'reasons': ['data aggregation', 'filters and exports', 'charting library', 'data performance'],
        'tasks': ['Create analytics API','Design DB aggregates','Implement frontend charts','Add analytics tests']
    },
    'default': {
        'roles': ['Frontend Developer','Backend Developer','QA Engineer'],
        'reasons': ['feature implementation','integration points','testing'],
        'tasks': ['Define API contract','Implement UI','Create tests']
    }
}

ROLE_INNER_STEPS = {
    'Frontend Developer': [
        "Design/implement UI components",
        "Call backend APIs and handle UX states",
        "Add client-side validation and error handling"
    ],
    'Backend Developer': [
        "Implement API endpoints and business logic",
        "Ensure data persistence and data models",
        "Add input validation and error handling"
    ],
    'QA Engineer': [
        "Write test cases for happy & edge flows",
        "Run cross-browser / cross-device tests",
        "Validate error handling and retries"
    ],
    'Data Engineer': [
        "Design ETL / data pipeline",
        "Aggregate metrics and maintain data schemas"
    ],
    'Security/DevOps': [
        "Ensure secure credential storage",
        "Add monitoring and logging",
        "Deploy secure infra and rotate secrets"
    ]
}

def keyword_category(s: str) -> str:
    s_low = s.lower()
    if any(k in s_low for k in ['upi','payment','checkout','card','payment gateway','stripe','paytm','razorpay']):
        return 'payment'
    if any(k in s_low for k in ['login','signin','sign in','oauth','google','auth','password','2fa','two-factor','otp']):
        return 'auth'
    if any(k in s_low for k in ['analytics','dashboard','filters','export','report','chart','metrics']):
        return 'analytics'
    return 'default'

def round_to_fib(x: float) -> int:
    return int(min(FIB, key=lambda v: abs(v - x)))

def get_complexity(sp: int) -> str:
    if sp <= 3:
        return "Low"
    if sp <= 8:
        return "Medium"
    return "High"

def sprint_classification(sp: int, team_velocity: int) -> str:
    if sp <= team_velocity:
        return f"Fits in current sprint (team velocity = {team_velocity} SP)"
    if sp <= team_velocity * 1.5:
        return "Recommend next sprint or split tasks"
    return "Split across 2 or more sprints"

def predict_and_explain(text: str, team_velocity: int = 20):
    # model expects raw text (vectorizer handles tokenization used at train time)
    vec = vectorizer.transform([text])
    raw_pred = float(model.predict(vec)[0])
    rounded_sp = round_to_fib(raw_pred)
    complexity = get_complexity(rounded_sp)
    cat = keyword_category(text)
    rules = ROLE_RULES.get(cat, ROLE_RULES['default'])
    reasons = rules['reasons']
    roles = rules['roles']
    tasks = rules['tasks']
    sprint = sprint_classification(rounded_sp, team_velocity)
    return {
        "predicted_raw": raw_pred,
        "story_points": rounded_sp,
        "complexity": complexity,
        "reasons": reasons,
        "roles": roles,
        "role_inner_steps": ROLE_INNER_STEPS,
        "recommended_tasks": tasks,
        "sprint_suggestion": sprint,
        "category": cat
    }

def finalize_by_team_votes(ai_sp: int, team_votes: dict):
    # team_votes e.g. {'FE':8,'BE':13,'QA':5}
    votes = list(team_votes.values())
    if len(votes) == 0:
        return {
            "ai_suggestion": ai_sp,
            "team_avg": None,
            "team_rounded": None,
            "final_story_points": ai_sp,
            "rationale": "No team votes provided — AI suggestion used."
        }
    avg_vote = mean(votes)
    team_rounded = int(min(FIB, key=lambda v: abs(v - avg_vote)))
    # decision rule: if team average close to AI -> accept AI else accept team rounded
    if abs(team_rounded - ai_sp) <= 2:
        final = ai_sp
        rationale = "AI estimate accepted (team consensus within +/-2)."
    else:
        final = team_rounded
        rationale = "Scrum Master accepted team consensus (rounded)."
    return {
        "ai_suggestion": ai_sp,
        "team_avg": round(avg_vote,2),
        "team_rounded": team_rounded,
        "final_story_points": final,
        "rationale": rationale
    }

# ---------- UI ----------
with st.container():
    st.write("")  # spacing

left, right = st.columns([2,1])

with left:
    story = st.text_area("User Story", height=140,
                         placeholder="ex: As a user, I want to login using Google OAuth so I can sign in faster")
    team_velocity = st.number_input("Team velocity (story points)", min_value=5, max_value=100, value=20, step=1)
    if st.button("Estimate Effort 🚀"):
        if story.strip() == "":
            st.warning("Please enter a user story.")
        else:
            out = predict_and_explain(story, team_velocity=team_velocity)

            # Top result card
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                        f"<div><div class='metric'>{out['story_points']}</div>"
                        f"<div class='metric-label'>Predicted Story Points</div></div>"
                        f"<div style='text-align:right;'><div class='small'>Raw model value</div>"
                        f"<div style='font-weight:700;color:#D1D5DB'>{out['predicted_raw']:.3f}</div></div>"
                        f"</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Complexity + reasons + tasks + sprint
            st.subheader("Explanation")
            st.markdown(f"**Complexity:** {out['complexity']}")
            st.markdown("**Reason(s) for this effort:**")
            for r in out['reasons']:
                st.write("- " + r)

            st.markdown("**Recommended Backlog Tasks:**")
            for i,t in enumerate(out['recommended_tasks'], start=1):
                st.write(f"{i}. {t}")

            st.markdown(f"**Sprint Suggestion:** {out['sprint_suggestion']}")

            # Roles and inner steps
            st.subheader("Roles Required & Inner Steps")
            for role in out['roles']:
                st.markdown(f"**{role}**")
                steps = out['role_inner_steps'].get(role, [])
                for s in steps:
                    st.write("- " + s)

            # Team voting input for Scrum Master finalization
            st.subheader("Team Voting (Planning Poker) — Enter votes here")
            st.markdown("Enter as comma separated `Role:points`, e.g. `FE:8,BE:13,QA:5`")
            votes_raw = st.text_input("Team votes (optional)")
            if st.button("Finalize by Scrum Master"):
                # parse votes
                votes = {}
                try:
                    if votes_raw.strip():
                        parts = [p.strip() for p in votes_raw.split(",") if p.strip()]
                        for p in parts:
                            if ":" not in p:
                                raise ValueError("Use Role:points format")
                            k,v = p.split(":")
                            votes[k.strip()] = int(v.strip())
                    final = finalize_by_team_votes(out['story_points'], votes)
                    st.subheader("Scrum Master Final Decision")
                    st.write(f"AI suggestion: **{final['ai_suggestion']} SP**")
                    if final['team_avg'] is not None:
                        st.write(f"Team average: **{final['team_avg']}** → rounded to **{final['team_rounded']} SP**")
                    st.success(f"Final committed: **{final['final_story_points']} SP**")
                    st.caption(final['rationale'])
                except Exception as e:
                    st.error("Could not parse votes. Use format `FE:8,BE:13,QA:5`")

with right:
    st.markdown("<div class='card'><strong>Quick Help</strong><br><br>"
                "• Paste a user story in Agile style.<br>"
                "• Longer stories are more accurate.<br>"
                "• Use the Team votes box to enter estimates and finalize.</div>", unsafe_allow_html=True)

st.markdown("<br><br><center style='color:#666'>Made with 💛 by Story Scale AI</center>", unsafe_allow_html=True)
