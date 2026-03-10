import streamlit as st


def render_results(adaptive_controller):
    quiz = st.session_state.get("current_quiz")
    rec  = st.session_state.get("last_recommendation")

    if not quiz or not rec:
        st.markdown(
            '<div class="imtiqan-card" style="text-align:center;padding:48px;">'
            '<div style="font-size:3rem;">😕</div>'
            '<div style="color:#f1f5f9;font-size:1.2rem;font-weight:600;margin:12px 0;">'
            'No results to display</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("← Back to Home", use_container_width=True):
            st.session_state["current_page"] = "home"
            st.rerun()
        return

    summary = quiz.summary()
    pct     = summary["percentage"]
    score   = summary["score"]
    total   = summary["total"]

    if pct == 100:
        st.balloons()

    # Hero banner  
    if pct == 100:
        grade, gcol, gemoji = "Perfect!",         "#10b981", "🏆"
    elif pct >= 80:
        grade, gcol, gemoji = "Excellent!",       "#10b981", "🎉"
    elif pct >= 60:
        grade, gcol, gemoji = "Good Job!",        "#f59e0b", "👍"
    elif pct >= 40:
        grade, gcol, gemoji = "Keep Going!",      "#f59e0b", "💪"
    else:
        grade, gcol, gemoji = "Keep Practicing!", "#ef4444", "📚"

    st.markdown(
        f'<div class="hero-banner">'
        f'<div style="font-size:3.5rem;">{gemoji}</div>'
        f'<div class="hero-title" style="margin-top:8px;">{grade}</div>'
        f'<div class="hero-sub">Quiz completed · {summary["topic"][:50]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Score + metrics 
    sc_col, m_col = st.columns([1, 2])

    with sc_col:
        st.markdown(
            f'<div class="score-display">'
            f'<div style="color:#94a3b8;font-size:.8rem;text-transform:uppercase;'
            f'letter-spacing:.08em;margin-bottom:8px;">Final Score</div>'
            f'<div class="score-pct">{pct}%</div>'
            f'<div style="color:#cbd5e1;margin-top:8px;font-size:1rem;font-weight:600;">'
            f'{score} / {total} correct</div>'
            f'<div style="margin-top:16px;">'
            f'<div style="background:rgba(255,255,255,0.1);border-radius:99px;'
            f'height:8px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;'
            f'background:linear-gradient(90deg,#6366f1,#a78bfa,#ec4899);'
            f'border-radius:99px;"></div></div></div></div>',
            unsafe_allow_html=True,
        )

    with m_col:
        r1c1, r1c2 = st.columns(2)
        r1c1.metric("Difficulty",   summary["difficulty"].capitalize())
        r1c2.metric("Accuracy",     f"{pct}%")
        r2c1, r2c2 = st.columns(2)
        r2c1.metric("Next Level",   rec["next_difficulty"].capitalize())
        r2c2.metric("Sessions",     rec["performance"]["sessions_completed"])

        # type breakdown if mixed
        breakdown = summary.get("type_breakdown", {})
        if len(breakdown) > 1:
            st.markdown(
                '<div style="margin-top:12px;color:#94a3b8;font-size:.8rem;'
                'font-weight:600;text-transform:uppercase;letter-spacing:.05em;">'
                'By Type</div>',
                unsafe_allow_html=True,
            )
            bd_cols = st.columns(len(breakdown))
            type_labels = {
                "MCQ": "MCQ", "true_false": "T / F", "short_answer": "Short Ans."
            }
            for col, (qtype, data) in zip(bd_cols, breakdown.items()):
                pct_t = round(data["correct"] / data["total"] * 100) if data["total"] else 0
                col.metric(
                    type_labels.get(qtype, qtype),
                    f'{data["correct"]}/{data["total"]}',
                    f'{pct_t}%',
                )

    st.markdown("---")

    # Recommendation  
    st.markdown(
        f'<div class="imtiqan-card" style="border-color:rgba(251,191,36,0.4);'
        f'background:linear-gradient(135deg,rgba(251,191,36,0.08),'
        f'rgba(245,158,11,0.05));">'
        f'<div style="color:#fbbf24;font-weight:700;font-size:1rem;margin-bottom:6px;">'
        f'🤖 ImtiQan Recommends</div>'
        f'<div style="color:#e2e8f0;line-height:1.7;">{rec["message"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Weak / strong topics  
    perf = rec["performance"]
    t1, t2 = st.columns(2)

    with t1:
        if perf.get("weak_topics"):
            st.markdown(
                '<div class="imtiqan-card" style="border-color:rgba(239,68,68,0.4);'
                'background:rgba(239,68,68,0.06);">'
                '<div style="color:#f87171;font-weight:700;margin-bottom:10px;">'
                '⚠️ Topics to Improve</div>',
                unsafe_allow_html=True,
            )
            for t in perf["weak_topics"]:
                st.markdown(
                    f'<span class="topic-chip" style="border-color:rgba(239,68,68,0.4);'
                    f'color:#fca5a5;">📌 {t}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="imtiqan-card" style="border-color:rgba(16,185,129,0.4);'
                'background:rgba(16,185,129,0.06);text-align:center;">'
                '<div style="color:#34d399;font-weight:700;">✅ No Weak Topics!</div>'
                '<div style="color:#94a3b8;font-size:.88rem;margin-top:4px;">'
                'Great performance across all areas.</div></div>',
                unsafe_allow_html=True,
            )

    with t2:
        if perf.get("strong_topics"):
            st.markdown(
                '<div class="imtiqan-card" style="border-color:rgba(16,185,129,0.4);'
                'background:rgba(16,185,129,0.06);">'
                '<div style="color:#34d399;font-weight:700;margin-bottom:10px;">'
                '💪 Strong Topics</div>',
                unsafe_allow_html=True,
            )
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
        label      = (
            f"{icon}  Q{q['question_id']+1}: "
            f"{q['question'][:70]}{'…' if len(q['question'])>70 else ''}"
        )

        with st.expander(label, expanded=False):
            st.markdown(
                f'<div style="color:#f1f5f9;font-weight:600;font-size:1rem;'
                f'line-height:1.6;margin-bottom:14px;">{q["question"]}</div>',
                unsafe_allow_html=True,
            )

            # MCQ options display
            if q["question_type"] == "MCQ" and q.get("options"):
                for k, v in q["options"].items():
                    is_ans  = k == q["answer"]
                    is_user = k == q["user_answer"]

                    if is_ans and is_user:
                        bg, bord, tc, badge = (
                            "rgba(16,185,129,0.15)", "rgba(16,185,129,0.5)",
                            "#34d399", "✅ Correct · Your Answer"
                        )
                    elif is_ans:
                        bg, bord, tc, badge = (
                            "rgba(16,185,129,0.08)", "rgba(16,185,129,0.4)",
                            "#34d399", "✅ Correct Answer"
                        )
                    elif is_user:
                        bg, bord, tc, badge = (
                            "rgba(239,68,68,0.1)", "rgba(239,68,68,0.4)",
                            "#f87171", "❌ Your Answer"
                        )
                    else:
                        bg, bord, tc, badge = (
                            "rgba(255,255,255,0.03)", "rgba(255,255,255,0.08)",
                            "#94a3b8", ""
                        )

                    badge_html = (
                        f'<span style="font-size:.75rem;color:{tc};font-weight:700;">'
                        f'{badge}</span>'
                        if badge else ""
                    )
                    st.markdown(
                        f'<div style="background:{bg};border:1px solid {bord};'
                        f'border-radius:10px;padding:10px 16px;margin-bottom:6px;'
                        f'display:flex;justify-content:space-between;align-items:center;">'
                        f'<span style="color:{tc};font-weight:500;">{k})&nbsp;{v}</span>'
                        f'{badge_html}</div>',
                        unsafe_allow_html=True,
                    )

            # True/False and Short Answer display
            else:
                ua_col = "#34d399" if is_correct else "#f87171"
                st.markdown(
                    f'<div style="margin-bottom:10px;">'
                    f'<span style="color:#94a3b8;font-size:.85rem;">Your answer:</span><br>'
                    f'<span style="color:{ua_col};font-weight:500;">'
                    f'{q["user_answer"] or "—"}</span></div>'
                    f'<div><span style="color:#94a3b8;font-size:.85rem;">'
                    f'Correct answer:</span><br>'
                    f'<span style="color:#34d399;font-weight:500;">{q["answer"]}</span></div>',
                    unsafe_allow_html=True,
                )

            # Explanation — always shown
            explanation = q.get("explanation", "")
            if explanation:
                st.markdown(
                    f'<div style="background:rgba(99,102,241,0.08);'
                    f'border:1px solid rgba(99,102,241,0.25);border-radius:10px;'
                    f'padding:12px 16px;margin-top:12px;color:#a5b4fc;'
                    f'font-size:.88rem;line-height:1.65;">'
                    f'📖 <strong>Explanation:</strong><br>{explanation}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Action buttons 
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button(
            "🔄 Next Adaptive Quiz",
            use_container_width = True,
            key = "next_adaptive",
        ):
            with st.spinner("✨ Generating adaptive quiz…"):
                next_quiz = adaptive_controller.next_quiz()
            st.session_state["current_quiz"]           = next_quiz
            st.session_state["feedback_state"]         = None
            st.session_state["answered_questions"]     = []
            st.session_state["teacher_chat_history"]   = []
            st.session_state["current_page"]           = "quiz"
            st.rerun()

    with b2:
        if st.button(
            "⚙️ New Quiz Settings",
            use_container_width = True,
            key = "new_settings",
        ):
            st.session_state["recommended_difficulty"] = rec["next_difficulty"]
            st.session_state["feedback_state"]         = None
            st.session_state["answered_questions"]     = []
            st.session_state["teacher_chat_history"]   = []
            st.session_state["current_page"]           = "home"
            st.rerun()

    with b3:
        if st.button(
            "🏠 Back to Home",
            use_container_width = True,
            key = "back_home",
        ):
            st.session_state["feedback_state"]       = None
            st.session_state["answered_questions"]   = []
            st.session_state["teacher_chat_history"] = []
            st.session_state["current_page"]         = "home"
            st.rerun()