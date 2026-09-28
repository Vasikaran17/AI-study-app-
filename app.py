"""Study Buddy - A personalized learning workspace for university coursework & revision."""

import os
from typing import Optional
import pandas as pd
import streamlit as st

from src.ai_service import AIService, get_active_api_key, has_valid_api_key
from src.config import APP_NAME, APP_TAGLINE, CUSTOM_CSS, DEFAULT_SUBJECTS, EXAMPLE_PROMPTS
from src.notes_manager import NotesStore, extract_text_from_file
from src.quiz_manager import (
    compute_progress_metrics,
    grade_quiz,
    initialize_quiz_history_df,
    record_quiz_in_history,
)
from src.ui_components import (
    render_concept_cards,
    render_empty_state,
    render_explanation_result,
    render_header,
)

# -----------------------------------------------------------------------------
# 1. Page Configuration & Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} | University Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom editorial CSS styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
def initialize_session_state():
    """Ensure all required session state keys exist."""
    if "notes_store" not in st.session_state:
        st.session_state.notes_store = NotesStore()

    if "quiz_history_df" not in st.session_state:
        st.session_state.quiz_history_df = initialize_quiz_history_df()

    if "current_quiz" not in st.session_state:
        st.session_state.current_quiz = None

    if "user_quiz_answers" not in st.session_state:
        st.session_state.user_quiz_answers = {}

    if "quiz_graded_result" not in st.session_state:
        st.session_state.quiz_graded_result = None

    if "active_explanation" not in st.session_state:
        st.session_state.active_explanation = None

    if "active_question_input" not in st.session_state:
        st.session_state.active_question_input = ""

    if "sample_notes_loaded" not in st.session_state:
        st.session_state.sample_notes_loaded = False

    if "session_api_key" not in st.session_state:
        st.session_state.session_api_key = ""


initialize_session_state()


