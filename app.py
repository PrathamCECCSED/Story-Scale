import streamlit as st
import joblib
from statistics import mean
import pandas as pd
import io

# ---------- CONFIG ----------
st.set_page_config(page_title="Story Scale", page_icon="📈", layout="wide")

# ---------- LOAD MODEL ----------
model = joblib.load("model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# ---------- STYLE ----------
st.markdown("""
    <style>
      .container { background-color: #0B0F14; color: #E6EEF3; }
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
      .subtle { color:#9FA6B2; font-size:13px; }
      .small { font-size:13px; color:#B7C0CC; }
      .reason { margin-left:6px; color:#D8E6F0; }
    </style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
FIB = [1, 2, 3, 5, 8, 13, 21, 40]

ROLE_RULES = {
    'payment': {
        'roles': ['Backend Developer','Frontend Developer','QA Engineer','Security/DevOps'],
        'reasons': ['Payment API integration','Validation & reconciliation','Security + encryption','Callback handling'],
        'tasks': ['Setup payment provider credentials','Implement payment API endpoints','UI payment flow','Add payment tests']
    },
    'auth': {
        'roles': ['Frontend Developer','Backend Developer','QA Engineer'],
        'reasons': ['Authentication flow','Token handling','Session management','Redirects'],
        'tasks': ['Create auth endpoints','Implement login UI','Token storage & refresh','Test auth flows']
    },
    'analytics': {
        'roles': ['Backend Developer','Data Engineer','Frontend Developer','QA Engineer'],
        'reasons': ['Data aggregation','Filters and exports','Charting library','Performance optimization'],
        'tasks': ['Create analytics API','Design DB aggregates','Implement frontend charts','Add analytics tests']
    },
    'default': {
        'roles': ['Frontend Developer','Backend Developer','QA Engineer'],
        'reasons': ['Feature implementation','Integration points','Testing'],
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
    if any(k in s_low for k in ['upi','payment','checkout','card','stripe','razorpay','paytm']):
        return 'payment'
    if any(k in s_low for k in ['login','signin','sign in','oauth','google','auth','password','otp','2fa','two-factor']):
        return 'auth'
    if any(k in s_low for k in ['analytics','dashboard','filters','export','report','chart','metrics']):
        return 'analytics'
    return 'default'

def round_to_fib(x: float) -> int:
    return int(min(FIB, key=lambda v: abs(v - x)))

def get_complexity(sp: int) -> str:
    if sp <= 3: return "Low"
    if sp <= 8: return "Medium"
    return "High"

def sprint_classification(sp: int, team_velocity: int) -> str:
    if sp <= team_velocity:
        return f"Fits in current sprint (velocity={team_velocity} SP)"
    if sp <= team_velocity * 1.5:
        return "Recommend next sprint or split tasks"
    return "Split across 2 or more sprints"

def predict_and_explain(text: str, team_velocity: int = 20):
    vec = vectorizer.transform([text])
    raw_pred = float(model.predict(vec)[0])
    rounded_sp = round_to_fib(raw_pred)
    complexity = get_complexity(rounded_sp)
    cat = keyword_category(text)
    rules = ROLE_RULES.get(cat, ROLE_RULES['default'])
    return {
        "predicted_raw": raw_pred,
        "story_points": rounded_sp,
        "complexity": complexity,
        "reasons": rules['reasons'],
        "roles": rules['roles'],
        "role_inner_steps": ROLE_INNER_STEPS,
        "recommended_tasks": rules['tasks'],
        "sprint_suggestion": sprint_classification(rounded_sp, team_velocity),
        "category": cat
    }

def finalize_by_team_votes(ai_sp: int, team_votes: dict):
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
    team_rounded = round_to_fib(avg_vote)
    if abs(team_rounded - ai_sp) <= 2:
        final = ai_sp
        rationale = "AI estimate accepted (team consensus within ±2)."
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

def make_downloadable_report(story_text, out, final=None):
    rows = [
        ["Input Story", story_text],
        ["Predicted Raw", out['predicted_raw']],
        ["Rounded SP", out['story_points']],
        ["Complexity", out['complexity']],
        ["Category", out['category']],
        ["Sprint Suggestion", out['sprint_suggestion']],
        ["Reasons", "; ".join(out['reasons'])],
        ["Recommended Tasks", "; ".join(out['recommended_tasks'])]
    ]
    if final:
        rows.append(["Final Committed SP", final['final_story_points']])
        rows.append(["Final Rationale", final['rationale']])
    df = pd.DataFrame(rows, columns=["Field","Value"])
    return df.to_csv(index=False).encode('utf-8')

# ---------- SESSION STATE ----------
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "votes" not in st.session_state:
    st.session_state.votes = ""

# ---------- UI ----------
st.markdown("<h1 style='color:#E6EEF3'>📈 Story Scale</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#9FA6B2'>AI Effort Estimator — beautiful cards + clear reasons</p>", unsafe_allow_html=True)

story = st.text_area("Paste user story (Agile style)", height=140,
                     placeholder="As a user, I want to login using Google OAuth so I can sign in faster")
team_velocity = st.number_input("Team velocity (Story Points)", min_value=5, max_value=200, value=20)

if st.button("Estimate Effort 🚀"):
    if story.strip():
        st.session_state.cache = predict_and_explain(story, team_velocity)
    else:
        st.warning("Please enter a story first.")

if st.session_state.cache:
    out = st.session_state.cache
    # top cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><div class='card-title'>🎯 Estimated Effort</div><div class='big-metric'>{out['story_points']}</div><div class='small'>Raw: {out['predicted_raw']:.3f}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='card-title'>🧩 Complexity</div><b>{out['complexity']}</b></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='card-title'>🚦 Sprint Suggestion</div><b>{out['sprint_suggestion']}</b></div>", unsafe_allow_html=True)

    # reasons and tasks
    st.markdown("<div class='card'><div class='card-title'>⚙️ Reasons</div>", unsafe_allow_html=True)
    for r in out['reasons']: st.markdown(f"- {r}")
    st.markdown("<hr><div class='card-title'>📝 Recommended Tasks</div>", unsafe_allow_html=True)
    for i,t in enumerate(out['recommended_tasks'],1): st.markdown(f"{i}. {t}")
    st.markdown("</div>", unsafe_allow_html=True)

    # roles and inner steps
    st.markdown("<div class='card'><div class='card-title'>👥 Roles & Inner Steps</div>", unsafe_allow_html=True)
    for role in out['roles']:
        st.markdown(f"**{role}**")
        for s in out['role_inner_steps'].get(role, []): st.markdown(f"- {s}")
        st.markdown("")
    st.markdown("</div>", unsafe_allow_html=True)

    # team voting
    st.markdown("<div class='card'><div class='card-title'>🧮 Team Voting (Planning Poker)</div>", unsafe_allow_html=True)
    votes_raw = st.text_input("Team votes (e.g. FE:8,BE:13,QA:5)", value=st.session_state.votes)
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
        st.success(f"✅ Final Effort: {final['final_story_points']} SP")
        st.caption(final['rationale'])
        csv = make_downloadable_report(story, out, final)
        st.download_button("📥 Download Report (CSV)", csv, file_name="story_estimate_report.csv", mime="text/csv")

# footer
st.markdown("<br><br><center style='color:#9FA6B2'>Made with 💛 by Story Scale — Story Scale AI</center>", unsafe_allow_html=True)
