import re
from pathlib import Path
from typing import List, Optional
from fastembed import TextEmbedding
from data_prep.utils.logger import logger

def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".pdf":
        import pdfplumber
        out: List[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    out.append(text)
        return "\n\n".join(out)

    if ext == ".docx":
        import docx2txt
        return docx2txt.process(str(path)) or ""

    raise ValueError(f"Unsupported file type: {path.name}")

def chunk_text(text: str, max_chars: int = 1800, overlap_chars: int = 200) -> List[str]:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        if end < n:
            cut = text.rfind("\n\n", start, end)
            if cut != -1 and cut > start + int(max_chars * 0.5):
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap_chars)
    return chunks

class GhostEmbedding:
    """
    Local embedding generator using FastEmbed.
    Uses 'BAAI/bge-small-en-v1.5' by default (384 dims).
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        logger.info(f"Initializing embedding model: {model_name}")
        self.model = TextEmbedding(model_name=model_name)

    def generate(self, texts: List[str]) -> List[List[float]]:
        # FastEmbed returns a generator of numpy arrays
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

embedding_generator = GhostEmbedding()
