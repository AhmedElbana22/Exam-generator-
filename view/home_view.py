import streamlit as st
import re


def _extract_topics_from_text(text: str) -> list[str]:
    """
    Very lightweight keyword extraction so the user can pick topics
    from checkboxes instead of typing freeform.
    Returns up to 20 candidate noun-phrases / significant words.
    """
    # strip short words & numbers, lowercase
    words = re.findall(r'\b[A-Za-z][a-z]{3,}\b', text)
    freq: dict[str, int] = {}
    stopwords = {
        "this","that","with","from","have","been","will","they",
        "their","which","about","into","also","more","than","when",
        "what","were","there","then","some","such","each","these",
        "those","here","just","like","over","only","both","through",
        "after","before","because","between","however","therefore",
        "using","used","based","figure","table","section","chapter",
    }
    for w in words:
        lw = w.lower()
        if lw not in stopwords:
            freq[lw] = freq.get(lw, 0) + 1
    # top 20 by frequency, title-cased
    top = sorted(freq.items(), key=lambda x: -x[1])[:20]
    return [w.title() for w, _ in top if freq[w] > 1]


def render_home(adaptive_controller):
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">🎓 ImtiQan</div>
      <div class="hero-sub">
        AI-Powered Adaptive Quiz Generator &nbsp;·&nbsp;
        Learn smarter, not harder
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 1
    st.markdown('<div class="step-badge">📄 Step 1 &mdash; Load Study Material</div>',
                unsafe_allow_html=True)

    tab_text, tab_pdf = st.tabs(["📋  Paste Text", "📁  Upload PDF"])
 
    with tab_text:
        text_input = st.text_area(
            "Paste your study material below:",
            height=260,
            placeholder=(
                "Paste any content here — lecture notes, articles, "
                "textbook chapters, research papers...\n\n"
                "(Minimum 100 characters)"
            ),
            key="home_text_area",
        )
        col_load, col_info = st.columns([1, 2])
        with col_load:
            load_text_btn = st.button(
                "📥 Load Text", use_container_width=True, key="load_text_btn"
            )
        with col_info:
            if text_input:
                chars = len(text_input.strip())
                colour = "#10b981" if chars >= 100 else "#f59e0b"
                st.markdown(
                    f'<p style="color:{colour};margin-top:10px;">'
                    f'{"✅" if chars>=100 else "⚠️"} {chars} characters</p>',
                    unsafe_allow_html=True,
                )

        if load_text_btn:
            if len(text_input.strip()) < 100:
                st.error("⚠️ Text is too short — please paste at least 100 characters.")
            else:
                with st.spinner("🔍 Processing & indexing text…"):
                    count = adaptive_controller.load_text(text_input)
                    topics = _extract_topics_from_text(text_input)
                st.session_state["document_loaded"] = True
                st.session_state["chunk_count"]     = count
                st.session_state["extracted_topics"] = topics
                st.session_state["raw_text_preview"] = text_input[:400]
                st.success(f"✅ Text loaded — **{count} chunks** indexed and ready!")
                st.rerun()
 
    with tab_pdf:
        uploaded_file = st.file_uploader(
            "Upload a PDF file:",
            type=["pdf"],
            key="home_pdf_uploader",
        )
        if uploaded_file:
            st.markdown(
                f'<p style="color:#a78bfa;">📎 {uploaded_file.name} '
                f'({uploaded_file.size / 1024:.1f} KB)</p>',
                unsafe_allow_html=True,
            )
        load_pdf_btn = st.button(
            "📥 Load PDF",
            use_container_width=True,
            key="load_pdf_btn",
            disabled=uploaded_file is None,
        )
        if uploaded_file and load_pdf_btn:
            with st.spinner("📖 Reading & indexing PDF…"):
                import os
                os.makedirs("data", exist_ok=True)
                temp_path = f"data/temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
                count  = adaptive_controller.load_pdf(temp_path)
                # try to extract preview text for topic suggestions
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(temp_path)
                    raw = " ".join(page.get_text() for page in doc)
                    topics = _extract_topics_from_text(raw)
                    st.session_state["raw_text_preview"] = raw[:400]
                except Exception:
                    topics = []
                    st.session_state["raw_text_preview"] = ""

            st.session_state["document_loaded"]  = True
            st.session_state["chunk_count"]      = count
            st.session_state["extracted_topics"] = topics
            st.success(f"✅ PDF loaded — **{count} chunks** indexed and ready!")
            st.rerun()

    # Loaded banner
    if st.session_state.get("document_loaded"):
        chunk_count = st.session_state.get("chunk_count", 0)
        st.markdown(f"""
        <div class="imtiqan-card" style="
            border-color:rgba(16,185,129,0.4);
            background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(52,211,153,0.05));
            display:flex; align-items:center; gap:16px;">
          <span style="font-size:2rem;">✅</span>
          <div>
            <div style="color:#34d399;font-weight:700;font-size:1rem;">
              Document Ready
            </div>
            <div style="color:#94a3b8;font-size:.88rem;">
              {chunk_count} semantic chunks indexed · ready to generate questions
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Step 2
        st.markdown('<div class="step-badge">⚙️ Step 2 &mdash; Configure Your Quiz</div>',
                    unsafe_allow_html=True)

        # Topic selection
        extracted = st.session_state.get("extracted_topics", [])

        st.markdown("**📌 Focus Topic(s)**")

        if extracted:
            st.markdown(
                '<p style="color:#94a3b8;font-size:.88rem;">'
                'Topics detected from your document — tick any you want '
                'to focus on, <em>or</em> type a custom topic below.</p>',
                unsafe_allow_html=True,
            )
            # Use multiselect for detected topics
            selected_chips = st.multiselect(
                "Detected topics (select one or more):",
                options=extracted,
                default=[],
                key="selected_topics_multi",
                label_visibility="collapsed",
            )
        else:
            selected_chips = []

        custom_topic = st.text_input(
            "✏️ Or enter a custom topic:",
            placeholder="e.g.  neural networks, photosynthesis, World War II …",
            key="custom_topic_input",
        )

        # Resolve final topic
        if selected_chips and custom_topic.strip():
            final_topic = ", ".join(selected_chips) + ", " + custom_topic.strip()
        elif selected_chips:
            final_topic = ", ".join(selected_chips)
        else:
            final_topic = custom_topic.strip()

        if final_topic:
            st.markdown(
                f'<p style="color:#a78bfa;font-size:.88rem;">'
                f'🎯 Will focus on: <strong>{final_topic}</strong></p>',
                unsafe_allow_html=True,
            )

        st.markdown(" ")

        # Quiz settings in columns 
        col1, col2, col3 = st.columns(3)

        with col1:
            question_type = st.selectbox(
                "❓ Question Type",
                options=["MCQ", "true_false", "short_answer"],
                format_func=lambda x: {
                    "MCQ":          "🔘 Multiple Choice",
                    "true_false":   "✔️  True / False",
                    "short_answer": "✍️  Short Answer",
                }[x],
                key="q_type_select",
            )

        with col2:
            difficulty = st.selectbox(
                "🎯 Difficulty",
                options=["easy", "medium", "hard"],
                index=["easy", "medium", "hard"].index(
                    st.session_state.get("recommended_difficulty", "medium")
                ),
                format_func=lambda x: {
                    "easy":   "🟢 Easy",
                    "medium": "🟡 Medium",
                    "hard":   "🔴 Hard",
                }[x],
                key="difficulty_select",
            )

        with col3:
            num_questions = st.select_slider(
                "🔢 Questions",
                options=list(range(2, 16)),
                value=5,
                key="num_q_slider",
            )

        st.markdown(" ")

        language = st.radio(
            "🌍 Language",
            ["english", "arabic"],
            format_func=lambda x: "🇬🇧 English" if x == "english" else "🇸🇦 Arabic",
            horizontal=True,
            key="language_radio",
        )

        # AI recommendation banner  
        if st.session_state.get("last_recommendation"):
            rec = st.session_state["last_recommendation"]
            st.markdown(f"""
            <div class="imtiqan-card" style="
                border-color:rgba(251,191,36,0.4);
                background:linear-gradient(135deg,
                  rgba(251,191,36,0.08),rgba(245,158,11,0.05));">
              <span style="color:#fbbf24;font-weight:700;">💡 ImtiQan Recommends</span><br>
              <span style="color:#e2e8f0;">{rec['message']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Generate button  
        gen_disabled = not final_topic
        if gen_disabled:
            st.markdown(
                '<p style="color:#f59e0b;font-size:.88rem;">'
                '⚠️ Please select or enter a topic to generate the quiz.</p>',
                unsafe_allow_html=True,
            )

        if st.button(
            "🚀  Generate Quiz Now",
            use_container_width=True,
            disabled=gen_disabled,
            key="generate_quiz_btn",
        ):
            with st.spinner(
                f"✨ Generating {num_questions} {question_type} questions "
                f"about '{final_topic}'…"
            ):
                quiz = adaptive_controller.start_quiz(
                    topic=final_topic,
                    question_type=question_type,
                    num_questions=num_questions,
                    language=language,
                    difficulty=difficulty,
                )
            st.session_state["current_quiz"]         = quiz
            st.session_state["feedback_state"]       = None
            st.session_state["answered_questions"]   = []
            st.session_state["current_page"]         = "quiz"
            st.rerun()

    else:
        # Placeholder feature cards when no doc loaded
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        features = [
            ("🤖", "Adaptive AI",
             "Adjusts difficulty automatically based on your performance across sessions."),
            ("📚", "RAG-Powered",
             "Questions are generated directly from your own study material — no hallucinations."),
            ("📊", "Smart Analytics",
             "Tracks weak topics, strong areas and gives personalised recommendations."),
        ]
        for col, (icon, title, desc) in zip([c1, c2, c3], features):
            with col:
                st.markdown(f"""
                <div class="imtiqan-card" style="text-align:center;padding:32px 20px;">
                  <div style="font-size:2.5rem;margin-bottom:12px;">{icon}</div>
                  <div style="color:#a78bfa;font-weight:700;font-size:1rem;
                              margin-bottom:8px;">{title}</div>
                  <div style="color:#94a3b8;font-size:.88rem;line-height:1.6;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)