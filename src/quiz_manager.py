"""Quiz Manager: Session quiz tracking, grading logic, and Pandas progress management."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def initialize_quiz_history_df() -> pd.DataFrame:
    """Initialize an empty Pandas DataFrame for tracking quiz progress across the session."""
    columns = [
        "timestamp",
        "quiz_title",
        "topic",
        "source",
        "score",
        "total",
        "percent",
        "status"
    ]
    return pd.DataFrame(columns=columns)


def grade_quiz(quiz_data: Dict[str, Any], user_answers: Dict[int, str]) -> Dict[str, Any]:
    """Grade submitted user answers against quiz questions and compile review details."""
    questions = quiz_data.get("questions", [])
    total = len(questions)
    correct_count = 0
    review_items = []

    for q in questions:
        q_id = q.get("id")
        correct_letter = q.get("correct_letter", "A").strip().upper()
        user_choice_str = user_answers.get(q_id, "")
        
        # Extract option letter selected by student (e.g., "A) Option text" -> "A")
        user_letter = ""
        if user_choice_str:
            letter_match = user_choice_str.strip()[:1].upper()
            user_letter = letter_match

        is_correct = (user_letter == correct_letter)
        if is_correct:
            correct_count += 1

        # Match option texts
        options = q.get("options", [])
        correct_opt_text = next((opt for opt in options if opt.strip().startswith(correct_letter)), "")
        user_opt_text = user_choice_str or "No answer selected"

        # Determine distractor correction if incorrect
        distractor_corrections = q.get("distractor_explanations", {})
        distractor_msg = distractor_corrections.get(user_letter, "")

        review_items.append({
            "id": q_id,
            "question": q.get("question", ""),
            "is_correct": is_correct,
            "user_choice": user_opt_text,
            "correct_choice": correct_opt_text,
            "explanation": q.get("explanation", ""),
            "distractor_explanation": distractor_msg
        })

    percent = (correct_count / total * 100) if total > 0 else 0.0

    if percent >= 80:
        status = "Mastered (>=80%)"
    elif percent >= 60:
        status = "Satisfactory (60-79%)"
    else:
        status = "Needs Review (<60%)"

    return {
        "score": correct_count,
        "total": total,
        "percent": round(percent, 1),
        "status": status,
        "review_items": review_items,
        "graded_at": datetime.now().strftime("%b %d, %Y %I:%M %p")
    }


def record_quiz_in_history(
    history_df: pd.DataFrame,
    quiz_title: str,
    topic: str,
    source: str,
    grade_results: Dict[str, Any]
) -> pd.DataFrame:
    """Append a graded quiz result row to the Pandas history DataFrame."""
    new_entry = {
        "timestamp": grade_results.get("graded_at", datetime.now().strftime("%b %d, %Y %I:%M %p")),
        "quiz_title": quiz_title,
        "topic": topic,
        "source": source,
        "score": grade_results.get("score", 0),
        "total": grade_results.get("total", 0),
        "percent": grade_results.get("percent", 0.0),
        "status": grade_results.get("status", "Completed")
    }
    
    new_row_df = pd.DataFrame([new_entry])
    if history_df.empty:
        return new_row_df
    updated_df = pd.concat([history_df, new_row_df], ignore_index=True)
    return updated_df


def compute_progress_metrics(history_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute restrained, purposeful summary statistics using Pandas."""
    if history_df.empty:
        return {
            "total_quizzes": 0,
            "total_questions_answered": 0,
            "avg_score_percent": 0.0,
            "best_topic": "N/A",
            "needs_work_topic": "N/A",
            "topic_summary_df": pd.DataFrame(),
            "recent_quizzes_df": pd.DataFrame()
        }

    total_quizzes = len(history_df)
    total_questions = int(history_df["total"].sum())
    avg_score = round(float(history_df["percent"].mean()), 1)

    # Performance aggregated by topic using Pandas groupby
    topic_group = history_df.groupby("topic").agg(
        quizzes_taken=("percent", "count"),
        avg_score=("percent", "mean"),
        best_score=("percent", "max")
    ).reset_index()

    topic_group["avg_score"] = topic_group["avg_score"].round(1)
    topic_group["best_score"] = topic_group["best_score"].round(1)
    topic_group.columns = ["Topic", "Quizzes Completed", "Avg Score (%)", "Best Score (%)"]
    topic_group = topic_group.sort_values(by="Avg Score (%)", ascending=False)

    best_topic = topic_group.iloc[0]["Topic"] if not topic_group.empty else "N/A"
    
    # Identify topic with lowest average score for targeted study recommendations
    lowest_topic_row = topic_group.sort_values(by="Avg Score (%)", ascending=True).iloc[0]
    needs_work_topic = lowest_topic_row["Topic"] if lowest_topic_row["Avg Score (%)"] < 75 else "None (All >= 75%)"

    recent_df = history_df.tail(10)[["timestamp", "quiz_title", "topic", "score", "total", "percent", "status"]].copy()
    recent_df.columns = ["Date / Time", "Quiz Title", "Topic", "Correct", "Questions", "Score (%)", "Performance"]
    # Reverse to show newest on top
    recent_df = recent_df.iloc[::-1].reset_index(drop=True)

    return {
        "total_quizzes": total_quizzes,
        "total_questions_answered": total_questions,
        "avg_score_percent": avg_score,
        "best_topic": best_topic,
        "needs_work_topic": needs_work_topic,
        "topic_summary_df": topic_group,
        "recent_quizzes_df": recent_df
    }
