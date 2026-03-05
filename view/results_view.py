import streamlit as st


def render_results(adaptive_controller):
    quiz = st.session_state.get("current_quiz")
    rec  = st.session_state.get("last_recommendation")

    if not quiz or not rec:
        st.markdown("""
        <div class="imtiqan-card" style="text-align:center;padding:48px;">
          <div style="font-size:3rem;">😕</div>
          <div style="color:#f1f5f9;font-size:1.2rem;font-weight:600;margin:12px 0;">
            No results to display
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Back to Home", use_container_width=True):
            st.session_state["current_page"] = "home"
            st.rerun()
        return

    summary = quiz.summary()
    pct     = summary["percentage"]
    score   = summary["score"]
    total   = summary["total"]

    # Confetti for perfect score  
    if pct == 100:
        st.balloons()

    # Hero result banner  
    if pct == 100:
        grade, grade_col, grade_emoji = "Perfect!", "#10b981", "🏆"
    elif pct >= 80:
        grade, grade_col, grade_emoji = "Excellent!", "#10b981", "🎉"
    elif pct >= 60:
        grade, grade_col, grade_emoji = "Good Job!", "#f59e0b", "👍"
    elif pct >= 40:
        grade, grade_col, grade_emoji = "Keep Going!", "#f59e0b", "💪"
    else:
        grade, grade_col, grade_emoji = "Keep Practicing!", "#ef4444", "📚"

    st.markdown(f"""
    <div class="hero-banner">
      <div style="font-size:3.5rem;">{grade_emoji}</div>
      <div class="hero-title" style="margin-top:8px;">{grade}</div>
      <div class="hero-sub">Quiz completed · {summary['topic'][:50]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Score + metrics 
    sc_col, m_col = st.columns([1, 2])

    with sc_col:
        st.markdown(f"""
        <div class="score-display">
          <div style="color:#94a3b8;font-size:.85rem;
                      text-transform:uppercase;letter-spacing:.08em;
                      margin-bottom:8px;">Final Score</div>
          <div class="score-pct">{pct}%</div>
          <div style="color:#cbd5e1;margin-top:8px;font-size:1rem;font-weight:600;">
            {score} / {total} correct
          </div>
          <div style="margin-top:16px;">
            <div style="background:rgba(255,255,255,0.1);
                        border-radius:99px;height:8px;overflow:hidden;">
              <div style="
                width:{pct}%;
                height:100%;
                background:linear-gradient(90deg,#6366f1,#a78bfa,#ec4899);
                border-radius:99px;
                transition:width 1s ease;">
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with m_col:
        m1, m2 = st.columns(2)
        m1.metric("Difficulty",   summary["difficulty"].capitalize())
        m2.metric("Accuracy",     f"{pct}%")
        m3, m4 = st.columns(2)
        m3.metric("Next Level",   rec["next_difficulty"].capitalize())
        m4.metric("Sessions",     rec["performance"]["sessions_completed"])

    st.markdown("---")

    #  ImtiQan recommendation 
    st.markdown(f"""
    <div class="imtiqan-card" style="
        border-color:rgba(251,191,36,0.4);
        background:linear-gradient(135deg,rgba(251,191,36,0.08),rgba(245,158,11,0.05));">
      <div style="color:#fbbf24;font-weight:700;font-size:1rem;margin-bottom:6px;">
        🤖 ImtiQan Recommends
      </div>
      <div style="color:#e2e8f0;line-height:1.7;">{rec['message']}</div>
    </div>
    """, unsafe_allow_html=True)

    #  Weak / strong topics  
    perf = rec["performance"]
    t_col1, t_col2 = st.columns(2)

    with t_col1:
        if perf.get("weak_topics"):
            st.markdown("""
            <div class="imtiqan-card" style="
                border-color:rgba(239,68,68,0.4);
                background:rgba(239,68,68,0.06);">
              <div style="color:#f87171;font-weight:700;margin-bottom:10px;">
                ⚠️ Topics to Improve
              </div>
            """, unsafe_allow_html=True)
            for t in perf["weak_topics"]:
                st.markdown(
                    f'<span class="topic-chip" style="border-color:rgba(239,68,68,0.4);'
                    f'color:#fca5a5;">📌 {t}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="imtiqan-card" style="
                border-color:rgba(16,185,129,0.4);
                background:rgba(16,185,129,0.06);text-align:center;">
              <div style="color:#34d399;font-weight:700;">✅ No Weak Topics!</div>
              <div style="color:#94a3b8;font-size:.88rem;margin-top:4px;">
                Great performance across all areas.
              </div>
            </div>
            """, unsafe_allow_html=True)

    with t_col2:
        if perf.get("strong_topics"):
            st.markdown("""
            <div class="imtiqan-card" style="
                border-color:rgba(16,185,129,0.4);
                background:rgba(16,185,129,0.06);">
              <div style="color:#34d399;font-weight:700;margin-bottom:10px;">
                💪 Strong Topics
              </div>
            """, unsafe_allow_html=True)
            for t in perf["strong_topics"]:
                st.markdown(
                    f'<span class="topic-chip" style="border-color:rgba(16,185,129,0.4);'
                    f'color:#6ee7b7;">⭐ {t}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Question-by-question review 
    st.markdown(
        '<div class="step-badge">📝 Question Review</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    for q in summary["questions"]:
        is_correct = q["is_correct"]
        icon       = "✅" if is_correct else "❌"
        bar_color  = "#10b981" if is_correct else "#ef4444"
        label      = f"{icon}  Q{q['question_id'] + 1}: {q['question'][:75]}{'…' if len(q['question'])>75 else ''}"

        with st.expander(label, expanded=False):
            # question text
            st.markdown(
                f'<div style="color:#f1f5f9;font-weight:600;'
                f'font-size:1rem;margin-bottom:14px;line-height:1.6;">'
                f'{q["question"]}</div>',
                unsafe_allow_html=True,
            )

            if q["question_type"] == "MCQ" and q.get("options"):
                for k, v in q["options"].items():
                    if k == q["answer"] and k == q["user_answer"]:
                        bg   = "rgba(16,185,129,0.15)"
                        bord = "rgba(16,185,129,0.5)"
                        badge = "✅ Correct · Your Answer"
                        tc    = "#34d399"
                    elif k == q["answer"]:
                        bg   = "rgba(16,185,129,0.08)"
                        bord = "rgba(16,185,129,0.4)"
                        badge = "✅ Correct Answer"
                        tc    = "#34d399"
                    elif k == q["user_answer"]:
                        bg   = "rgba(239,68,68,0.1)"
                        bord = "rgba(239,68,68,0.4)"
                        badge = "❌ Your Answer"
                        tc    = "#f87171"
                    else:
                        bg   = "rgba(255,255,255,0.03)"
                        bord = "rgba(255,255,255,0.08)"
                        badge = ""
                        tc    = "#94a3b8"

                    st.markdown(f"""
                    <div style="
                      background:{bg};border:1px solid {bord};
                      border-radius:10px;padding:10px 16px;
                      margin-bottom:6px;display:flex;
                      justify-content:space-between;align-items:center;">
                      <span style="color:{tc};font-weight:500;">
                        {k})&nbsp; {v}
                      </span>
                      {"<span style='font-size:.78rem;color:"+tc+";font-weight:700;'>"+badge+"</span>" if badge else ""}
                    </div>
                    """, unsafe_allow_html=True)

            else:
                ua_col = "#34d399" if is_correct else "#f87171"
                st.markdown(f"""
                <div style="margin-bottom:8px;">
                  <span style="color:#94a3b8;font-size:.85rem;">Your answer:</span><br>
                  <span style="color:{ua_col};font-weight:500;font-size:.95rem;">
                    {q['user_answer'] or '—'}
                  </span>
                </div>
                <div>
                  <span style="color:#94a3b8;font-size:.85rem;">Correct answer:</span><br>
                  <span style="color:#34d399;font-weight:500;font-size:.95rem;">
                    {q['answer']}
                  </span>
                </div>
                """, unsafe_allow_html=True)

            if q.get("explanation"):
                st.markdown(f"""
                <div style="
                  background:rgba(99,102,241,0.08);
                  border:1px solid rgba(99,102,241,0.25);
                  border-radius:10px;
                  padding:12px 16px;
                  margin-top:12px;
                  color:#a5b4fc;
                  font-size:.88rem;
                  line-height:1.65;">
                  📖 <strong>Explanation:</strong><br>{q['explanation']}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Action buttons  
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("🔄 Next Adaptive Quiz", use_container_width=True, key="next_adaptive"):
            with st.spinner("✨ Generating next adaptive quiz…"):
                next_quiz = adaptive_controller.next_quiz()
            st.session_state["current_quiz"]       = next_quiz
            st.session_state["feedback_state"]     = None
            st.session_state["answered_questions"] = []
            st.session_state["current_page"]       = "quiz"
            st.rerun()

    with b2:
        if st.button("⚙️ New Quiz Settings", use_container_width=True, key="new_settings"):
            st.session_state["recommended_difficulty"] = rec["next_difficulty"]
            st.session_state["feedback_state"]         = None
            st.session_state["answered_questions"]     = []
            st.session_state["current_page"]           = "home"
            st.rerun()

    with b3:
        if st.button("🏠 Back to Home", use_container_width=True, key="back_home_results"):
            st.session_state["feedback_state"]     = None
            st.session_state["answered_questions"] = []
            st.session_state["current_page"]       = "home"
            st.rerun()