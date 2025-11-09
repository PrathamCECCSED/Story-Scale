
import streamlit as st
import joblib

# ---------- CONFIG ----------
st.set_page_config(page_title="Story Scale", page_icon="📈", layout="wide")

# ---------- LOAD MODEL ----------
artifact = joblib.load("storypoint_artifact.joblib")
model = artifact["model"]
vectorizer = artifact["vectorizer"]
  # <-- same file in your repo

# ---------- CSS THEME (DARK) ----------
st.markdown("""
    <style>
        body { background-color: #0E1117; }
        .main { background-color: #0E1117; }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .title {
            font-size:42px;
            font-weight:800;
            color:white;
            padding-bottom:10px;
        }
        .sub {
            font-size:18px;
            color:#9FA6B2;
            padding-bottom:20px;
        }
        .card {
            background-color:#161B22;
            padding:18px 22px;
            border-radius:16px;
            border:1px solid #262E38;
            margin-bottom:14px;
        }
        .metric {
            font-size:28px;
            font-weight:700;
            color:#4ADE80;
        }
        .metric-label {
            font-size:15px;
            color:#9FA6B2;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<div class='title'>📈 Story Scale</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>AI based User Story Effort Estimator for Agile Teams.</div>", unsafe_allow_html=True)

# ---------- INPUT ----------
story = st.text_area("User Story", placeholder="ex: As a user, I should be able to login via Google OAuth so I can sign in faster")

if st.button("Estimate Effort 🚀"):
    if story.strip()=="":
        st.warning("Please enter a story first.")
    else:
       vec = vectorizer.transform([story])
       pred = model.predict(vec)[0]


        # -------- Result Cards --------
        st.markdown("<div class='card'> <div class='metric'>"+ str(pred) +"</div><div class='metric-label'>Predicted Story Points</div></div>", unsafe_allow_html=True)

        with st.expander("Team Roles Required"):
            st.write("""
**Engineering**  
• Backend Engineer  
• Frontend Engineer  
• QA Engineer  
• DevOps Integration  

**Product**  
• Product Manager  
• UX Designer
""")

        with st.expander("Inner Role Steps"):
            st.write("""
**Backend**  
1) Model + DB schema  
2) API endpoint  
3) integration + Auth  

**Frontend**  
1) UI Component  
2) API connect  
3) Validation + Testing  

**QA**  
1) test plan  
2) automation  
3) regression  
""")

        with st.expander("Scrum Master Final Effort"):
            st.success(f"Consensus: **{pred} Story Points** (Planning Poker Finalized)")

# footer
st.markdown("<br><br><center style='color:#666'>Made with 💛 by Story Scale AI</center>", unsafe_allow_html=True)

