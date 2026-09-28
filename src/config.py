"""Configuration, default topics, and custom styling for Study Buddy."""

APP_NAME = "Study Buddy"
APP_TAGLINE = "A personalized learning workspace for university coursework & revision"
APP_VERSION = "1.0.0"

# Pre-configured subjects/topics for university students
DEFAULT_SUBJECTS = [
    "Computer Science",
    "Biology & Life Sciences",
    "Economics & Finance",
    "Mathematics & Statistics",
    "Psychology & Cognitive Science",
    "History & Philosophy",
    "Custom / Other Topic"
]

# Example starter prompts to assist student exploration
EXAMPLE_PROMPTS = {
    "Biology & Life Sciences": [
        "What is the net ATP yield of glycolysis, and what are its key regulatory enzymes?",
        "How does the electron transport chain establish a proton-motive force?",
        "Compare lactic acid fermentation with alcoholic fermentation."
    ],
    "Computer Science": [
        "Explain the fundamental difference between O(n log n) and O(n^2) with a concrete sorting example.",
        "What is the formal mathematical definition of Big-O notation?",
        "When is it worth trading auxiliary memory for better time complexity?"
    ],
    "Economics & Finance": [
        "Explain the law of diminishing marginal returns in simple terms.",
        "What is the difference between fiscal policy and monetary policy?",
        "How does elasticity of demand affect total revenue for a firm?"
    ],
    "Mathematics & Statistics": [
        "What is the intuitive meaning of an eigenvector and eigenvalue?",
        "Explain the Central Limit Theorem and why sample size matters.",
        "What is the difference between Type I and Type II errors in hypothesis testing?"
    ]
}

# Editorial CSS to establish a calm, focused academic aesthetic
CUSTOM_CSS = """
<style>
/* Import refined typography */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&family=Inter:wght@400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&display=swap');

:root {
    --bg-page: #FBF9F5;
    --bg-card: #FFFFFF;
    --bg-subtle: #F3EFE6;
    --text-primary: #1C1917;
    --text-secondary: #57534E;
    --text-muted: #78716C;
    --accent-teal: #134E4A;
    --accent-teal-soft: #E6F4F1;
    --accent-amber: #B45309;
    --accent-amber-soft: #FEF3C7;
    --border-subtle: #E7E2D8;
    --border-strong: #D6CEBE;
    --shadow-soft: 0 1px 3px rgba(28, 25, 23, 0.04), 0 1px 2px rgba(28, 25, 23, 0.02);
}

/* Global body styling */
html, body, [class*="stApp"] {
    background-color: var(--bg-page);
    color: var(--text-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* Heading styles with editorial serif feel */
h1, h2, h3 {
    font-family: 'Newsreader', Georgia, 'Times New Roman', serif !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.015em;
}

h1 {
    font-size: 2.1rem !important;
    line-height: 1.25 !important;
    margin-bottom: 0.25rem !important;
}

h2 {
    font-size: 1.45rem !important;
    line-height: 1.35 !important;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0.35rem;
    margin-top: 1.2rem !important;
}

h3 {
    font-size: 1.15rem !important;
    margin-top: 0.75rem !important;
}

/* Sidebar refined styling */
section[data-testid="stSidebar"] {
    background-color: #F6F3EB !important;
    border-right: 1px solid var(--border-subtle) !important;
}

section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
}

/* Header container */
.study-header-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-soft);
}

.study-title {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 2rem;
    font-weight: 600;
    color: var(--accent-teal);
    margin: 0;
    line-height: 1.2;
}

.study-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-top: 0.35rem;
    margin-bottom: 0;
}

/* Content cards */
.editorial-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-soft);
}

/* Badges */
.badge-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    margin-right: 0.5rem;
}

.badge-notes {
    background-color: var(--accent-teal-soft);
    color: var(--accent-teal);
    border: 1px solid #BCE2DA;
}

.badge-model {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
}

.badge-neutral {
    background-color: var(--bg-subtle);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
}

/* Special callout boxes */
.callout-simple-terms {
    background-color: #F8FAF9;
    border-left: 3px solid var(--accent-teal);
    border-radius: 0 6px 6px 0;
    padding: 0.85rem 1.1rem;
    margin: 1rem 0;
    font-size: 0.92rem;
}

.callout-simple-terms .title {
    font-weight: 600;
    color: var(--accent-teal);
    margin-bottom: 0.25rem;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.callout-example {
    background-color: #FFFDF8;
    border-left: 3px solid var(--accent-amber);
    border-radius: 0 6px 6px 0;
    padding: 0.85rem 1.1rem;
    margin: 1rem 0;
    font-size: 0.92rem;
}

.callout-example .title {
    font-weight: 600;
    color: var(--accent-amber);
    margin-bottom: 0.25rem;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.source-citation-box {
    background-color: #F4F8F7;
    border: 1px solid #BCE2DA;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-top: 1rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.source-citation-box .header {
    font-weight: 600;
    color: var(--accent-teal);
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.25rem;
}

/* Question prompt pills */
.prompt-suggestion-btn {
    font-size: 0.82rem !important;
    text-align: left !important;
    padding: 0.45rem 0.75rem !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    background: var(--bg-card) !important;
    margin-bottom: 0.35rem !important;
    width: 100% !important;
}

/* Stat metric boxes */
.metric-box {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    text-align: center;
}

.metric-value {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 1.85rem;
    font-weight: 600;
    color: var(--accent-teal);
    line-height: 1.1;
}

.metric-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}

/* Button overrides for deep teal calm feel */
div.stButton > button[kind="primary"] {
    background-color: var(--accent-teal) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent-teal) !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}

div.stButton > button[kind="secondary"], div.stButton > button:not([kind]) {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 6px !important;
}

/* Quiz styling */
.quiz-question-box {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.2rem;
}

.quiz-question-header {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 1.05rem;
    margin-bottom: 0.75rem;
}

.review-correct {
    background-color: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.88rem;
    color: #166534;
}

.review-incorrect {
    background-color: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.88rem;
    color: #991B1B;
}

/* Hide streamlit branding clutter */
footer {visibility: hidden;}
</style>
"""
