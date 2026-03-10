import streamlit as st


def render_home(adaptive_controller):
    st.markdown(
        '<div class="hero-banner">'
        '<div class="hero-title">🎓 ImtiQan</div>'
        '<div class="hero-sub">'
        'AI-Powered Adaptive Quiz Generator &nbsp;·&nbsp; Learn smarter, not harder'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Step 1: Load material  
    st.markdown(
        '<div class="step-badge">📄 Step 1 — Load Study Material</div>',
        unsafe_allow_html=True,
    )

    tab_text, tab_pdf = st.tabs(["📋 Paste Text", "📁 Upload PDF"])

    with tab_text:
        text_input = st.text_area(
            "Paste your study material:",
            height      = 240,
            placeholder = (
                "Paste any content — lecture notes, articles, textbook chapters…\n\n"
                "(Minimum 100 characters)"
            ),
            key = "home_text_area",
        )
        c1, c2 = st.columns([1, 2])
        with c1:
            load_text_btn = st.button(
                "📥 Load Text", use_container_width=True, key="load_text_btn"
            )
        with c2:
            if text_input:
                chars  = len(text_input.strip())
                colour = "#10b981" if chars >= 100 else "#f59e0b"
                icon   = "✅" if chars >= 100 else "⚠️"
                st.markdown(
                    f'<p style="color:{colour};margin-top:10px;">'
                    f'{icon} {chars:,} characters</p>',
                    unsafe_allow_html=True,
                )

        if load_text_btn:
            if len(text_input.strip()) < 100:
                st.error("⚠️ Paste at least 100 characters of study material.")
            else:
                with st.spinner("🔍 Processing & indexing…"):
                    count = adaptive_controller.load_text(text_input)
                _set_document_loaded(count, text_input[:400])
                st.success(f"✅ Loaded — **{count} chunks** indexed!")
                st.rerun()

    with tab_pdf:
        uploaded = st.file_uploader(
            "Upload a PDF:", type=["pdf"], key="home_pdf_uploader"
        )
        if uploaded:
            st.markdown(
                f'<p style="color:#a78bfa;">📎 {uploaded.name} '
                f'({uploaded.size / 1024:.1f} KB)</p>',
                unsafe_allow_html=True,
            )

        load_pdf_btn = st.button(
            "📥 Load PDF",
            use_container_width = True,
            key                 = "load_pdf_btn",
            disabled            = uploaded is None,
        )

        if uploaded and load_pdf_btn:
            with st.spinner("📖 Reading & indexing PDF…"):
                import os
                os.makedirs("data", exist_ok=True)
                temp_path = f"data/temp_{uploaded.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded.read())

                count = adaptive_controller.load_pdf(temp_path)

                try:
                    import fitz
                    doc     = fitz.open(temp_path)
                    preview = " ".join(p.get_text() for p in doc)[:400]
                except Exception:
                    preview = ""

            _set_document_loaded(count, preview)
            st.success(f"✅ PDF loaded — **{count} chunks** indexed!")
            st.rerun()

    # Document ready  
    if st.session_state.get("document_loaded"):
        chunk_count = st.session_state.get("chunk_count", 0)
        st.markdown(
            f'<div class="imtiqan-card" style="border-color:rgba(16,185,129,0.4);'
            f'background:linear-gradient(135deg,rgba(16,185,129,0.08),'
            f'rgba(52,211,153,0.05));display:flex;align-items:center;gap:16px;">'
            f'<span style="font-size:2rem;">✅</span>'
            f'<div><div style="color:#34d399;font-weight:700;">Document Ready</div>'
            f'<div style="color:#94a3b8;font-size:.88rem;">'
            f'{chunk_count} chunks indexed · ready to generate questions'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Step 2: Configure quiz 
        st.markdown(
            '<div class="step-badge">⚙️ Step 2 — Configure Your Quiz</div>',
            unsafe_allow_html=True,
        )

        # Topic input — fully optional  
        st.markdown("**📌 Topic** *(optional)*")
        st.markdown(
            '<p style="color:#64748b;font-size:.83rem;margin-top:-8px;margin-bottom:12px;">'
            'Leave empty to generate a general quiz from the whole document, '
            'or type a specific topic you want to focus on.</p>',
            unsafe_allow_html=True,
        )

        custom_topic = st.text_input(
            "topic_input",
            placeholder      = "e.g. neural networks, photosynthesis, the French Revolution…",
            key              = "custom_topic_input",
            label_visibility = "collapsed",
        )

        # resolve final topic — empty → general
        final_topic = custom_topic.strip() if custom_topic.strip() else ""

        if final_topic:
            st.markdown(
                f'<p style="color:#a78bfa;font-size:.85rem;margin-top:4px;">'
                f'🎯 Focusing on: <strong>{final_topic}</strong></p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="color:#64748b;font-size:.85rem;margin-top:4px;">'
                '📄 No topic set — quiz will cover the document generally.</p>',
                unsafe_allow_html=True,
            )

        st.markdown(" ")

        # Settings 
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            question_type = st.selectbox(
                "❓ Question Type",
                options = ["MCQ", "true_false", "short_answer", "mixed"],
                format_func = lambda x: {
                    "MCQ":          "🔘 Multiple Choice",
                    "true_false":   "✔️  True / False",
                    "short_answer": "✍️  Short Answer",
                    "mixed":        "🎲 Mixed (all types)",
                }[x],
                key = "q_type_select",
            )

        with c2:
            rec_diff = st.session_state.get("recommended_difficulty", "medium")
            difficulty = st.selectbox(
                "🎯 Difficulty",
                options = ["easy", "medium", "hard"],
                index   = ["easy", "medium", "hard"].index(rec_diff),
                format_func = lambda x: {
                    "easy":   "🟢 Easy",
                    "medium": "🟡 Medium",
                    "hard":   "🔴 Hard",
                }[x],
                key = "difficulty_select",
            )

        with c3:
            num_questions = st.select_slider(
                "🔢 Questions",
                options = list(range(3, 21)),
                value   = 5,
                key     = "num_q_slider",
            )

        with c4:
            language = st.selectbox(
                "🌍 Language",
                options     = ["english", "arabic"],
                format_func = lambda x: "🇬🇧 English" if x == "english" else "🇸🇦 Arabic",
                key         = "language_select",
            )

        # mixed breakdown info
        if question_type == "mixed":
            mcq_n = num_questions // 3 + (1 if num_questions % 3 > 0 else 0)
            tf_n  = num_questions // 3 + (1 if num_questions % 3 > 1 else 0)
            sa_n  = num_questions // 3
            st.markdown(
                f'<div class="imtiqan-card" style="padding:14px 18px;'
                f'border-color:rgba(139,92,246,0.4);background:rgba(139,92,246,0.07);">'
                f'<div style="color:#a78bfa;font-weight:600;font-size:.88rem;">'
                f'🎲 Mixed breakdown: &nbsp;'
                f'<span style="color:#e2e8f0;">'
                f'{mcq_n} MCQ &nbsp;·&nbsp; {tf_n} T/F &nbsp;·&nbsp; {sa_n} Short Answer'
                f'</span></div></div>',
                unsafe_allow_html=True,
            )

        # recommendation banner
        if st.session_state.get("last_recommendation"):
            rec = st.session_state["last_recommendation"]
            st.markdown(
                f'<div class="imtiqan-card" style="border-color:rgba(251,191,36,0.4);'
                f'background:linear-gradient(135deg,rgba(251,191,36,0.08),'
                f'rgba(245,158,11,0.05));">'
                f'<span style="color:#fbbf24;font-weight:700;">💡 ImtiQan Recommends'
                f'</span><br>'
                f'<span style="color:#e2e8f0;">{rec["message"]}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Generate 
        type_label = {
            "MCQ": "MCQ", "true_false": "True/False",
            "short_answer": "Short Answer", "mixed": "Mixed",
        }.get(question_type, question_type)

        btn_label = (
            f"🚀 Generate {num_questions} {type_label} Questions"
            if final_topic
            else f"🚀 Generate {num_questions} {type_label} Questions (General)"
        )

        if st.button(btn_label, use_container_width=True, key="generate_quiz_btn"):
            # use general query if no topic given
            query = final_topic if final_topic else "general overview summary of the document"

            with st.spinner(
                f"✨ Generating {num_questions} {type_label} questions"
                f"{' about ' + final_topic if final_topic else ''}…"
            ):
                quiz = adaptive_controller.start_quiz(
                    topic         = query,
                    question_type = question_type,
                    num_questions = num_questions,
                    language      = language,
                    difficulty    = difficulty,
                )

            st.session_state["current_quiz"]         = quiz
            st.session_state["feedback_state"]       = None
            st.session_state["answered_questions"]   = []
            st.session_state["teacher_chat_history"] = []
            st.session_state["current_page"]         = "quiz"
            st.rerun()

    else:
        #  Feature cards  
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        features = [
            ("🤖", "Adaptive AI",
             "Difficulty adjusts automatically based on your live performance."),
            ("📚", "RAG-Powered",
             "Questions come from YOUR material — zero hallucinations."),
            ("🎲", "Mixed Quizzes",
             "MCQ, True/False, and Short Answer all in one session."),
            ("🧑‍🏫", "Teacher Agent",
             "Ask the AI Teacher anything about each question in real time."),
        ]
        for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
            with col:
                st.markdown(
                    f'<div class="imtiqan-card" style="text-align:center;padding:28px 16px;">'
                    f'<div style="font-size:2.2rem;margin-bottom:10px;">{icon}</div>'
                    f'<div style="color:#a78bfa;font-weight:700;font-size:.95rem;'
                    f'margin-bottom:6px;">{title}</div>'
                    f'<div style="color:#94a3b8;font-size:.83rem;line-height:1.6;">'
                    f'{desc}</div></div>',
                    unsafe_allow_html=True,
                )


# Helpers  
def _set_document_loaded(count: int, preview: str):
    st.session_state["document_loaded"]  = True
    st.session_state["chunk_count"]      = count
    st.session_state["raw_text_preview"] = preview