def load_sample_course_notes():
    """Load pre-packaged university sample notes into the session store."""
    notes_store = st.session_state.notes_store
    samples = [
        ("Cellular_Respiration_Overview.txt", "Cellular Respiration & ATP Pathways"),
        ("Introduction_to_Algorithm_Complexity.txt", "Algorithm Complexity & Big-O Notation")
    ]
    loaded_count = 0
    for filename, title in samples:
        filepath = os.path.join(os.path.dirname(__file__), "sample_notes", filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Check if already added
                already_exists = any(n["filename"] == filename for n in notes_store.list_notes())
                if not already_exists:
                    notes_store.add_note(filename=filename, content=content, title=title)
                    loaded_count += 1
    st.session_state.sample_notes_loaded = True
    return loaded_count


# Preload sample notes on first visit for immediate student exploration
if not st.session_state.sample_notes_loaded and st.session_state.notes_store.total_notes_count() == 0:
    load_sample_course_notes()


# Initialize AI Service
active_key = get_active_api_key(st.session_state.session_api_key)
ai_service = AIService(api_key=active_key)


# -----------------------------------------------------------------------------
# 3. Sidebar Navigation & Academic Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #E7E2D8; margin-bottom: 1rem;">
            <div style="font-family: 'Newsreader', Georgia, serif; font-size: 1.55rem; font-weight: 600; color: #134E4A;">
                {APP_NAME}
            </div>
            <div style="font-size: 0.8rem; color: #57534E; margin-top: 0.15rem;">
                Personalized University Revision Tool
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Clean navigation
    nav_selection = st.radio(
        "Workspace View",
        options=["Study", "My Notes", "Quiz", "Progress"],
        format_func=lambda x: {
            "Study": "📖  Study",
            "My Notes": "📁  My Notes",
            "Quiz": "✍️  Quiz",
            "Progress": "📊  Progress"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("<hr style='margin: 1.25rem 0 0.85rem 0; border: none; border-top: 1px solid #E7E2D8;'>", unsafe_allow_html=True)

    # Active Notes Summary badge
    total_notes = st.session_state.notes_store.total_notes_count()
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E7E2D8; border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #78716C;">Course Material</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #134E4A; margin-top: 0.1rem;">
                {total_notes} {'Note' if total_notes == 1 else 'Notes'} Available
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # API Configuration Expander
    with st.expander("API & Connection Settings", expanded=False):
        st.markdown(
            "<p style='font-size: 0.82rem; color: #57534E;'>Provide an OpenAI API key for live GPT-4o-mini answers, or rely on curated fallback explanations.</p>",
            unsafe_allow_html=True
        )

        has_env_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
        key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.session_api_key,
            type="password",
            placeholder="sk-proj-...",
            help="Your key remains in your local browser session and is never logged."
        )
        if key_input != st.session_state.session_api_key:
            st.session_state.session_api_key = key_input.strip()
            active_key = get_active_api_key(st.session_state.session_api_key)
            ai_service.update_key(active_key)
            st.rerun()

        if has_valid_api_key(st.session_state.session_api_key):
            st.markdown(
                """
                <div style="font-size: 0.78rem; color: #166534; background: #F0FDF4; border: 1px solid #BBF7D0; padding: 0.35rem 0.6rem; border-radius: 4px; margin-top: 0.5rem;">
                    &#10003; <strong>Live OpenAI API Active</strong>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="font-size: 0.78rem; color: #854D0E; background: #FEFCE8; border: 1px solid #FEF08A; padding: 0.35rem 0.6rem; border-radius: 4px; margin-top: 0.5rem;">
                    &#9888; <strong>Curated Preview Mode</strong><br>
                    Set <code>OPENAI_API_KEY</code> env var or paste key above for live generation.
                </div>
                """,
                unsafe_allow_html=True
            )

    # Quick workspace actions
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    if not st.session_state.sample_notes_loaded or total_notes == 0:
        if st.button("Load University Sample Notes", use_container_width=True):
            added = load_sample_course_notes()
            st.success(f"Added {added} sample note files.")
            st.rerun()

    if st.button("Reset Session Workspace", help="Clears loaded notes, quiz history, and active answers", use_container_width=True):
        st.session_state.notes_store = NotesStore()
        st.session_state.quiz_history_df = initialize_quiz_history_df()
        st.session_state.current_quiz = None
        st.session_state.user_quiz_answers = {}
        st.session_state.quiz_graded_result = None
        st.session_state.active_explanation = None
        st.session_state.sample_notes_loaded = False
        st.rerun()


# -----------------------------------------------------------------------------
# 4. View 1: STUDY (Ask a Question & Conceptual Explanations)
# -----------------------------------------------------------------------------
if nav_selection == "Study":
    render_header(
        title="Study Workspace",
        subtitle="Ask questions in plain language, receive structured conceptual breakdowns, and review source notes."
    )

    col_topic, col_notes_opt = st.columns([2, 1])
    with col_topic:
        subject_choice = st.selectbox(
            "Subject or Course Topic",
            options=DEFAULT_SUBJECTS,
            index=0,
            help="Select the discipline to frame the academic context."
        )
        if subject_choice == "Custom / Other Topic":
            active_topic = st.text_input("Enter Custom Subject / Course Name", placeholder="e.g. Organic Chemistry, Macroeconomics...")
            if not active_topic.strip():
                active_topic = "General Academic Curriculum"
        else:
            active_topic = subject_choice

    with col_notes_opt:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        search_notes_enabled = st.checkbox(
            "Ground answer in uploaded notes",
            value=True,
            help="When enabled, Study Buddy searches your uploaded notes first and provides transparent citations."
        )

    # Example starter prompts
    if active_topic in EXAMPLE_PROMPTS:
        st.markdown("<p style='font-size: 0.85rem; color: #57534E; margin-bottom: 0.35rem;'>Sample starter inquiries:</p>", unsafe_allow_html=True)
        example_cols = st.columns(len(EXAMPLE_PROMPTS[active_topic]))
        for i, prompt_text in enumerate(EXAMPLE_PROMPTS[active_topic]):
            with example_cols[i]:
                if st.button(f"“{prompt_text[:50]}...”", key=f"ex_btn_{i}", help=prompt_text, use_container_width=True):
                    st.session_state.active_question_input = prompt_text
                    st.rerun()

    # Question Input
    question_input = st.text_area(
        "Your Academic Question",
        value=st.session_state.active_question_input,
        placeholder="e.g., Explain the difference between glycolysis and the citric acid cycle, or what does O(n log n) mean in practice?",
        height=100
    )

    col_ask_btn, col_clear_btn = st.columns([1, 5])
    with col_ask_btn:
        ask_submitted = st.button("Explain Concept", type="primary", use_container_width=True)

    if ask_submitted:
        clean_q = question_input.strip()
        if not clean_q:
            st.warning("Please type a question before submitting.")
        else:
            with st.spinner("Analyzing curriculum principles and searching notes..."):
                relevant_chunks = []
                if search_notes_enabled and st.session_state.notes_store.total_notes_count() > 0:
                    relevant_chunks = st.session_state.notes_store.search_relevant_chunks(clean_q, top_k=3)

                explanation_res = ai_service.answer_question(
                    question=clean_q,
                    topic=active_topic,
                    relevant_chunks=relevant_chunks
                )
                st.session_state.active_explanation = explanation_res

    # Display Active Explanation Result
    if st.session_state.active_explanation:
        st.markdown("<hr style='margin: 1.5rem 0 1rem 0; border: none; border-top: 1px solid #E7E2D8;'>", unsafe_allow_html=True)
        render_explanation_result(st.session_state.active_explanation)


# -----------------------------------------------------------------------------
# 5. View 2: MY NOTES (Upload & Study Notes)
# -----------------------------------------------------------------------------
elif nav_selection == "My Notes":
    render_header(
        title="Course Notes & Documents",
        subtitle="Upload your lecture notes, extract core concepts, and build a personalized revision corpus."
    )

    tab_upload, tab_manage = st.tabs(["Upload New Note", "Manage Uploaded Notes"])

    with tab_upload:
        st.markdown("### Add Course Notes (.pdf, .txt)")
        uploaded_file = st.file_uploader(
            "Select a course document to upload",
            type=["pdf", "txt"],
            help="PDF lecture slides, syllabus readings, or plain text notes are parsed and indexed."
        )

        note_title_input = st.text_input(
            "Document Title (Optional)",
            placeholder="e.g. Chapter 4: Cellular Metabolism"
        )

        if uploaded_file is not None:
            if st.button("Process and Index Note", type="primary"):
                with st.spinner("Extracting text and chunking content..."):
                    file_bytes = uploaded_file.read()
                    extracted_text, error_msg = extract_text_from_file(file_bytes, uploaded_file.name)

                    if error_msg:
                        st.error(error_msg)
                    else:
                        title = note_title_input.strip() if note_title_input.strip() else None
                        record = st.session_state.notes_store.add_note(
                            filename=uploaded_file.name,
                            content=extracted_text,
                            title=title
                        )
                        st.success(
                            f"Successfully indexed '{record['title']}' ({record['word_count']} words in {len(record['chunks'])} searchable sections)."
                        )
                        st.rerun()

    with tab_manage:
        notes_list = st.session_state.notes_store.list_notes()
        if not notes_list:
            render_empty_state(
                title="No Course Notes Uploaded",
                description="Upload lecture transcripts, slide summaries, or chapter notes in PDF or TXT format to enable source-grounded answers.",
                hint="You can click 'Load University Sample Notes' in the sidebar to test immediately."
            )
        else:
            st.markdown(f"### Available Course Documents ({len(notes_list)})")
            for note in notes_list:
                with st.container():
                    st.markdown(
                        f"""
                        <div class="editorial-card" style="margin-bottom: 1rem;">
                            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                <div style="font-family: 'Newsreader', Georgia, serif; font-size: 1.25rem; font-weight: 600; color: #134E4A;">
                                    {note['title']}
                                </div>
                                <span class="badge-pill badge-neutral">{note['filename']}</span>
                            </div>
                            <div style="font-size: 0.82rem; color: #78716C; margin-top: 0.25rem;">
                                Added: {note['uploaded_at']} &middot; {note['word_count']} words &middot; {len(note['chunks'])} indexed sections
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    col_summary_btn, col_view_btn, col_del_btn = st.columns([2, 2, 1])

                    with col_summary_btn:
                        summary_btn_key = f"sum_{note['id']}"
                        if st.button("Synthesize Summary & Key Concepts", key=summary_btn_key, use_container_width=True):
                            with st.spinner(f"Synthesizing key concepts from {note['title']}..."):
                                summary_res = ai_service.summarize_note(note['title'], note['content'])
                                note["summary"] = summary_res.get("summary")
                                note["key_concepts"] = summary_res.get("key_concepts")
                                note["core_takeaway"] = summary_res.get("core_takeaway")
                                st.rerun()

                    with col_view_btn:
                        view_btn_key = f"view_{note['id']}"
                        show_content = st.checkbox("Preview Document Text", key=view_btn_key)

                    with col_del_btn:
                        del_btn_key = f"del_{note['id']}"
                        if st.button("Remove Note", key=del_btn_key, use_container_width=True):
                            st.session_state.notes_store.remove_note(note['id'])
                            st.warning(f"Removed '{note['title']}'.")
                            st.rerun()

                    # Render cached summary if available
                    if note.get("summary"):
                        st.markdown(
                            f"""
                            <div class="callout-simple-terms" style="margin-top: 0.75rem;">
                                <div class="title">Academic Executive Summary</div>
                                <div>{note['summary']}</div>
                                {f'<div style="margin-top: 0.5rem; font-style: italic; color: #134E4A; font-size: 0.85rem;">Key Takeaway: {note.get("core_takeaway")}</div>' if note.get('core_takeaway') else ''}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # Render cached key concepts
                    if note.get("key_concepts"):
                        st.markdown("#### Key Concepts & Formulations")
                        render_concept_cards(note["key_concepts"])

                    # Document Preview accordion
                    if show_content:
                        with st.expander("Full Text & Section Chunks", expanded=True):
                            st.text_area(
                                "Raw Extracted Text",
                                value=note["content"],
                                height=280,
                                disabled=True,
                                key=f"raw_text_{note['id']}"
                            )

                    st.markdown("<hr style='margin: 1.25rem 0; border: none; border-top: 1px solid #E7E2D8;'>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. View 3: QUIZ (Generate Quizzes, Test Knowledge, Review Feedback)
# -----------------------------------------------------------------------------
elif nav_selection == "Quiz":
    render_header(
        title="Knowledge Assessment & Quizzes",
        subtitle="Generate multiple-choice checks from your coursework, review constructive corrections, and log progress."
    )

    # Quiz Generation Setup
    st.markdown("### Generate a Practice Quiz")
    col_q_source, col_q_topic, col_q_num = st.columns([1.5, 1.5, 1])

    with col_q_source:
        notes_options = [("topic_only", "General Topic Curriculum")]
        for n in st.session_state.notes_store.list_notes():
            notes_options.append((n["id"], f"Note: {n['title']}"))

        selected_source_tuple = st.selectbox(
            "Quiz Source Material",
            options=notes_options,
            format_func=lambda x: x[1]
        )

    with col_q_topic:
        quiz_topic_input = st.selectbox(
            "Subject / Topic Area",
            options=DEFAULT_SUBJECTS,
            index=0
        )
        if quiz_topic_input == "Custom / Other Topic":
            quiz_topic = st.text_input("Specify Custom Topic", value="University Exam Prep")
        else:
            quiz_topic = quiz_topic_input

    with col_q_num:
        num_questions = st.select_slider(
            "Number of Questions",
            options=[3, 4, 5],
            value=4
        )

    if st.button("Generate Quiz Now", type="primary"):
        with st.spinner("Synthesizing questions, answer keys, and pedagogical distractor explanations..."):
            note_content = None
            note_filename = None
            if selected_source_tuple[0] != "topic_only":
                note_rec = st.session_state.notes_store.get_note(selected_source_tuple[0])
                if note_rec:
                    note_content = note_rec["content"]
                    note_filename = note_rec["filename"]
                    quiz_topic = note_rec["title"]

            generated_quiz = ai_service.generate_quiz(
                topic=quiz_topic,
                note_content=note_content,
                note_filename=note_filename,
                num_questions=num_questions
            )

            if generated_quiz.get("success", False) and generated_quiz.get("questions"):
                st.session_state.current_quiz = generated_quiz
                st.session_state.user_quiz_answers = {}
                st.session_state.quiz_graded_result = None
                st.rerun()
            else:
                st.error("Failed to generate quiz. Please try again or select another topic.")

    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #E7E2D8;'>", unsafe_allow_html=True)

    # Active Quiz Rendering
    active_quiz = st.session_state.current_quiz
    if not active_quiz:
        render_empty_state(
            title="No Active Quiz",
            description="Select a topic or course note above to generate a 4-question revision check.",
            hint="Quizzes include detailed explanations for every correct option and constructive corrections for mistakes."
        )
    else:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 1rem;">
                <h2 style="margin: 0; font-family: 'Newsreader', Georgia, serif; color: #134E4A;">{active_quiz.get('quiz_title')}</h2>
                <span class="badge-pill badge-neutral">Source: {active_quiz.get('source', 'General Curriculum')}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Form for questions
        graded_result = st.session_state.quiz_graded_result

        # If not graded yet, show active interactive quiz form
        if graded_result is None:
            with st.form("quiz_form"):
                for q in active_quiz.get("questions", []):
                    q_id = q.get("id")
                    st.markdown(
                        f"""
                        <div class="quiz-question-box">
                            <div class="quiz-question-header">Question {q_id}: {q.get('question')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    options = q.get("options", [])
                    st.radio(
                        label=f"Select your answer for Question {q_id}:",
                        options=options,
                        index=None,
                        key=f"q_choice_{q_id}",
                        label_visibility="collapsed"
                    )
                    st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)

                submit_quiz_btn = st.form_submit_button("Submit Quiz for Evaluation", type="primary")

                if submit_quiz_btn:
                    # Gather answers
                    answers = {}
                    all_answered = True
                    for q in active_quiz.get("questions", []):
                        choice = st.session_state.get(f"q_choice_{q.get('id')}")
                        if not choice:
                            all_answered = False
                        answers[q.get("id")] = choice or ""

                    if not all_answered:
                        st.warning("Please select an answer for all questions before submitting.")
                    else:
                        st.session_state.user_quiz_answers = answers
                        graded = grade_quiz(active_quiz, answers)
                        st.session_state.quiz_graded_result = graded

                        # Record in Pandas DataFrame
                        st.session_state.quiz_history_df = record_quiz_in_history(
                            history_df=st.session_state.quiz_history_df,
                            quiz_title=active_quiz.get("quiz_title", "Untitled Quiz"),
                            topic=active_quiz.get("topic", "General"),
                            source=active_quiz.get("source", "Curriculum"),
                            grade_results=graded
                        )
                        st.rerun()

        # Display Graded Review
        else:
            score = graded_result["score"]
            total = graded_result["total"]
            percent = graded_result["percent"]
            status = graded_result["status"]

            status_color = "#166534" if percent >= 80 else ("#854D0E" if percent >= 60 else "#991B1B")
            status_bg = "#F0FDF4" if percent >= 80 else ("#FEFCE8" if percent >= 60 else "#FEF2F2")

            st.markdown(
                f"""
                <div style="background: {status_bg}; border: 1px solid {status_color}; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; text-align: center;">
                    <div style="font-family: 'Newsreader', Georgia, serif; font-size: 2.2rem; font-weight: 600; color: {status_color};">
                        {score} / {total} ({percent:.0f}%)
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 500; color: {status_color}; margin-top: 0.25rem;">
                        {status}
                    </div>
                    <div style="font-size: 0.8rem; color: #57534E; margin-top: 0.35rem;">
                        Result automatically recorded in your session progress tracker.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("### Detailed Question Review & Corrections")
            for item in graded_result.get("review_items", []):
                q_id = item["id"]
                is_correct = item["is_correct"]

                box_class = "review-correct" if is_correct else "review-incorrect"
                icon = "&#10003; Correct" if is_correct else "&#10007; Incorrect"

                st.markdown(
                    f"""
                    <div class="quiz-question-box">
                        <div style="font-weight: 600; font-size: 1rem; color: #1C1917; margin-bottom: 0.5rem;">
                            Question {q_id}: {item['question']}
                        </div>
                        <div style="font-size: 0.88rem; margin-bottom: 0.35rem;">
                            <strong>Your Selection:</strong> {item['user_choice']}
                        </div>
                        <div style="font-size: 0.88rem; margin-bottom: 0.65rem;">
                            <strong>Correct Answer:</strong> {item['correct_choice']}
                        </div>
                        <div class="{box_class}">
                            <div style="font-weight: 600; margin-bottom: 0.25rem;">{icon}</div>
                            <div>{item['explanation']}</div>
                            {f'<div style="margin-top: 0.45rem; font-style: italic; border-top: 1px dashed rgba(0,0,0,0.15); padding-top: 0.35rem;">Distractor note: {item["distractor_explanation"]}</div>' if item.get('distractor_explanation') and not is_correct else ''}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            col_retake, col_new_quiz = st.columns(2)
            with col_retake:
                if st.button("Retake This Quiz", use_container_width=True):
                    st.session_state.quiz_graded_result = None
                    st.session_state.user_quiz_answers = {}
                    st.rerun()

            with col_new_quiz:
                if st.button("Start Another Quiz", type="primary", use_container_width=True):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_graded_result = None
                    st.session_state.user_quiz_answers = {}
                    st.rerun()


# -----------------------------------------------------------------------------
# 7. View 4: PROGRESS (Pandas Records, Performance by Topic, Study Guidance)
# -----------------------------------------------------------------------------
elif nav_selection == "Progress":
    render_header(
        title="Learning Progress & Study Guidance",
        subtitle="Review quiz outcomes, analyze performance across subject topics, and follow targeted next steps."
    )

    history_df = st.session_state.quiz_history_df
    metrics = compute_progress_metrics(history_df)

    # Restrained, purposeful summary metric boxes
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{metrics['total_quizzes']}</div>
                <div class="metric-label">Quizzes Completed</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{metrics['avg_score_percent']}%</div>
                <div class="metric-label">Average Score</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m3:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{metrics['total_questions_answered']}</div>
                <div class="metric-label">Questions Evaluated</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_m4:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value" style="font-size: 1.25rem; padding-top: 0.35rem;">{metrics['best_topic']}</div>
                <div class="metric-label">Highest Grasp</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Storage notice
    st.markdown(
        """
        <div style="background: #F8FAF9; border-left: 3px solid #134E4A; padding: 0.75rem 1rem; margin: 1.5rem 0; font-size: 0.85rem; color: #57534E;">
            <strong>Session Storage Notice:</strong> Progress metrics and quiz records are managed in Pandas memory for your active browser session. To retain records across sessions, use the CSV export below.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Section 1: Study Suggestions based on performance
    st.markdown("### Targeted Study Guidance")
    recent_records = history_df.to_dict(orient="records") if not history_df.empty else []
    notes_titles = [n["title"] for n in st.session_state.notes_store.list_notes()]

    with st.spinner("Analyzing performance patterns..."):
        suggestions = ai_service.generate_study_suggestions(recent_records, notes_titles)

    if suggestions:
        sug_cols = st.columns(len(suggestions))
        for i, sug in enumerate(suggestions):
            with sug_cols[i]:
                priority_color = "#134E4A" if sug.get("priority") == "High" else "#B45309"
                st.markdown(
                    f"""
                    <div class="editorial-card" style="height: 100%;">
                        <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 600; color: {priority_color}; margin-bottom: 0.35rem;">
                            {sug.get('priority', 'Suggested Step')}
                        </div>
                        <div style="font-family: 'Newsreader', Georgia, serif; font-size: 1.1rem; font-weight: 600; color: #1C1917; margin-bottom: 0.45rem;">
                            {sug.get('title')}
                        </div>
                        <div style="font-size: 0.86rem; color: #44403C; line-height: 1.45;">
                            {sug.get('action')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #E7E2D8;'>", unsafe_allow_html=True)

    # Section 2: Performance by Topic
    st.markdown("### Performance Breakdown by Course Topic")
    topic_df = metrics.get("topic_summary_df")
    if topic_df.empty:
        render_empty_state(
            title="No Topic Data Available Yet",
            description="Take your first quiz in the 'Quiz' tab to unlock topic-level mastery analysis.",
            hint="Scores will aggregate automatically here by subject."
        )
    else:
        st.dataframe(
            topic_df,
            use_container_width=True,
            hide_index=True
        )

    # Section 3: Recent Quiz History Log
    st.markdown("### Recent Quiz Log")
    recent_df = metrics.get("recent_quizzes_df")
    if recent_df.empty:
        st.info("No completed quizzes recorded in this session.")
    else:
        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True
        )

        # CSV Download Button
        csv_data = history_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Session Progress as CSV",
            data=csv_data,
            file_name="study_buddy_session_progress.csv",
            mime="text/csv"
        )
