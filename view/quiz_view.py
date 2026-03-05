import streamlit as st


def render_quiz(adaptive_controller):
    quiz = st.session_state.get("current_quiz")

    # No quiz guard  
    if not quiz:
        st.markdown("""
        <div class="imtiqan-card" style="text-align:center;padding:48px;">
          <div style="font-size:3rem;">😕</div>
          <div style="color:#f1f5f9;font-size:1.2rem;font-weight:600;margin:12px 0;">
            No active quiz found
          </div>
          <div style="color:#94a3b8;">Head back home to generate a new quiz.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Back to Home", use_container_width=True):
            st.session_state["current_page"] = "home"
            st.rerun()
        return

    # Check completion 
    if quiz.is_complete:
        recommendation = adaptive_controller.process_results(quiz)
        st.session_state["last_recommendation"] = recommendation
        st.session_state["current_page"]        = "results"
        st.rerun()
        return

    question = quiz.current_question()
    if question is None:
        recommendation = adaptive_controller.process_results(quiz)
        st.session_state["last_recommendation"] = recommendation
        st.session_state["current_page"]        = "results"
        st.rerun()
        return

    progress  = quiz.progress()
    answered  = progress["answered"]
    total     = progress["total"]
    pct_done  = answered / total if total > 0 else 0

    # Header
    left, mid, right = st.columns([2, 3, 2])
    with left:
        st.markdown(f"""
        <div style="color:#a78bfa;font-weight:700;font-size:.9rem;
                    text-transform:uppercase;letter-spacing:.08em;">
          🎓 ImtiQan Quiz
        </div>
        <div style="color:#94a3b8;font-size:.8rem;">
          Topic: {quiz.topic[:35]}{"…" if len(quiz.topic)>35 else ""}
        </div>
        """, unsafe_allow_html=True)
    with mid:
        st.progress(pct_done)
        st.markdown(
            f'<div style="text-align:center;color:#94a3b8;font-size:.8rem;'
            f'margin-top:4px;">'
            f'Question {answered + 1} of {total}</div>',
            unsafe_allow_html=True,
        )
    with right:
        diff_color = {"easy": "#10b981", "medium": "#f59e0b", "hard": "#ef4444"}
        dc = diff_color.get(quiz.difficulty, "#a78bfa")
        st.markdown(f"""
        <div style="text-align:right;">
          <span style="background:rgba(99,102,241,0.15);
                       border:1px solid rgba(99,102,241,0.3);
                       border-radius:99px;padding:4px 14px;
                       color:#a5b4fc;font-size:.8rem;font-weight:600;">
            🎯 {quiz.difficulty.capitalize()}
          </span><br>
          <span style="color:#94a3b8;font-size:.8rem;">
            ✅ {progress['score']} correct
          </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Answered question history (collapsible) 
    history = st.session_state.get("answered_questions", [])
    if history:
        with st.expander(
            f"📖 Review previous answers ({len(history)} answered)", expanded=False
        ):
            for item in history:
                icon  = "✅" if item["is_correct"] else "❌"
                color = "#10b981" if item["is_correct"] else "#ef4444"
                st.markdown(f"""
                <div style="
                  border-left:3px solid {color};
                  padding:10px 16px;
                  margin-bottom:8px;
                  background:rgba(255,255,255,0.03);
                  border-radius:0 8px 8px 0;">
                  <div style="color:{color};font-weight:600;font-size:.85rem;">
                    {icon} Q{item['q_num']}: {item['question'][:90]}
                    {"…" if len(item['question'])>90 else ""}
                  </div>
                  <div style="color:#94a3b8;font-size:.8rem;margin-top:4px;">
                    Your answer: <em>{item['user_answer']}</em>
                    {"" if item['is_correct']
                      else f" &nbsp;·&nbsp; Correct: <strong>{item['correct_answer']}</strong>"}
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # Question card  
    st.markdown(f"""
    <div class="question-card">
      <div class="q-number">Question {answered + 1} / {total}</div>
      <div class="question-text">{question.question}</div>
    </div>
    """, unsafe_allow_html=True)

    # Feedback state (shown BEFORE moving on) 
    feedback = st.session_state.get("feedback_state")

    if feedback is not None:
        # Show feedback and a "Next Question" button — do NOT auto-advance
        if feedback["is_correct"]:
            st.markdown("""
            <div class="feedback-correct">
              <div style="color:#10b981;font-size:1.2rem;font-weight:700;">
                🎉 Correct! Well done!
              </div>
              <div style="color:#6ee7b7;margin-top:6px;">
                Keep it up — you're on a roll!
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="feedback-wrong">
              <div style="color:#ef4444;font-size:1.2rem;font-weight:700;">
                ❌ Not quite right
              </div>
              <div style="color:#fca5a5;margin-top:8px;">
                <strong>Correct answer:</strong> {feedback['answer']}
              </div>
              <div style="
                background:rgba(255,255,255,0.05);
                border-radius:8px;
                padding:10px 14px;
                margin-top:10px;
                color:#e2e8f0;
                font-size:.9rem;
                line-height:1.6;">
                📖 {feedback['explanation']}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        btn_label = "➡️ Next Question" if answered < total else "📊 See Results"
        if st.button(btn_label, use_container_width=True, key="next_q_btn"):
            st.session_state["feedback_state"] = None
            st.rerun()
        return          # stop here; don't show answer input again

    # Answer input 
    user_answer = None

    if question.question_type == "MCQ" and question.options:
        st.markdown(
            '<div style="color:#cbd5e1;font-weight:500;margin-bottom:8px;">'
            'Choose your answer:</div>',
            unsafe_allow_html=True,
        )
        selected = st.radio(
            "Choose your answer:",
            options=list(question.options.keys()),
            format_func=lambda k: f"  {k})  {question.options[k]}",
            index=None,
            key=f"mcq_radio_{question.question_id}",
            label_visibility="collapsed",
        )
        user_answer = selected

    elif question.question_type == "true_false":
        st.markdown(
            '<div style="color:#cbd5e1;font-weight:500;margin-bottom:8px;">'
            'Is this statement True or False?</div>',
            unsafe_allow_html=True,
        )
        tf_col1, tf_col2 = st.columns(2)
        with tf_col1:
            true_btn  = st.button("✅  True",  use_container_width=True, key="tf_true")
        with tf_col2:
            false_btn = st.button("❌  False", use_container_width=True, key="tf_false")

        if true_btn:
            user_answer = "true"
        elif false_btn:
            user_answer = "false"

        # submit immediately when T/F button pressed
        if user_answer:
            is_correct = quiz.submit_answer(user_answer)
            # record history
            _record_history(question, user_answer, is_correct, answered + 1)
            st.session_state["feedback_state"] = {
                "is_correct":  is_correct,
                "answer":      question.answer,
                "explanation": question.explanation or "",
            }
            st.rerun()
        return  # wait for button click

    elif question.question_type == "short_answer":
        st.markdown(
            '<div style="color:#cbd5e1;font-weight:500;margin-bottom:8px;">'
            'Type your answer below:</div>',
            unsafe_allow_html=True,
        )
        user_answer = st.text_area(
            "Your answer:",
            height=130,
            placeholder="Write a clear, concise answer…",
            key=f"sa_input_{question.question_id}",
            label_visibility="collapsed",
        )

    # Submit button (MCQ & short answer)  
    if question.question_type != "true_false":
        st.markdown("<br>", unsafe_allow_html=True)

        submit_col, quit_col = st.columns([3, 1])
        with submit_col:
            submit_disabled = not user_answer or (
                isinstance(user_answer, str) and not user_answer.strip()
            )
            if st.button(
                "✅  Submit Answer",
                use_container_width=True,
                disabled=submit_disabled,
                key=f"submit_btn_{question.question_id}",
            ):
                is_correct = quiz.submit_answer(user_answer)
                _record_history(question, user_answer, is_correct, answered + 1)
                st.session_state["feedback_state"] = {
                    "is_correct":  is_correct,
                    "answer":      question.answer,
                    "explanation": question.explanation or "",
                }
                st.rerun()

        with quit_col:
            if st.button("🚪 Quit", use_container_width=True, key="quit_btn"):
                st.session_state["current_page"] = "home"
                st.session_state["feedback_state"] = None
                st.rerun()

    else:
        # quit button for T/F (already handled above but keep layout)
        if st.button("🚪 Quit Quiz", use_container_width=True, key="quit_tf"):
            st.session_state["current_page"] = "home"
            st.session_state["feedback_state"] = None
            st.rerun()

    # Mini progress dots  
    st.markdown("<br>", unsafe_allow_html=True)
    dots_html = ""
    for i in range(total):
        if i < answered:
            hist = st.session_state.get("answered_questions", [])
            correct = hist[i]["is_correct"] if i < len(hist) else False
            col = "#10b981" if correct else "#ef4444"
        elif i == answered:
            col = "#6366f1"
        else:
            col = "rgba(255,255,255,0.15)"
        dots_html += (
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'border-radius:50%;background:{col};margin:0 4px;'
            f'{"box-shadow:0 0 8px " + col + ";" if i==answered else ""}"></span>'
        )
    st.markdown(
        f'<div style="text-align:center;margin-top:8px;">{dots_html}</div>',
        unsafe_allow_html=True,
    )


# helper 
def _record_history(question, user_answer: str, is_correct: bool, q_num: int):
    history = st.session_state.get("answered_questions", [])
    history.append({
        "q_num":          q_num,
        "question":       question.question,
        "user_answer":    user_answer,
        "correct_answer": question.answer,
        "is_correct":     is_correct,
        "explanation":    question.explanation or "",
        "options":        question.options if hasattr(question, "options") else None,
        "question_type":  question.question_type,
    })
    st.session_state["answered_questions"] = history