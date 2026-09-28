"""Notes Manager: Extraction, chunking, and transparent keyword/TF-IDF retrieval."""

import io
import math
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pypdf

# Common English stopwords for query tokenization
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more",
    "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's",
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Extract lowercase alphanumeric tokens, filtering out single characters and punctuation."""
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def extract_text_from_file(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    """Extract text from uploaded PDF or TXT file bytes.
    
    Returns:
        Tuple of (clean_text, error_message). If successful, error_message is empty.
    """
    ext = filename.lower().split(".")[-1]
    if ext == "txt":
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(encoding)
                if not text.strip():
                    return "", "The uploaded text file is empty."
                return text.strip(), ""
            except UnicodeDecodeError:
                continue
        return "", "Could not decode text file with standard encodings."

    elif ext == "pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            if len(reader.pages) == 0:
                return "", "The uploaded PDF has no readable pages."
            
            pages_text = []
            for i, page in enumerate(reader.pages):
                page_content = page.extract_text() or ""
                if page_content.strip():
                    pages_text.append(f"--- [Page {i + 1}] ---\n{page_content.strip()}")
            
            full_text = "\n\n".join(pages_text).strip()
            if not full_text:
                return "", "No extractable text found in this PDF (it may contain scanned image-only pages)."
            return full_text, ""
        except Exception as e:
            return "", f"Error reading PDF file: {str(e)}"
    else:
        return "", f"Unsupported file type: .{ext}. Please upload a .txt or .pdf file."


def chunk_text(text: str, filename: str, note_id: str, chunk_size_words: int = 180, overlap_words: int = 40) -> List[Dict]:
    """Divide text into overlapping word chunks with metadata for precise citations."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    # If text is structured in paragraphs, combine or split into coherent chunks
    words = text.split()
    if not words:
        return []

    chunks = []
    start_idx = 0
    chunk_num = 1

    while start_idx < len(words):
        end_idx = min(start_idx + chunk_size_words, len(words))
        chunk_slice = words[start_idx:end_idx]
        chunk_content = " ".join(chunk_slice)
        
        # Try to detect any heading or page markers inside this chunk
        marker_match = re.search(r"--- \[(Page \d+)\] ---", chunk_content)
        location_label = marker_match.group(1) if marker_match else f"Section {chunk_num}"

        chunks.append({
            "chunk_id": f"{note_id}_c{chunk_num}",
            "note_id": note_id,
            "filename": filename,
            "location": location_label,
            "text": chunk_content,
            "word_count": len(chunk_slice)
        })

        if end_idx >= len(words):
            break
        start_idx += (chunk_size_words - overlap_words)
        chunk_num += 1

    return chunks


class NotesStore:
    """In-memory notes store for the user's active session with BM25 / TF-IDF retrieval."""

    def __init__(self):
        self.notes: Dict[str, Dict] = {}

    def add_note(self, filename: str, content: str, title: Optional[str] = None) -> Dict:
        """Add a parsed note, chunk it, and store in session."""
        note_id = str(uuid.uuid4())[:8]
        clean_title = title or filename.rsplit(".", 1)[0].replace("_", " ").title()
        
        chunks = chunk_text(content, filename=filename, note_id=note_id)
        
        note_record = {
            "id": note_id,
            "title": clean_title,
            "filename": filename,
            "content": content,
            "chunks": chunks,
            "uploaded_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
            "word_count": len(content.split()),
            "char_count": len(content),
            "summary": None,
            "key_concepts": None
        }
        self.notes[note_id] = note_record
        return note_record

    def remove_note(self, note_id: str) -> bool:
        """Remove a note by ID."""
        if note_id in self.notes:
            del self.notes[note_id]
            return True
        return False

    def get_note(self, note_id: str) -> Optional[Dict]:
        return self.notes.get(note_id)

    def list_notes(self) -> List[Dict]:
        return list(self.notes.values())

    def total_notes_count(self) -> int:
        return len(self.notes)

    def search_relevant_chunks(self, query: str, top_k: int = 3, min_score_threshold: float = 0.8) -> List[Dict]:
        """Simple, transparent BM25-inspired retrieval over all note chunks.
        
        Returns a list of matching chunk dicts with 'score' and 'matched_terms'.
        If no chunks meet the threshold, returns an empty list.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        all_chunks: List[Dict] = []
        for note in self.notes.values():
            all_chunks.extend(note["chunks"])

        if not all_chunks:
            return []

        # Calculate document frequency for each query token
        total_chunks = len(all_chunks)
        doc_freq = {}
        for token in query_tokens:
            freq = sum(1 for c in all_chunks if token in c["text"].lower())
            doc_freq[token] = freq

        # Average chunk length
        avg_chunk_len = sum(c["word_count"] for c in all_chunks) / max(1, total_chunks)

        scored_chunks = []
        k1 = 1.5
        b = 0.75

        for chunk in all_chunks:
            chunk_tokens = tokenize(chunk["text"])
            chunk_len = len(chunk_tokens)
            score = 0.0
            matched_terms = []

            for token in query_tokens:
                tf = chunk_tokens.count(token)
                if tf > 0:
                    matched_terms.append(token)
                    # Standard smoothed BM25 IDF
                    df = doc_freq.get(token, 0)
                    idf = math.log(1.0 + (total_chunks - df + 0.5) / (df + 0.5))
                    # BM25 term saturation
                    term_score = idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (chunk_len / max(1, avg_chunk_len)))))
                    score += term_score

            # Boost if query tokens appear adjacent or in succession
            query_phrase = " ".join(query_tokens[:3])
            if query_phrase and query_phrase in chunk["text"].lower():
                score += 2.0

            if score > 0 and matched_terms:
                chunk_copy = dict(chunk)
                chunk_copy["score"] = round(score, 3)
                chunk_copy["matched_terms"] = list(set(matched_terms))
                scored_chunks.append(chunk_copy)

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # Filter by threshold to ensure we don't return irrelevant notes
        relevant = [c for c in scored_chunks if c["score"] >= min_score_threshold]
        return relevant[:top_k]
