# 🎓 Study Buddy: Personalized University Learning Assistant

**Study Buddy** is a personalized learning and revision workspace designed specifically for university students. Rather than functioning like a generic AI chatbot or auto-generated dashboard, Study Buddy provides an editorial, calm study environment to help students understand course materials, revise from their own lecture notes, test their knowledge with diagnostic quizzes, and track their revision progress.

---

## 🌟 Core Features

### 1. 📖 Ask a Question (Conceptual Explanations)
- **Subject-Framed Learning**: Select an academic discipline (Computer Science, Biology, Economics, Mathematics, etc.) or input a custom course topic.
- **Student-Level Clarity**: Explanations break down multi-step mechanisms without unnecessary academic pretension.
- **"In Simple Terms"**: Every answer includes an intuitive, jargon-free summary to build conceptual intuition.
- **"Concrete Example"**: Practical real-world or academic examples to help students apply theoretical knowledge.
- **Transparent Source Citations**:
  - If an answer uses your uploaded course notes, Study Buddy displays the exact note title, section/page, relevance score, and verbatim excerpt.
  - If no matching notes are found or search is disabled, Study Buddy explicitly discloses that the explanation is synthesized from general curriculum knowledge. It never falsely implies that notes were searched.

### 2. 📁 Upload and Study Notes
- **Multi-Format Ingestion**: Supports `.pdf` (lecture slides, papers, book chapters) and `.txt` files.
- **Text Extraction & Chunking**: Extracts readable text and segments documents into overlapping semantic sections with section markers.
- **Note Summaries & Key Concepts**: Automatically synthesizes a 3-4 sentence academic overview and extracts 5-7 key concepts with clear definitions.
- **Document Management**: Easily inspect note statistics (word count, sections indexed), preview raw text, or remove files.
- **Built-in Sample Notes**: Includes pre-packaged university notes on *Cellular Respiration* and *Algorithm Complexity* for instant experimentation.

### 3. ✍️ Generate Practice Quizzes
- **Targeted Revision**: Generate multiple-choice quizzes from either a specific uploaded note or a chosen curriculum subject.
- **Pedagogical Feedback**: After submitting answers, students receive a clear score review:
  - Correct answers are highlighted with detailed explanations of why the answer is right.
  - Incorrect choices feature specific **distractor corrections** explaining the underlying misconception.
- **Automatic Progress Logging**: Scores, timestamps, and topics are automatically recorded into the session's progress manager.

### 4. 📊 Track Progress (Pandas-Powered)
- **Session Progress Records**: Uses **Pandas** DataFrames to manage quiz logs, topic aggregations, and performance metrics.
- **Restrained, Purposeful Display**:
  - Key metrics: Quizzes Completed, Average Score %, Total Questions Answered, and Highest Grasp Topic.
  - Topic Performance Breakdown: Shows quizzes completed, average score, and best score per topic.
  - Recent Quiz History Log.
- **CSV Data Export**: Students can download their complete session revision log as a CSV file (`study_buddy_session_progress.csv`).
- **Clear Storage Scope**: Explains that progress records are stored in memory for the active browser session.

### 5. 💡 Targeted Study Suggestions
- **Actionable Next Steps**: Analyzes recent quiz performance and active course materials to provide 3-4 constructive, practical study recommendations (e.g. active recall techniques, reviewing specific distractor explanations, or exploring comparative synthesis).
- **Supportive Tone**: Practical, concise, and encouraging without being judgmental.

---

## 🎨 Editorial Design Aesthetic

Study Buddy is built with an editorial academic aesthetic:
- **Warm Off-White Canvas**: Background (`#FBF9F5`) and card surfaces (`#FFFFFF` with subtle `#E7E2D8` borders).
- **Dark Ink Typography**: High-contrast, readable text (`#1C1917`) paired with serif editorial headings (`Newsreader`).
- **Restrained Deep Teal Accent**: Deep academic teal (`#134E4A`) for focal points, badges, and primary buttons.
- **Distraction-Free UI**: Avoids robot mascots, neon gradients, bloated dashboards, and oversized AI marketing banners.

---

## 🏗️ Architecture & Project Structure

The project is structured into modular, beginner-friendly components:

```
AI chatbot/
├── .streamlit/
│   └── config.toml          # Custom theme configuration (warm off-white, teal accent)
├── sample_notes/
│   ├── Cellular_Respiration_Overview.txt         # Sample university biology notes
│   └── Introduction_to_Algorithm_Complexity.txt # Sample university CS notes
├── src/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Academic subjects, starter prompts, and editorial CSS
│   ├── notes_manager.py     # PDF/TXT extraction, chunking, and transparent BM25 retrieval
│   ├── ai_service.py        # OpenAI API client, JSON formatting, and fallback preview mode
│   ├── quiz_manager.py      # Quiz grading, distractor corrections, and Pandas progress tracking
│   └── ui_components.py     # Reusable cards, source citation badges, and score displays
├── app.py                   # Main Streamlit web application entry point
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation and setup guide
```

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed on your machine.

### Step 1: Clone or Navigate to the Project Directory
```bash
cd "c:\Users\LENOVO\Desktop\AI chatbot"
```

### Step 2: (Recommended) Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure OpenAI API Key

Study Buddy reads your OpenAI API key from the `OPENAI_API_KEY` environment variable.

#### Setting the Environment Variable:

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-proj-your-actual-openai-api-key"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-proj-your-actual-openai-api-key
```

**macOS / Linux (Bash / Zsh):**
```bash
export OPENAI_API_KEY="sk-proj-your-actual-openai-api-key"
```

> **Tip:** You can also enter or override your API key directly inside the app in the **API & Connection Settings** expander in the sidebar. If no API key is provided, Study Buddy runs in **Curated Preview Mode**, allowing you to explore the sample notes, quiz workflows, and progress tracking immediately without an API key!

### Step 5: Run the Streamlit Application
```bash
python -m streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.

---

## 🔍 How the Retrieval Engine Works

Study Buddy uses a transparent, lightweight retrieval algorithm inspired by **BM25 / TF-IDF**:
1. When notes are uploaded or pre-loaded, their text is split into overlapping chunks of ~180 words.
2. When a student asks a question with note-grounding enabled, the query is tokenized, stripped of common stopwords, and scored against all note chunks using term frequency and inverse document frequency (IDF) saturation.
3. If the top-scoring chunk exceeds the relevance threshold, it is supplied to the model as primary grounding context, and an explicit citation badge with the note title and text excerpt is displayed.
4. If no uploaded notes match the query (e.g. asking about microeconomics when only biology notes are uploaded), the retrieval engine returns an empty list, and the system explicitly tells the student that the answer is derived from general academic principles.

---

## 🛡️ Reliability & Academic Disclaimer

- **No Hard-Coded Secrets**: Keys are read strictly from environment variables or in-session password inputs.
- **Graceful Error Handling**: Handles unreadable/empty PDFs, network timeouts, API rate limits, and authentication errors with actionable feedback.
- **Academic Verification Notice**: All explanations and quiz solutions generated by AI are intended for study assistance and conceptual revision. Students should always cross-reference key formulas, dates, and definitions with their primary course syllabus and required textbooks.
