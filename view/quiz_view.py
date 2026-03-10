import streamlit as st
from services.teacher_service import TeacherService


def render_quiz(adaptive_controller):
    quiz = st.session_state.get("current_quiz")

    if not quiz:
        _no_quiz_screen()
        return

    if quiz.is_complete:
        _finish_quiz(adaptive_controller, quiz)
        return

    question = quiz.current_question()
    if question is None:
        _finish_quiz(adaptive_controller, quiz)
        return

    _ensure_teacher()

    progress = quiz.progress()
    answered = progress["answered"]
    total    = progress["total"]

    # Layout: quiz (left 65%) | teacher (right 35%)
    quiz_col, teacher_col = st.columns([13, 7], gap="large")

    with quiz_col:
        _render_header(quiz, progress)
        _render_progress_dots(progress)
        _render_question_card(question, answered, total)

        feedback = st.session_state.get("feedback_state")

        if feedback is not None:
            _render_feedback(feedback, question)
            _render_next_button(answered, total)
        else:
            _render_answer_input(quiz, question, answered)

        _render_history()

    with teacher_col:
        _render_teacher_panel(question, adaptive_controller)


# Sub-renderers

def _render_header(quiz, progress):
    left, mid, right = st.columns([2, 3, 2])
    answered = progress["answered"]
    total    = progress["total"]

    with left:
        type_badge = {
            "MCQ": "🔘 MCQ", "true_false": "✔️ T/F",
            "short_answer": "✍️ SA", "mixed": "🎲 Mixed",
        }.get(quiz.question_type, quiz.question_type)
        st.markdown(
            f'<div style="color:#a78bfa;font-weight:700;font-size:.9rem;">'
            f'🎓 ImtiQan &nbsp;·&nbsp; {type_badge}</div>'
            f'<div style="color:#94a3b8;font-size:.8rem;">'
            f'Topic: {quiz.topic[:35]}{"…" if len(quiz.topic)>35 else ""}</div>',
            unsafe_allow_html=True,
        )

    with mid:
        pct_done = answered / total if total > 0 else 0
        st.progress(pct_done)
        st.markdown(
            f'<div style="text-align:center;color:#94a3b8;font-size:.8rem;margin-top:4px;">'
            f'Question {answered + 1} of {total}</div>',
            unsafe_allow_html=True,
        )

    with right:
        diff_color = {"easy": "#10b981", "medium": "#f59e0b", "hard": "#ef4444"}
        dc = diff_color.get(quiz.difficulty, "#a78bfa")
        st.markdown(
            f'<div style="text-align:right;">'
            f'<span style="background:rgba(99,102,241,0.15);border:1px solid '
            f'rgba(99,102,241,0.3);border-radius:99px;padding:4px 14px;'
            f'color:#a5b4fc;font-size:.8rem;font-weight:600;">'
            f'🎯 {quiz.difficulty.capitalize()}</span><br>'
            f'<span style="color:{dc};font-size:.8rem;">✅ {progress["score"]} correct</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)


def _render_progress_dots(progress):
    results  = progress["results"]
    total    = progress["total"]
    answered = progress["answered"]
    dots     = ""

    for i in range(total):
        if i < answered:
            col = "#10b981" if results[i] else "#ef4444"
            shadow = ""
        elif i == answered:
            col    = "#6366f1"
            shadow = f"box-shadow:0 0 8px #6366f1;"
        else:
            col    = "rgba(255,255,255,0.15)"
            shadow = ""

        dots += (
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'border-radius:50%;background:{col};margin:0 4px;{shadow}"></span>'
        )

    st.markdown(
        f'<div style="text-align:center;margin-bottom:16px;">{dots}</div>',
        unsafe_allow_html=True,
    )


def _render_question_card(question, answered, total):
    q_type_icon = {
        "MCQ": "🔘", "true_false": "✔️", "short_answer": "✍️"
    }.get(question.question_type, "❓")

    st.markdown(
        f'<div class="question-card">'
        f'<div class="q-number">'
        f'{q_type_icon} Question {answered + 1} / {total}'
        f'</div>'
        f'<div class="question-text">{question.question}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_feedback(feedback: dict, question):
    """
    Inline feedback shown immediately after submitting.
    Always shows the explanation — not just on wrong answers.
    """
    if feedback["is_correct"]:
        st.markdown(
            f'<div class="feedback-correct">'
            f'<div style="color:#10b981;font-size:1.1rem;font-weight:700;">'
            f'🎉 Correct!</div>'
            f'<div style="background:rgba(16,185,129,0.08);border-radius:8px;'
            f'padding:10px 14px;margin-top:10px;color:#e2e8f0;font-size:.9rem;'
            f'line-height:1.6;">📖 {feedback["explanation"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="feedback-wrong">'
            f'<div style="color:#ef4444;font-size:1.1rem;font-weight:700;">'
            f'❌ Not quite</div>'
            f'<div style="color:#fca5a5;margin-top:6px;">'
            f'<strong>Correct answer:</strong> {feedback["answer"]}</div>'
            f'<div style="background:rgba(255,255,255,0.05);border-radius:8px;'
            f'padding:10px 14px;margin-top:10px;color:#e2e8f0;font-size:.9rem;'
            f'line-height:1.6;">📖 {feedback["explanation"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_next_button(answered: int, total: int):
    st.markdown("<br>", unsafe_allow_html=True)
    label = "📊 See Results" if answered + 1 >= total else "➡️ Next Question"

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button(label, use_container_width=True, key="next_q_btn"):
            st.session_state["feedback_state"] = None
            # reset teacher history for new question
            if "teacher_service" in st.session_state:
                st.session_state["teacher_service"].reset()
            st.rerun()
    with c2:
        if st.button("🚪 Quit", use_container_width=True, key="quit_after_feedback"):
            _quit_quiz()


def _render_answer_input(quiz, question, answered):
    """Render the correct input widget based on the current question's type."""

    if question.question_type == "MCQ":
        _render_mcq(quiz, question, answered)

    elif question.question_type == "true_false":
        _render_true_false(quiz, question, answered)

    elif question.question_type == "short_answer":
        _render_short_answer(quiz, question, answered)


def _render_mcq(quiz, question, answered):
    if not question.options:
        st.error("MCQ question has no options. Skipping.")
        return

    st.markdown(
        '<div style="color:#cbd5e1;font-weight:500;margin-bottom:8px;">'
        'Choose your answer:</div>',
        unsafe_allow_html=True,
    )
    selected = st.radio(
        "options",
        options  = list(question.options.keys()),
        format_func = lambda k: f"  {k})  {question.options[k]}",
        index    = None,
        key      = f"mcq_{question.question_id}_{question.fingerprint}",
        label_visibility = "collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button(
            "✅ Submit Answer",
            use_container_width = True,
            disabled = selected is None,
            key      = f"submit_mcq_{question.question_id}",
        ):
            _submit(quiz, question, selected, answered)
    with c2:
        if st.button("🚪 Quit", use_container_width=True, key="quit_mcq"):
            _quit_quiz()


def _render_true_false(quiz, question, answered):
    st.markdown(
        '<div style="color:#cbd5e1;font-weight:500;margin-bottom:12px;">'
        'Is this statement True or False?</div>',
        unsafe_allow_html=True,
    )

    # single row with True / False / Quit
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        if st.button(
            "✅  True", use_container_width=True,
            key=f"tf_true_{question.question_id}"
        ):
            _submit(quiz, question, "true", answered)
    with c2:
        if st.button(
            "❌  False", use_container_width=True,
            key=f"tf_false_{question.question_id}"
        ):
            _submit(quiz, question, "false", answered)
    with c3:
        if st.button("🚪 Quit", use_container_width=True, key="quit_tf"):
            _quit_quiz()


def _render_short_answer(quiz, question, answered):
    st.markdown(
        '<div style="color:#cbd5e1;font-weight:500;margin-bottom:8px;">'
        'Type your answer below:</div>',
        unsafe_allow_html=True,
    )
    user_answer = st.text_area(
        "answer",
        height      = 120,
        placeholder = "Write a clear, concise answer…",
        key         = f"sa_{question.question_id}_{question.fingerprint}",
        label_visibility = "collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        disabled = not (user_answer and user_answer.strip())
        if st.button(
            "✅ Submit Answer",
            use_container_width = True,
            disabled            = disabled,
            key                 = f"submit_sa_{question.question_id}",
        ):
            _submit(quiz, question, user_answer, answered)
    with c2:
        if st.button("🚪 Quit", use_container_width=True, key="quit_sa"):
            _quit_quiz()


def _render_history():
    history = st.session_state.get("answered_questions", [])
    if not history:
        return

    with st.expander(f"📖 Previous answers ({len(history)})", expanded=False):
        for item in reversed(history[-5:]):   # show last 5 most recent
            icon  = "✅" if item["is_correct"] else "❌"
            color = "#10b981" if item["is_correct"] else "#ef4444"
            st.markdown(
                f'<div style="border-left:3px solid {color};padding:8px 14px;'
                f'margin-bottom:6px;background:rgba(255,255,255,0.03);'
                f'border-radius:0 8px 8px 0;">'
                f'<div style="color:{color};font-weight:600;font-size:.85rem;">'
                f'{icon} Q{item["q_num"]}: {item["question"][:80]}'
                f'{"…" if len(item["question"])>80 else ""}</div>'
                f'<div style="color:#94a3b8;font-size:.78rem;margin-top:3px;">'
                f'Your: <em>{item["user_answer"]}</em>'
                f'{"" if item["is_correct"] else "  ·  Correct: <strong>{}</strong>".format(item["correct_answer"])}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _render_teacher_panel(question, adaptive_controller):
    """Right-side Teacher chat agent panel."""
    st.markdown(
        '<div style="background:rgba(99,102,241,0.08);border:1px solid '
        'rgba(99,102,241,0.3);border-radius:16px;padding:20px;">'
        '<div style="color:#a78bfa;font-weight:700;font-size:1rem;'
        'margin-bottom:4px;">🧑‍🏫 Teacher</div>'
        '<div style="color:#64748b;font-size:.78rem;margin-bottom:16px;">'
        'Ask me anything about this question</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    teacher: TeacherService = st.session_state["teacher_service"]
    chat_history = st.session_state.get("teacher_chat_history", [])

    # chat history display
    chat_container = st.container(height=320)
    with chat_container:
        if not chat_history:
            st.markdown(
                '<div style="text-align:center;color:#475569;font-size:.85rem;'
                'padding:40px 0;">💬 Ask the Teacher a question about<br>'
                'this topic to get a deeper explanation.</div>',
                unsafe_allow_html=True,
            )
        for msg in chat_history:
            role  = msg["role"]
            text  = msg["content"]
            if role == "user":
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-end;'
                    f'margin-bottom:8px;">'
                    f'<div style="background:rgba(99,102,241,0.3);'
                    f'border-radius:14px 14px 2px 14px;padding:10px 14px;'
                    f'max-width:85%;color:#e2e8f0;font-size:.88rem;">'
                    f'{text}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-start;'
                    f'margin-bottom:8px;">'
                    f'<div style="background:rgba(16,185,129,0.12);'
                    f'border:1px solid rgba(16,185,129,0.25);'
                    f'border-radius:14px 14px 14px 2px;padding:10px 14px;'
                    f'max-width:90%;color:#e2e8f0;font-size:.88rem;'
                    f'line-height:1.6;">'
                    f'🧑‍🏫 {text}</div></div>',
                    unsafe_allow_html=True,
                )

    # input row
    user_msg = st.text_input(
        "Ask Teacher",
        placeholder = "e.g. Can you explain this concept more?",
        key         = f"teacher_input_{question.question_id}_{question.fingerprint}",
        label_visibility = "collapsed",
    )

    ask_col, clear_col = st.columns([3, 1])

    with ask_col:
        if st.button(
            "📨 Ask",
            use_container_width = True,
            disabled            = not (user_msg and user_msg.strip()),
            key                 = f"teacher_ask_{question.question_id}",
        ):
            with st.spinner("Teacher is thinking…"):
                # get a small context snippet from RAG for grounding
                try:
                    snippet = adaptive_controller.quiz_controller.rag.retrieve_as_context(
                        question.question, top_k=1
                    )
                except Exception:
                    snippet = ""

                response = teacher.ask(
                    student_message = user_msg.strip(),
                    quiz_question   = question.question,
                    context_snippet = snippet,
                )

            chat_history.append({"role": "user",      "content": user_msg.strip()})
            chat_history.append({"role": "assistant",  "content": response})
            st.session_state["teacher_chat_history"] = chat_history
            st.rerun()

    with clear_col:
        if st.button(
            "🗑️",
            use_container_width = True,
            key                 = f"teacher_clear_{question.question_id}",
            help                = "Clear chat history",
        ):
            st.session_state["teacher_chat_history"] = []
            teacher.reset()
            st.rerun()


# Shared helpers

def _submit(quiz, question, user_answer: str, answered: int):
    """Evaluate answer, record history, set feedback state, rerun."""
    is_correct = quiz.submit_answer(user_answer)
    _record_history(question, user_answer, is_correct, answered + 1)
    st.session_state["feedback_state"] = {
        "is_correct":  is_correct,
        "answer":      question.answer,
        "explanation": question.explanation or "No explanation provided.",
    }
    st.rerun()


def _quit_quiz():
    st.session_state["current_page"]    = "home"
    st.session_state["feedback_state"]  = None
    st.session_state["teacher_chat_history"] = []
    st.rerun()


def _finish_quiz(adaptive_controller, quiz):
    recommendation = adaptive_controller.process_results(quiz)
    st.session_state["last_recommendation"]  = recommendation
    st.session_state["teacher_chat_history"] = []
    st.session_state["current_page"]         = "results"
    st.rerun()


def _no_quiz_screen():
    st.markdown(
        '<div class="imtiqan-card" style="text-align:center;padding:48px;">'
        '<div style="font-size:3rem;">😕</div>'
        '<div style="color:#f1f5f9;font-size:1.2rem;font-weight:600;margin:12px 0;">'
        'No active quiz found</div>'
        '<div style="color:#94a3b8;">Head back home to generate a new quiz.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("← Back to Home", use_container_width=True):
        st.session_state["current_page"] = "home"
        st.rerun()


def _ensure_teacher():
    """Initialise TeacherService and chat history if not already in session."""
    if "teacher_service" not in st.session_state:
        st.session_state["teacher_service"]    = TeacherService()
        st.session_state["teacher_chat_history"] = []


def _record_history(question, user_answer: str, is_correct: bool, q_num: int):
    history = st.session_state.get("answered_questions", [])
    history.append({
        "q_num":          q_num,
        "question":       question.question,
        "question_type":  question.question_type,
        "user_answer":    user_answer,
        "correct_answer": question.answer,
        "is_correct":     is_correct,
        "explanation":    question.explanation or "",
        "options":        question.options,
    })
    st.session_state["answered_questions"] = history