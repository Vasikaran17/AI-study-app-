"""UI Components: Editorial cards, source citations, score badges, and structured layouts."""

from typing import Any, Dict, List, Optional
import streamlit as st


def render_header(title: str = "Study Buddy", subtitle: str = "Your personalized learning workspace for coursework & revision"):
    """Render the calm, editorial header banner."""
    st.markdown(
        f"""
        <div class="study-header-card">
            <h1 class="study-title">{title}</h1>
            <p class="study-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_source_badge(source_type: str, sources: Optional[List[Dict]] = None):
    """Render transparent source disclosure badge and source snippet cards."""
    if source_type == "notes" and sources:
        st.markdown(
            """
            <div style="margin: 0.5rem 0 1rem 0;">
                <span class="badge-pill badge-notes">&#128218; Grounded in Uploaded Notes</span>
                <span style="font-size: 0.82rem; color: #57534E;">Matched from your course material</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.expander("View Note Citations & Matched Excerpts", expanded=False):
            for i, src in enumerate(sources, 1):
                st.markdown(
                    f"""
                    <div class="source-citation-box">
                        <div class="header">
                            <span>Excerpt {i}: <strong>{src.get('filename')}</strong> &middot; {src.get('location')}</span>
                            <span style="margin-left: auto; font-size: 0.75rem; color: #78716C;">Relevance Score: {src.get('score', 0):.2f}</span>
                        </div>
                        <p style="margin: 0.35rem 0 0 0; font-family: monospace; font-size: 0.82rem; line-height: 1.4; color: #292524;">
                            "{src.get('excerpt')}"
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.markdown(
            """
            <div style="margin: 0.5rem 0 1rem 0;">
                <span class="badge-pill badge-model">&#9878; General Curriculum / Model Knowledge</span>
                <span style="font-size: 0.82rem; color: #57534E;">No matching passages were found in your notes. Explained from academic principles.</span>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_explanation_result(result: Dict[str, Any]):
    """Render a comprehensive, readable explanation with distinct callouts and source references."""
    if not result.get("success", False):
        st.error(result.get("error", "An error occurred while generating the explanation."))
        return

    # Source disclosure
    render_source_badge(result.get("source_type", "model"), result.get("sources", []))

    # Core Explanation
    st.markdown("### Conceptual Explanation")
    st.markdown(result.get("explanation", ""))

    # In Simple Terms Callout
    simple_terms = result.get("simple_terms")
    if simple_terms:
        st.markdown(
            f"""
            <div class="callout-simple-terms">
                <div class="title">In Simple Terms</div>
                <div>{simple_terms}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Concrete Example Callout
    example = result.get("example")
    if example:
        st.markdown(
            f"""
            <div class="callout-example">
                <div class="title">Concrete Example</div>
                <div>{example}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Academic Disclaimer
    disclaimer = result.get("disclaimer")
    if disclaimer:
        st.caption(f"&#9432; {disclaimer}")


def render_concept_cards(key_concepts: List[Dict[str, str]]):
    """Render key concept cards for study notes."""
    if not key_concepts:
        st.info("No concepts extracted yet.")
        return

    cols = st.columns(2)
    for i, concept in enumerate(key_concepts):
        col = cols[i % 2]
        with col:
            st.markdown(
                f"""
                <div class="editorial-card" style="padding: 1rem 1.15rem; margin-bottom: 0.85rem;">
                    <div style="font-weight: 600; color: #134E4A; font-size: 0.95rem; margin-bottom: 0.35rem;">
                        {concept.get('term')}
                    </div>
                    <div style="font-size: 0.85rem; color: #44403C; line-height: 1.45;">
                        {concept.get('definition')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_empty_state(title: str, description: str, hint: Optional[str] = None):
    """Render a clean, quiet empty state."""
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px dashed #D6CEBE; border-radius: 8px; padding: 2.5rem 1.5rem; text-align: center; margin: 1.5rem 0;">
            <div style="font-family: 'Newsreader', Georgia, serif; font-size: 1.25rem; font-weight: 600; color: #292524; margin-bottom: 0.4rem;">
                {title}
            </div>
            <p style="color: #78716C; font-size: 0.9rem; max-width: 480px; margin: 0 auto; line-height: 1.5;">
                {description}
            </p>
            {f'<p style="margin-top: 0.75rem; font-size: 0.82rem; color: #134E4A; font-weight: 500;">Tip: {hint}</p>' if hint else ''}
        </div>
        """,
        unsafe_allow_html=True
    )
