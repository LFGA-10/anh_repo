import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")


def _read_text_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def extract_text(path: Path) -> str:
    """
    Extract text from supported documents.
    - .txt: read directly
    - .pdf/.docx: best-effort extraction using optional deps (pdfplumber, docx2txt)
    """
    ext = path.suffix.lower()
    if ext == ".txt":
        return _read_text_file(path)

    if ext == ".pdf":
        try:
            import pdfplumber  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "pdfplumber is required to extract PDF text. Install with: pip install pdfplumber"
            ) from e
        out: List[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    out.append(text)
        return "\n\n".join(out)

    if ext == ".docx":
        try:
            import docx2txt  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "docx2txt is required to extract DOCX text. Install with: pip install docx2txt"
            ) from e
        return docx2txt.process(str(path)) or ""

    raise RuntimeError(f"Unsupported file type: {path.name}")


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


def safe_print(msg: str) -> None:
    """
    Windows console can be cp1252; replace non-encodable chars.
    """
    enc = sys.stdout.encoding or "utf-8"
    sys.stdout.write(msg.encode(enc, errors="replace").decode(enc, errors="replace") + "\n")


@dataclass(frozen=True)
class PathInfo:
    trade_id: str
    trade_name: str
    level_id: str
    module_id: str
    module_name: str
    document_type: str


def parse_module_folder_name(name: str) -> Tuple[str, str]:
    """
    Example: 'AHNRF302-Ruminant farming' -> ('AHNRF302', 'Ruminant farming')
    """
    m = re.match(r"^\s*([A-Za-z0-9]+)\s*-\s*(.+?)\s*$", name)
    if not m:
        return _slug(name).upper(), name.strip()
    return m.group(1).strip(), m.group(2).strip()


def iter_source_docs(module_dir: Path) -> Iterable[Tuple[str, Path]]:
    """
    Yields (document_type, file_path) for supported docs inside:
    Notes/, Past Exams/, Question_Bank/, Supplementary Materials/
    """
    mapping = {
        "Notes": "notes",
        "Past Exams": "past_exam",
        "Question_Bank": "question_bank",
        "Supplementary Materials": "supplementary",
    }
    for folder_name, doc_type in mapping.items():
        folder = module_dir / folder_name
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() in {".pdf", ".docx", ".txt"}:
                yield doc_type, p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_root", required=True, help="e.g. curriculum_data/raw/AnimalHealth/L3_curriculum")
    ap.add_argument("--out_root", required=True, help="e.g. curriculum_data/vector_documents")
    ap.add_argument("--trade_id", required=True, help="e.g. ANH")
    ap.add_argument("--trade_name", required=True, help="e.g. Animal Health")
    ap.add_argument("--level_id", required=True, help="e.g. L3")
    ap.add_argument("--max_chars", type=int, default=1800)
    ap.add_argument("--overlap_chars", type=int, default=200)
    args = ap.parse_args()

    raw_root = Path(args.raw_root).resolve()
    out_root = Path(args.out_root).resolve()

    if not raw_root.exists():
        raise SystemExit(f"raw_root not found: {raw_root}")

    out_root.mkdir(parents=True, exist_ok=True)

    module_dirs = [p for p in raw_root.iterdir() if p.is_dir()]
    module_dirs.sort(key=lambda p: p.name.lower())

    for module_dir in module_dirs:
        module_id, module_name = parse_module_folder_name(module_dir.name)

        for doc_type, doc_path in iter_source_docs(module_dir):
            try:
                text = extract_text(doc_path)
            except Exception as e:
                safe_print(f"[skip] {doc_path} ({e})")
                continue

            chunks = chunk_text(text, max_chars=args.max_chars, overlap_chars=args.overlap_chars)
            if not chunks:
                safe_print(f"[skip] empty text: {doc_path}")
                continue

            dest_dir = out_root / args.trade_id / module_id / doc_type
            dest_dir.mkdir(parents=True, exist_ok=True)

            metadata_items = []
            base = _slug(doc_path.stem)
            for i, chunk in enumerate(chunks, start=1):
                chunk_filename = f"{base}_chunk_{i:03d}.txt"
                (dest_dir / chunk_filename).write_text(chunk + "\n", encoding="utf-8")

                metadata_items.append(
                    {
                        "chunk_filename": chunk_filename,
                        "trade_id": args.trade_id,
                        "trade_name": args.trade_name,
                        "level_id": args.level_id,
                        "module_id": module_id,
                        "module_name": module_name,
                        "unit_id": None,
                        "unit_name": None,
                        "topic_id": None,
                        "topic_name": None,
                        "document_type": doc_type,
                        "source_document": doc_path.name,
                        "source_relpath": str(doc_path.relative_to(raw_root)).replace("\\", "/"),
                        "ingested_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    }
                )

            meta_path = dest_dir / f"{base}_metadata.json"
            meta_path.write_text(json.dumps(metadata_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            safe_print(f"[ok] {doc_path.name} -> {len(chunks)} chunks ({meta_path.relative_to(out_root)})")


if __name__ == "__main__":
    main()

