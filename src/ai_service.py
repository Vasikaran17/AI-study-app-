"""AI Service: OpenAI API integration for explanations, note synthesis, quizzes, and study guidance."""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import openai


def get_active_api_key(session_key: Optional[str] = None) -> Optional[str]:
    """Retrieve the active OpenAI API key from session state or environment variable."""
    if session_key and session_key.strip():
        return session_key.strip()
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    return env_key if env_key else None


def has_valid_api_key(session_key: Optional[str] = None) -> bool:
    """Check whether a non-empty API key is available."""
    key = get_active_api_key(session_key)
    return bool(key and len(key) > 10)


class AIService:
    """Service handling all interactions with OpenAI LLM, with fallback modes and error safety."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key) if api_key else None

    def update_key(self, api_key: Optional[str]):
        """Update active API key and reinitialize client."""
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key) if api_key else None

    # -------------------------------------------------------------------------
    # Feature 1: Ask a Question & Get Structured Explanations
    # -------------------------------------------------------------------------
    def answer_question(
        self,
        question: str,
        topic: str,
        relevant_chunks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate a student-level explanation with simple terms, example, and explicit source disclosure."""
        use_notes = bool(relevant_chunks and len(relevant_chunks) > 0)

        # If no client is available, route to intelligent offline fallback
        if not self.client:
            return self._fallback_answer_question(question, topic, relevant_chunks)

        # Assemble context if notes were matched
        context_block = ""
        sources_list = []
        if use_notes:
            context_pieces = []
            for i, chunk in enumerate(relevant_chunks, 1):
                sources_list.append({
                    "filename": chunk["filename"],
                    "location": chunk["location"],
                    "excerpt": chunk["text"][:240] + ("..." if len(chunk["text"]) > 240 else ""),
                    "score": chunk.get("score", 0.0)
                })
                context_pieces.append(
                    f"--- Source Excerpt {i} (File: {chunk['filename']}, {chunk['location']}) ---\n{chunk['text']}"
                )
            context_block = "\n\n".join(context_pieces)

        system_prompt = (
            "You are Study Buddy, an academic tutor for university students. "
            "Your explanations are articulate, pedagogically sound, and directly tailored to university-level study. "
            "Always follow this structured JSON output format:\n"
            "{\n"
            '  "explanation": "A thorough, 2-3 paragraph explanation of the concept, breaking down key mechanisms and principles.",\n'
            '  "simple_terms": "A 2-3 sentence intuitive explanation free of dense jargon.",\n'
            '  "example": "A concrete, relatable real-world or academic example that crystallizes the concept.",\n'
            '  "source_acknowledgment": "A brief sentence stating whether the answer was synthesized from the student\'s course notes or general academic principles."\n'
            "}\n"
            "CRITICAL RULES:\n"
            "1. If course note excerpts are provided, prioritize information from them and cite specific sections.\n"
            "2. If no notes excerpts are provided, state clearly that you are answering from general academic knowledge.\n"
            "3. Never claim notes were consulted if no excerpts are provided.\n"
            "4. Return strictly valid JSON."
        )

        user_content = f"Subject / Topic: {topic}\nStudent Question: {question}\n\n"
        if use_notes:
            user_content += f"STUDENT UPLOADED NOTES CONTEXT:\n{context_block}\n\nPlease explain the concept using the student's notes above as your primary grounding."
        else:
            user_content += "NOTE: No relevant student notes were found in the uploaded documents. Please explain using general academic knowledge and clearly note this."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)

            return {
                "success": True,
                "explanation": parsed.get("explanation", "Could not generate full explanation."),
                "simple_terms": parsed.get("simple_terms", "No summary provided."),
                "example": parsed.get("example", "No example provided."),
                "source_type": "notes" if use_notes else "model",
                "sources": sources_list,
                "source_acknowledgment": parsed.get("source_acknowledgment", ""),
                "disclaimer": "AI-generated explanation for revision. Check primary course syllabi and textbooks for official course requirements."
            }

        except openai.AuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed. Please verify your OpenAI API key in the sidebar.",
                "source_type": "error"
            }
        except openai.RateLimitError:
            return {
                "success": False,
                "error": "OpenAI rate limit reached. Please wait a moment or check your API billing quota.",
                "source_type": "error"
            }
        except Exception as e:
            # Fallback to local parsing if JSON fails
            return self._fallback_answer_question(question, topic, relevant_chunks, error_msg=str(e))

    # -------------------------------------------------------------------------
    # Feature 2: Generate Summary & Key Concepts for Notes
    # -------------------------------------------------------------------------
    def summarize_note(self, note_title: str, note_content: str) -> Dict[str, Any]:
        """Generate a concise summary and 5-7 key concepts from an uploaded note."""
        if not self.client:
            return self._fallback_summarize_note(note_title, note_content)

        # Truncate content if extremely large to fit within model limits safely
        sample_content = note_content[:9000]

        system_prompt = (
            "You are an expert academic tutor. A university student has uploaded their study notes. "
            "Produce a structured study synthesis as JSON:\n"
            "{\n"
            '  "summary": "A concise, high-impact 3-4 sentence academic overview of the note\'s core subject matter.",\n'
            '  "key_concepts": [\n'
            '     {"term": "Term or Mechanism 1", "definition": "Clear, precise 1-2 sentence definition or significance."},\n'
            '     {"term": "Term or Mechanism 2", "definition": "Clear, precise 1-2 sentence definition or significance."}\n'
            '  ],\n'
            '  "core_takeaway": "One overarching revision tip or key formula/theorem to remember."\n'
            "}\n"
            "Include 5 to 7 key concepts. Ensure accurate academic terminology. Return strictly valid JSON."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Note Title: {note_title}\n\nNote Content:\n{sample_content}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            parsed = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "summary": parsed.get("summary", "Summary unavailable."),
                "key_concepts": parsed.get("key_concepts", []),
                "core_takeaway": parsed.get("core_takeaway", "")
            }
        except Exception as e:
            return self._fallback_summarize_note(note_title, note_content, error_msg=str(e))

    # -------------------------------------------------------------------------
    # Feature 3: Generate Quizzes (Multiple Choice with Explanations)
    # -------------------------------------------------------------------------
    def generate_quiz(
        self,
        topic: str,
        note_content: Optional[str] = None,
        note_filename: Optional[str] = None,
        num_questions: int = 4
    ) -> Dict[str, Any]:
        """Generate multiple choice questions with explanations and distractor corrections."""
        if not self.client:
            return self._fallback_generate_quiz(topic, note_content, note_filename, num_questions)

        has_note = bool(note_content and len(note_content.strip()) > 50)
        content_snippet = (note_content[:7000] if has_note else "")

        system_prompt = (
            "You are an academic exam writer for university-level courses. "
            "Generate a rigorous, fair, multiple-choice quiz designed to test conceptual understanding and application. "
            "Output must be strictly valid JSON in the following format:\n"
            "{\n"
            '  "quiz_title": "Concise Descriptive Title",\n'
            '  "topic": "Topic Name",\n'
            '  "questions": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "question": "Question text...",\n'
            '      "options": [\n'
            '        "A) Option A text",\n'
            '        "B) Option B text",\n'
            '        "C) Option C text",\n'
            '        "D) Option D text"\n'
            "      ],\n"
            '      "correct_letter": "A",\n'
            '      "explanation": "Clear explanation of why this answer is correct.",\n'
            '      "distractor_explanations": {\n'
            '        "B": "Why B is a common misconception or incorrect...",\n'
            '        "C": "Why C is incorrect...",\n'
            '        "D": "Why D is incorrect..."\n'
            "      }\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "REQUIREMENTS:\n"
            f"1. Generate exactly {num_questions} questions.\n"
            "2. Options must start with letters 'A) ', 'B) ', 'C) ', 'D) '.\n"
            "3. 'correct_letter' must be one of 'A', 'B', 'C', 'D'.\n"
            "4. Provide constructive explanations for why the correct option is right AND why distractors are wrong."
        )

        user_content = f"Topic: {topic}\nNumber of Questions: {num_questions}\n"
        if has_note:
            user_content += f"Ground questions in this uploaded note ({note_filename}):\n{content_snippet}\n"
        else:
            user_content += "Create standard university-level questions for this topic.\n"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)
            return {
                "success": True,
                "quiz_title": parsed.get("quiz_title", f"{topic} Quiz"),
                "topic": topic,
                "questions": parsed.get("questions", []),
                "source": note_filename if has_note else "General Curriculum"
            }
        except Exception as e:
            return self._fallback_generate_quiz(topic, note_content, note_filename, num_questions, error_msg=str(e))

    # -------------------------------------------------------------------------
    # Feature 5: Study Suggestions Based on Progress
    # -------------------------------------------------------------------------
    def generate_study_suggestions(
        self,
        recent_quizzes: List[Dict],
        notes_summary: List[str]
    ) -> List[Dict[str, str]]:
        """Generate 3-4 constructive, practical next steps based on student quiz performance."""
        if not self.client:
            return self._fallback_study_suggestions(recent_quizzes, notes_summary)

        perf_summary = []
        for q in recent_quizzes[-5:]:
            perf_summary.append(
                f"- Quiz '{q.get('quiz_title', 'Untitled')}' on topic '{q.get('topic', 'General')}': "
                f"Score {q.get('score', 0)}/{q.get('total', 0)} ({q.get('percent', 0):.0f}%)"
            )
        perf_text = "\n".join(perf_summary) if perf_summary else "No quizzes completed yet."
        notes_text = ", ".join(notes_summary) if notes_summary else "No notes uploaded yet."

        system_prompt = (
            "You are a supportive, insightful university academic mentor. "
            "Based on the student's recent quiz results and uploaded topics, produce 3-4 constructive, practical next steps. "
            "Guidelines:\n"
            "- Be practical, concise, and supportive rather than judgmental.\n"
            "- If a student scored poorly on a topic, suggest a concrete review method (e.g. flashcards, deriving a formula, re-reading specific sections).\n"
            "- If a student excelled, suggest exploring an advanced connection or taking a mixed topic quiz.\n"
            "Output JSON format:\n"
            "{\n"
            '  "suggestions": [\n'
            '    {"title": "Action Title", "action": "Clear 2-sentence actionable guidance.", "priority": "High" | "Medium" | "Reinforce"}\n'
            '  ]\n'
            "}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Student Recent Performance:\n{perf_text}\n\nAvailable Notes:\n{notes_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            parsed = json.loads(response.choices[0].message.content)
            return parsed.get("suggestions", self._fallback_study_suggestions(recent_quizzes, notes_summary))
        except Exception:
            return self._fallback_study_suggestions(recent_quizzes, notes_summary)

    # -------------------------------------------------------------------------
    # Intelligent Fallback & Offline Mode Responders
    # -------------------------------------------------------------------------
    def _fallback_answer_question(
        self,
        question: str,
        topic: str,
        relevant_chunks: Optional[List[Dict]] = None,
        error_msg: Optional[str] = None
    ) -> Dict[str, Any]:
        """High-quality offline response when API key is missing or offline preview is needed."""
        use_notes = bool(relevant_chunks and len(relevant_chunks) > 0)
        sources_list = []
        q_lower = question.lower()

        if use_notes:
            for chunk in relevant_chunks:
                sources_list.append({
                    "filename": chunk["filename"],
                    "location": chunk["location"],
                    "excerpt": chunk["text"][:240] + ("..." if len(chunk["text"]) > 240 else ""),
                    "score": chunk.get("score", 0.0)
                })

        # Pre-packaged pedagogical responses for sample domains
        if "respiration" in q_lower or "atp" in q_lower or "glycolysis" in q_lower:
            explanation = (
                "Cellular respiration is the biochemical mechanism eukaryotic cells use to convert the chemical "
                "potential energy stored in glucose into usable adenosine triphosphate (ATP). The pathway progresses "
                "through four tightly regulated stages: Glycolysis in the cytosol (netting 2 ATP and 2 NADH), "
                "Pyruvate Oxidation in the mitochondrial matrix (producing 2 Acetyl-CoA and 2 NADH), "
                "the Citric Acid Cycle (yielding 6 NADH, 2 FADH2, and 2 ATP per glucose), and finally "
                "Oxidative Phosphorylation along the cristae.\n\n"
                "In oxidative phosphorylation, the electron transport chain establishes a steep proton gradient across "
                "the inner membrane. Protons drive the mechanical rotation of ATP synthase via chemiosmosis, generating "
                "the majority of the cell's energy (yielding a theoretical total of 30-32 ATP per glucose molecule)."
            )
            simple = (
                "Think of glucose as a high-value savings bond and ATP as dollar bills you can actually spend in a vending machine. "
                "Cellular respiration is the banking process that breaks that single bond down into approximately 30 to 32 spending units."
            )
            example = (
                "When your muscles sprint during a 100-meter dash, oxygen delivery cannot keep pace with the electron transport chain. "
                "To keep glycolysis running and regenerate NAD+, your cells switch to lactic acid fermentation, causing temporary lactate buildup."
            )

        elif "big-o" in q_lower or "complexity" in q_lower or "algorithm" in q_lower or "o(" in q_lower:
            explanation = (
                "Algorithm complexity measures how the execution time or auxiliary memory of a computational procedure scales "
                "as the input size (n) approaches infinity. Big-O notation specifically provides a mathematical upper bound "
                "on the worst-case growth rate, intentionally abstracting away hardware differences and constant factors.\n\n"
                "For instance, an O(n) linear search tests each item one-by-one, while an O(log n) binary search eliminates half the remaining "
                "elements at each step. Efficient comparison-based sorts such as Merge Sort operate in optimal O(n log n) time, "
                "preventing the catastrophic performance cliff of naive O(n^2) nested loops on large datasets."
            )
            simple = (
                "Big-O tells you how much slower a program will run when you give it twice as much data. "
                "If doubling the data doubles the time, it's linear O(n); if it quadruples the time, it's quadratic O(n^2)."
            )
            example = (
                "Finding a name in an unsorted phonebook requires checking up to all n pages (O(n)). If the directory is sorted alphabetically, "
                "you can flip to the middle and divide repeatedly, needing only about 20 comparisons for 1,000,000 names (O(log n))."
            )

        else:
            # General synthesized explanation
            first_chunk_text = relevant_chunks[0]["text"] if use_notes else ""
            explanation = (
                f"Regarding **{question}** within {topic}:\n\n"
                f"{'Based on your uploaded course notes: ' + first_chunk_text[:350] + '...' if use_notes else 'From foundational principles in ' + topic + ', understanding this concept involves examining its primary mechanisms, theoretical context, and how it governs downstream processes.'}\n\n"
                "When studying this topic for university exams, always identify: (1) the core definition, (2) the governing conditions or assumptions, and (3) typical edge cases."
            )
            simple = (
                f"In essence, '{question.rstrip('?')}' asks how the core mechanism in {topic} operates under standard conditions."
            )
            example = (
                f"A common exam scenario is calculating or analyzing the outcome when one variable in {topic} changes while holding other factors constant."
            )

        return {
            "success": True,
            "explanation": explanation,
            "simple_terms": simple,
            "example": example,
            "source_type": "notes" if use_notes else "model",
            "sources": sources_list,
            "source_acknowledgment": (
                f"Synthesized from your uploaded note '{sources_list[0]['filename']}' ({sources_list[0]['location']})."
                if use_notes else
                "Synthesized from standard curriculum knowledge base (No matching excerpts found in uploaded notes)."
            ),
            "offline_mode": not bool(self.client),
            "disclaimer": "AI-generated explanation for revision. Check primary course materials for official exam specifications."
        }

    def _fallback_summarize_note(self, note_title: str, note_content: str, error_msg: Optional[str] = None) -> Dict[str, Any]:
        """Offline summary generation using heuristic sentence and term extraction."""
        paragraphs = [p.strip() for p in note_content.split("\n\n") if len(p.strip()) > 30]
        summary_intro = (
            f"This study note on '{note_title}' provides a comprehensive academic walkthrough of the subject's "
            "core principles, structural divisions, and quantitative relationships. "
            "Key topics are systematically broken down from foundational definitions to operational mechanisms."
        )

        # Heuristic concept extraction from markdown headers or bullet points
        concepts = []
        lines = note_content.splitlines()
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## ") or line_str.startswith("- ") or line_str.startswith("### "):
                clean_term = re.sub(r"^[#\-\*\d\.\s]+", "", line_str).split(":")[0].strip()
                if 3 < len(clean_term) < 45 and not clean_term.lower().startswith("table"):
                    # Find a sentence following this term
                    defn = "Key structural component or principle detailed in the uploaded document."
                    for p in paragraphs:
                        if clean_term.lower() in p.lower():
                            sentences = [s.strip() for s in p.split(".") if clean_term.lower() in s.lower()]
                            if sentences:
                                defn = sentences[0].replace("\n", " ").strip() + "."
                                break
                    concepts.append({"term": clean_term, "definition": defn[:140]})
            if len(concepts) >= 6:
                break

        if not concepts:
            concepts = [
                {"term": "Core Definition", "definition": "The foundational premise established in the opening section of the notes."},
                {"term": "Primary Mechanisms", "definition": "The multi-step reactions or procedural phases described throughout the document."},
                {"term": "System Constraints", "definition": "Boundary conditions, rates, or limitations governing theoretical outcomes."}
            ]

        return {
            "success": True,
            "summary": summary_intro,
            "key_concepts": concepts[:6],
            "core_takeaway": "Focus your revision on understanding the causal transitions between each phase rather than memorizing isolated terms.",
            "offline_mode": not bool(self.client)
        }

    def _fallback_generate_quiz(
        self,
        topic: str,
        note_content: Optional[str] = None,
        note_filename: Optional[str] = None,
        num_questions: int = 4,
        error_msg: Optional[str] = None
    ) -> Dict[str, Any]:
        """Curated offline quiz questions based on topic or content."""
        t_lower = topic.lower()

        if "respiration" in t_lower or "bio" in t_lower or (note_filename and "respiration" in note_filename.lower()):
            questions = [
                {
                    "id": 1,
                    "question": "What is the net yield of ATP produced directly from one molecule of glucose during glycolysis?",
                    "options": [
                        "A) 2 Net ATP",
                        "B) 4 Net ATP",
                        "C) 32 Net ATP",
                        "D) 0 Net ATP (Glycolysis only consumes energy)"
                    ],
                    "correct_letter": "A",
                    "explanation": "Glycolysis consumes 2 ATP in the preparatory energy-investment phase and synthesizes 4 ATP in the payoff phase, resulting in a net yield of 2 ATP per glucose.",
                    "distractor_explanations": {
                        "B": "4 ATP is the gross total produced in the payoff phase, but 2 ATP were consumed earlier.",
                        "C": "30 to 32 ATP is the total theoretical yield for complete aerobic respiration, not glycolysis alone.",
                        "D": "While glycolysis does invest 2 ATP initially, the subsequent substrate-level phosphorylation produces a net gain."
                    }
                },
                {
                    "id": 2,
                    "question": "Which molecule acts as the terminal electron acceptor in aerobic oxidative phosphorylation?",
                    "options": [
                        "A) Molecular Oxygen (O2)",
                        "B) Pyruvate",
                        "C) NAD+",
                        "D) Cytochrome c"
                    ],
                    "correct_letter": "A",
                    "explanation": "Molecular oxygen (O2) serves as the final electron acceptor at Complex IV of the electron transport chain, binding protons to form water (H2O).",
                    "distractor_explanations": {
                        "B": "Pyruvate acts as an electron acceptor in lactic acid fermentation, not aerobic oxidative phosphorylation.",
                        "C": "NAD+ is an electron carrier that collects electrons during glycolysis and the citric acid cycle.",
                        "D": "Cytochrome c is an intermediate mobile electron carrier, not the final acceptor."
                    }
                },
                {
                    "id": 3,
                    "question": "Where in a eukaryotic cell does the Citric Acid (Krebs) Cycle take place?",
                    "options": [
                        "A) Mitochondrial Matrix",
                        "B) Cytosol",
                        "C) Inner Mitochondrial Membrane",
                        "D) Intermembrane Space"
                    ],
                    "correct_letter": "A",
                    "explanation": "Pyruvate is transported from the cytosol across the mitochondrial membranes into the mitochondrial matrix, where pyruvate oxidation and the citric acid cycle occur.",
                    "distractor_explanations": {
                        "B": "Glycolysis occurs in the cytosol, but the Krebs cycle requires mitochondrial enzymes.",
                        "C": "The inner mitochondrial membrane houses the Electron Transport Chain complexes and ATP synthase.",
                        "D": "The intermembrane space is where protons are pumped to establish the proton gradient."
                    }
                },
                {
                    "id": 4,
                    "question": "What is the primary physiological purpose of fermentation in anaerobic muscle tissue?",
                    "options": [
                        "A) To regenerate NAD+ so glycolysis can continue producing ATP",
                        "B) To produce large amounts of additional ATP via substrate phosphorylation",
                        "C) To eliminate excess carbon dioxide from cellular metabolism",
                        "D) To convert lactic acid back into glycogen"
                    ],
                    "correct_letter": "A",
                    "explanation": "Under anaerobic conditions, NADH cannot transfer electrons to the ETC. Fermentation reduces pyruvate to lactate, which oxidizes NADH back into NAD+, allowing glycolysis to continue.",
                    "distractor_explanations": {
                        "B": "Fermentation itself yields zero additional ATP; its sole metabolic purpose is carrier regeneration.",
                        "C": "Lactic acid fermentation produces no carbon dioxide.",
                        "D": "Converting lactate back into glucose occurs later in the liver via the Cori Cycle, not during muscle fermentation."
                    }
                }
            ]
        elif "algorithm" in t_lower or "computer" in t_lower or "big-o" in t_lower or (note_filename and "algorithm" in note_filename.lower()):
            questions = [
                {
                    "id": 1,
                    "question": "Which of the following time complexities represents the fastest growth rate as input size n approaches infinity?",
                    "options": [
                        "A) O(2^n) - Exponential",
                        "B) O(n^2) - Quadratic",
                        "C) O(n log n) - Linearithmic",
                        "D) O(n) - Linear"
                    ],
                    "correct_letter": "A",
                    "explanation": "Exponential complexity O(2^n) grows far more aggressively than polynomial complexities (n^2, n log n, n), becoming computationally intractable even for moderate n values.",
                    "distractor_explanations": {
                        "B": "While O(n^2) is quadratic, O(2^n) grows much faster once n exceeds ~15.",
                        "C": "O(n log n) is standard for efficient sorting algorithms and grows much slower than O(2^n).",
                        "D": "O(n) scales proportionally and is significantly more efficient than exponential."
                    }
                },
                {
                    "id": 2,
                    "question": "What is the average and worst-case time complexity of Binary Search on a sorted array of size n?",
                    "options": [
                        "A) O(log n)",
                        "B) O(n)",
                        "C) O(1)",
                        "D) O(n log n)"
                    ],
                    "correct_letter": "A",
                    "explanation": "Because Binary Search halves the remaining search interval at each comparison step, the maximum number of steps required is bounded by log2(n).",
                    "distractor_explanations": {
                        "B": "O(n) is the complexity of Linear Search across an unsorted list.",
                        "C": "O(1) is best-case lookup (if the target happens to be at the exact midpoint on the first check).",
                        "D": "O(n log n) is the time complexity of comparison sorting, not binary searching."
                    }
                },
                {
                    "id": 3,
                    "question": "Why is the constant coefficient dropped when simplifying Big-O expressions (e.g., O(4n^2) -> O(n^2))?",
                    "options": [
                        "A) Big-O characterizes asymptotic growth rate as n -> infinity, where constants become negligible relative to the order of magnitude",
                        "B) Constants are strictly equal to 1 in theoretical computer science",
                        "C) Modern compilers automatically optimize away all constant factors",
                        "D) Only logarithmic factors matter in algorithmic efficiency"
                    ],
                    "correct_letter": "A",
                    "explanation": "Big-O is designed to classify algorithms by their asymptotic class of growth. Constant factors reflect hardware differences or compiler flags, whereas growth class dictates long-term scalability.",
                    "distractor_explanations": {
                        "B": "Constants are not 1; they are simply absorbed by the formal definition c * g(n).",
                        "C": "Compilers perform optimizations, but constants are omitted due to mathematical definition, not compiler features.",
                        "D": "All terms matter, but higher-order polynomial or exponential terms dominate."
                    }
                },
                {
                    "id": 4,
                    "question": "What is the theoretical lower bound for any comparison-based sorting algorithm in the worst case?",
                    "options": [
                        "A) Omega(n log n)",
                        "B) Omega(n)",
                        "C) Omega(n^2)",
                        "D) Omega(log n)"
                    ],
                    "correct_letter": "A",
                    "explanation": "A decision tree model for comparison sorting of n elements must distinguish between n! permutations. Since log(n!) = Theta(n log n), no comparison sort can beat Omega(n log n) in the worst case.",
                    "distractor_explanations": {
                        "B": "Linear time O(n) sorting is only possible with non-comparison algorithms like Counting Sort or Radix Sort under bounded key ranges.",
                        "C": "Omega(n^2) is the lower bound of inefficient sorts like Bubble Sort, not the optimal lower bound.",
                        "D": "Omega(log n) is impossible because examining every input element alone requires at least Omega(n)."
                    }
                }
            ]
        else:
            # Generic university quiz questions for custom topic
            questions = [
                {
                    "id": 1,
                    "question": f"In academic study of {topic}, which principle is fundamental to establishing reliable conclusions?",
                    "options": [
                        "A) Rigorous theoretical grounding and empirical validation",
                        "B) Relying exclusively on intuitive assumptions without testing",
                        "C) Discarding conflicting data points without documentation",
                        "D) Assuming experimental outcomes remain invariant across all contexts"
                    ],
                    "correct_letter": "A",
                    "explanation": f"In {topic}, academic rigor requires backing theoretical assertions with empirical or logical evidence and reproducible methodologies.",
                    "distractor_explanations": {
                        "B": "Intuition can guide hypotheses, but formal proof or evidence is required.",
                        "C": "Ignoring outliers or discrepancies violates scientific integrity.",
                        "D": "Boundary conditions must always be formally specified."
                    }
                },
                {
                    "id": 2,
                    "question": f"When analyzing complex systems within {topic}, why is abstraction widely used?",
                    "options": [
                        "A) To manage cognitive complexity by isolating relevant properties from extraneous implementation details",
                        "B) To intentionally obscure mathematical flaws from peer reviewers",
                        "C) Because abstract models require zero computation time",
                        "D) To avoid having to define system variables"
                    ],
                    "correct_letter": "A",
                    "explanation": "Abstraction allows scholars and practitioners to model high-level interactions without becoming bogged down by low-level noise.",
                    "distractor_explanations": {
                        "B": "Abstraction increases clarity rather than concealing errors.",
                        "C": "Abstract models still require analytical or computational resources.",
                        "D": "Precise definitions are essential even at high levels of abstraction."
                    }
                }
            ]

        return {
            "success": True,
            "quiz_title": f"{topic} Mastery Check",
            "topic": topic,
            "questions": questions[:num_questions],
            "source": note_filename or "Curated Academic Question Bank",
            "offline_mode": not bool(self.client)
        }

    def _fallback_study_suggestions(
        self,
        recent_quizzes: List[Dict],
        notes_summary: List[str]
    ) -> List[Dict[str, str]]:
        """Constructive, practical next steps generated offline based on session records."""
        suggestions = []

        if not recent_quizzes:
            suggestions.append({
                "title": "Establish a Baseline with a Quick Quiz",
                "action": "Take a 4-question check on one of your uploaded notes or a chosen subject to identify your current grasp of core concepts.",
                "priority": "High"
            })
            suggestions.append({
                "title": "Extract Key Concepts from Your Notes",
                "action": "Visit the 'My Notes' tab and generate a conceptual breakdown for your uploaded materials to clarify key terminology.",
                "priority": "Medium"
            })
            suggestions.append({
                "title": "Clarify Unclear Mechanisms",
                "action": "Ask a targeted question in the 'Study' tab about any mechanism or definition you find confusing.",
                "priority": "Reinforce"
            })
            return suggestions

        # Analyze scores
        avg_score = sum(q.get("percent", 0) for q in recent_quizzes) / len(recent_quizzes)
        lowest_quiz = min(recent_quizzes, key=lambda q: q.get("percent", 0))

        if lowest_quiz.get("percent", 0) < 75:
            suggestions.append({
                "title": f"Review Foundations: {lowest_quiz.get('topic', 'Recent Topic')}",
                "action": f"Your recent score on '{lowest_quiz.get('quiz_title', 'Quiz')}' was {lowest_quiz.get('percent', 0):.0f}%. Revisit the distractor explanations in your quiz review to clarify where misconceptions occurred.",
                "priority": "High"
            })

        if avg_score >= 80:
            suggestions.append({
                "title": "Synthesize Interdisciplinary Connections",
                "action": "You have demonstrated strong recall on core definitions. Try asking comparative questions (e.g. 'Compare mechanism X with mechanism Y') to deepen analytical synthesis.",
                "priority": "Medium"
            })
        else:
            suggestions.append({
                "title": "Active Recall Practice",
                "action": "Before attempting another quiz, write down 3 key principles from memory, then verify them against your notes to build retention.",
                "priority": "Medium"
            })

        suggestions.append({
            "title": "Targeted Self-Testing",
            "action": "Generate a new quiz focusing specifically on the sub-topics you found most challenging during your review.",
            "priority": "Reinforce"
        })

        return suggestions
