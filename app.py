
import streamlit as st
import joblib
from statistics import mean
import pandas as pd
import io

# ---------- CONFIG ----------
st.set_page_config(page_title="Story Scale", page_icon="📈", layout="wide")

# ---------- LOAD MODEL ----------
# Make sure model.joblib and vectorizer.joblib are in repo root
model = joblib.load("model.joblib")
vectorizer = joblib.load("vectorizer.joblib")

# ---------- STYLE (cards + dark feel) ----------
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
      .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#111827; color:#C7F7D4; font-weight:700; }
      .small { font-size:13px; color:#B7C0CC; }
      .reason { margin-left:6px; color:#D8E6F0; }
    </style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
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

def make_downloadable_report(story_text, out, final=None):
    rows = []
    rows.append(["Input Story", story_text])
    rows.append(["Predicted Raw", out['predicted_raw']])
    rows.append(["Rounded SP", out['story_points']])
    rows.append(["Complexity", out['complexity']])
    rows.append(["Category", out['category']])
    rows.append(["Sprint Suggestion", out['sprint_suggestion']])
    if final:
        rows.append(["Final Committed SP", final['final_story_points']])
        rows.append(["Final Rationale", final['rationale']])
    # reasons and tasks as joined
    rows.append(["Reasons", "; ".join(out['reasons'])])
    rows.append(["Recommended Tasks", "; ".join(out['recommended_tasks'])])
    df = pd.DataFrame(rows, columns=["field","value"])
    return df.to_csv(index=False).encode('utf-8')

# ---------- UI ----------
st.markdown("<div style='display:flex;align-items:center;gap:18px'>"
            "<h1 style='margin:0;color:#E6EEF3'>📈 Story Scale</h1>"
            "<div style='color:#9FA6B2;margin-top:4px'>AI Effort Estimator — beautiful cards + clear reasons</div>"
            "</div>", unsafe_allow_html=True)

st.write("")  # spacer

col1, col2 = st.columns([2,1])
final_result_cache = None

with col1:
    story = st.text_area("Paste user story (Agile style)", height=140,
                         placeholder="ex: As a user, I want to login using Google OAuth so I can sign in faster")
    team_velocity = st.number_input("Team velocity (story points)", min_value=5, max_value=200, value=20, step=1)
    if st.button("Estimate Effort 🚀"):
        if story.strip() == "":
            st.warning("Please enter a user story.")
        else:
            out = predict_and_explain(story, team_velocity=team_velocity)

            # Top cards row
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-title'>🎯 Estimated Effort</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='big-metric'>{out['story_points']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='subtle'>Rounded to nearest Fibonacci</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-title'>🧩 Complexity</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:20px;font-weight:700'>{out['complexity']}</div>", unsafe_allow_html=True)
                st.markdown("<div class='small'>Quick risk & effort indicator</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-title'>🚦 Sprint Suggestion</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-weight:700'>{out['sprint_suggestion']}</div>", unsafe_allow_html=True)
                st.markdown("<div class='small'>Use team velocity to decide</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Reasons + Tasks (wide)
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>⚙️ Reasons for this estimate</div>", unsafe_allow_html=True)
            for r in out['reasons']:
                st.markdown(f"- <span class='reason'> {r}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='opacity:0.06'/>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>📝 Recommended Backlog Tasks</div>", unsafe_allow_html=True)
            for i,t in enumerate(out['recommended_tasks'], start=1):
                st.markdown(f"{i}. {t}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Roles & inner steps
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>👥 Roles & Inner Steps</div>", unsafe_allow_html=True)
            for role in out['roles']:
                st.markdown(f"**{role}**")
                steps = out['role_inner_steps'].get(role, [])
                for s in steps:
                    st.markdown(f"- {s}")
                st.markdown("")  # gap
            st.markdown("</div>", unsafe_allow_html=True)

            # Team votes input
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>🧮 Team Voting (Planning Poker)</div>", unsafe_allow_html=True)
            st.markdown("<div class='small'>Enter votes as comma-separated Role:points (e.g. FE:8,BE:13,QA:5)</div>", unsafe_allow_html=True)
            votes_raw = st.text_input("Team votes (optional)", key="votes_input")
            finalize = st.button("Finalize by Scrum Master 🔨")
            st.markdown("</div>", unsafe_allow_html=True)

            # Save out to variable for download
            final_result_cache = {"story": story, "out": out, "votes_raw": votes_raw}

            # Show raw model value under small caption
            st.caption(f"Raw model output: {out['predicted_raw']:.3f}")

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>💡 Quick Help</div>", unsafe_allow_html=True)
    st.markdown("- Paste clear user stories in Agile format.")
    st.markdown("- Include acceptance criteria in story to improve accuracy.")
    st.markdown("- Use Team Votes to get Scrum Master finalization.")
    st.markdown("</div>", unsafe_allow_html=True)

# finalize action and reporting (outside columns)
if 'finalize' in locals() and finalize:
    # parse votes and compute final decision
    votes = {}
    try:
        if final_result_cache and final_result_cache.get("votes_raw", "").strip():
            parts = [p.strip() for p in final_result_cache["votes_raw"].split(",") if p.strip()]
            for p in parts:
                if ":" not in p:
                    raise ValueError("Wrong votes format")
                k,v = p.split(":")
                votes[k.strip()] = int(v.strip())
        else:
            votes = {}
        ai_sp = final_result_cache["out"]["story_points"]
        final = finalize_by_team_votes(ai_sp, votes)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>🔒 Scrum Master Final Decision</div>", unsafe_allow_html=True)
        st.markdown(f"- AI suggestion: **{final['ai_suggestion']} SP**")
        if final['team_avg'] is not None:
            st.markdown(f"- Team average: **{final['team_avg']}** → rounded to **{final['team_rounded']} SP**")
        st.success(f"Final committed: **{final['final_story_points']} SP**")
        st.markdown(f"_Rationale:_ {final['rationale']}")
        st.markdown("</div>", unsafe_allow_html=True)
        # Downloadable CSV report
        csv = make_downloadable_report(final_result_cache["story"], final_result_cache["out"], final)
        st.download_button("📥 Download estimation report (CSV)", csv, file_name="story_estimate_report.csv", mime="text/csv")
    except Exception as e:
        st.error("Could not finalize — check votes format: FE:8,BE:13,QA:5")

# footer
st.markdown("<br><br><center style='color:#9FA6B2'>Made with 💛 by Story Scale — Story Scale AI</center>", unsafe_allow_html=True)
