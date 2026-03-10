import streamlit as st
from controller.adaptive_controller import AdaptiveController
from view.home_view import render_home
from view.quiz_view import render_quiz
from view.results_view import render_results

st.set_page_config(
    page_title = "ImtiQan — Adaptive Quiz Generator",
    page_icon  = "🎓",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# Global CSS 
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
  }

  #MainMenu, footer, header { visibility: hidden; }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-right: 1px solid rgba(99,102,241,0.3);
  }
  section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

  /* ── Metrics ── */
  [data-testid="stMetric"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 14px 18px;
    backdrop-filter: blur(8px);
    transition: transform .2s;
  }
  [data-testid="stMetric"]:hover { transform: translateY(-2px); }
  [data-testid="stMetricLabel"] { color: #a5b4fc !important; font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }
  [data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 1.6rem; font-weight: 700; }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: .65rem 1.5rem;
    font-weight: 600;
    font-size: .95rem;
    letter-spacing: .03em;
    transition: all .25s ease;
    box-shadow: 0 4px 15px rgba(99,102,241,0.4);
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99,102,241,0.55);
  }
  .stButton > button:active  { transform: translateY(0); }
  .stButton > button:disabled {
    background: rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.3) !important;
    box-shadow: none; transform: none;
  }

  /* ── Inputs ── */
  .stTextInput > div > div > input,
  .stTextArea  > div > div > textarea,
  .stSelectbox > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea  > div > div > textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
  }
  .stTextInput label, .stTextArea label,
  .stSelectbox label, .stRadio label,
  .stSlider label, .stMultiSelect label { color: #cbd5e1 !important; font-weight: 500; }

  /* ── Radio ── */
  .stRadio > div { gap: 10px; }
  .stRadio > div > label {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 10px;
    padding: 10px 18px;
    cursor: pointer;
    transition: all .2s;
    color: #e2e8f0 !important;
  }
  .stRadio > div > label:hover {
    background: rgba(99,102,241,0.15);
    border-color: #6366f1;
  }

  /* ── Progress bar ── */
  .stProgress > div > div > div > div {
    background: linear-gradient(90deg, #6366f1, #a78bfa, #ec4899);
    border-radius: 99px;
  }
  .stProgress > div > div { background: rgba(255,255,255,0.1); border-radius: 99px; }

  /* ── Expander ── */
  .streamlit-expanderHeader {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 500;
  }
  .streamlit-expanderContent {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
  }

  /* ── Divider / Alerts / Slider ── */
  hr { border-color: rgba(99,102,241,0.2) !important; }
  .stAlert { border-radius: 10px !important; border-left-width: 4px !important; }
  .stSlider > div > div > div > div { background: #6366f1 !important; }

  /* ── Custom cards ── */
  .imtiqan-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(12px);
    margin-bottom: 16px;
    transition: transform .2s, box-shadow .2s;
  }
  .imtiqan-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(99,102,241,0.2); }

  /* ── Hero ── */
  .hero-banner {
    background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.15) 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }
  .hero-banner::before {
    content:'';position:absolute;top:-50%;left:-50%;
    width:200%;height:200%;
    background:radial-gradient(circle,rgba(99,102,241,0.08) 0%,transparent 60%);
    animation:pulse 4s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.05);opacity:.7} }

  .hero-title {
    font-size: 3rem; font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a78bfa, #ec4899);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0; line-height: 1.2;
  }
  .hero-sub { color: #94a3b8; font-size: 1.1rem; margin-top: 10px; }

  /* ── Step badge ── */
  .step-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; padding: 6px 16px; border-radius: 99px;
    font-size: .8rem; font-weight: 700;
    letter-spacing: .08em; text-transform: uppercase; margin-bottom: 12px;
  }

  /* ── Question card ── */
  .question-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.08));
    border: 1px solid rgba(99,102,241,0.4);
    border-radius: 18px; padding: 30px; margin-bottom: 24px;
  }
  .question-text { font-size: 1.25rem; font-weight: 600; color: #f1f5f9; line-height: 1.6; }
  .q-number {
    font-size: .85rem; font-weight: 700; color: #a78bfa;
    text-transform: uppercase; letter-spacing: .1em; margin-bottom: 8px;
  }

  /* ── Feedback boxes ── */
  .feedback-correct {
    background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(52,211,153,0.1));
    border: 1px solid rgba(16,185,129,0.5);
    border-radius: 14px; padding: 20px 24px; margin-top: 16px;
    animation: slideIn .3s ease;
  }
  .feedback-wrong {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(248,113,113,0.1));
    border: 1px solid rgba(239,68,68,0.5);
    border-radius: 14px; padding: 20px 24px; margin-top: 16px;
    animation: slideIn .3s ease;
  }
  @keyframes slideIn { from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:translateY(0)} }

  /* ── Score display ── */
  .score-display {
    text-align: center; padding: 32px;
    background: rgba(255,255,255,0.04);
    border-radius: 20px; border: 1px solid rgba(99,102,241,0.2);
  }
  .score-pct {
    font-size: 4rem; font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a78bfa, #ec4899);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1;
  }

  /* ── Topic chip ── */
  .topic-chip {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.4);
    color: #a5b4fc; padding: 4px 12px;
    border-radius: 99px; font-size: .8rem;
    font-weight: 600; margin: 3px;
    transition: all .2s;
  }

  /* ── Sidebar ── */
  .sidebar-logo {
    font-size: 1.6rem; font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; text-align: center; padding: 8px 0 4px;
  }
  .sidebar-tagline {
    text-align: center; color: #64748b !important;
    font-size: .78rem; letter-spacing: .05em;
    text-transform: uppercase; margin-bottom: 16px;
  }

  /* ── Multiselect ── */
  .stMultiSelect span[data-baseweb="tag"] {
    background: rgba(99,102,241,0.4) !important;
    border-radius: 6px !important;
  }

  /* ── Chat bubbles (Teacher) ── */
  .stChatMessage { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# Session state defaults  
_defaults = {
    "current_page":           "home",
    "document_loaded":        False,
    "current_quiz":           None,
    "last_recommendation":    None,
    "recommended_difficulty": "medium",
    "adaptive_controller":    None,       # lazy-init below
    "extracted_topics":       [],
    "feedback_state":         None,
    "answered_questions":     [],
    "teacher_chat_history":   [],
    "chunk_count":            0,
    "raw_text_preview":       "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# lazy-init AdaptiveController so it only builds once per session
if st.session_state["adaptive_controller"] is None:
    st.session_state["adaptive_controller"] = AdaptiveController()

ac = st.session_state["adaptive_controller"]

# Sidebar 
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🎓 ImtiQan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-tagline">Adaptive AI Quiz Engine</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    perf = ac.performance.summary()
    st.markdown("**📊 Your Performance**")
    st.metric("Overall Accuracy",   f"{perf['overall_accuracy']}%")
    st.metric("Questions Answered", perf["total_answered"])
    st.metric("Current Difficulty", perf["current_difficulty"].capitalize())
    st.metric("Sessions Completed", perf["sessions_completed"])

    if perf.get("weak_topics"):
        st.markdown("---")
        st.warning("⚠️ **Weak Topics**")
        for t in perf["weak_topics"]:
            st.markdown(f"&nbsp;&nbsp;• {t}")

    if perf.get("strong_topics"):
        st.markdown("---")
        st.success("💪 **Strong Topics**")
        for t in perf["strong_topics"]:
            st.markdown(f"&nbsp;&nbsp;• {t}")

    st.markdown("---")

    cur = st.session_state["current_page"]
    page_labels = {"home": "🏠 Home", "quiz": "📝 Quiz", "results": "📊 Results"}
    st.markdown(f"**Page:** {page_labels.get(cur, cur)}")

    if cur != "home":
        if st.button("🏠 Go to Home", use_container_width=True):
            st.session_state["current_page"]         = "home"
            st.session_state["feedback_state"]       = None
            st.session_state["teacher_chat_history"] = []
            st.rerun()

    # seen questions counter
    seen_count = len(ac.seen_questions)
    if seen_count:
        st.markdown("---")
        st.caption(f"🧠 {seen_count} questions memorised — won't repeat them.")

    st.markdown("---")
    st.caption("ImtiQan adapts to your performance automatically.")

# Page router 
page = st.session_state["current_page"]

if page == "home":
    render_home(ac)
elif page == "quiz":
    render_quiz(ac)
elif page == "results":
    render_results(ac)