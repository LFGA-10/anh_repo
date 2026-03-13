import utils.transport
import utils.session
import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def _norm_ws(s: str) -> str:
    s = re.sub(r"\r\n?", "\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _looks_like_heading(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    if len(line) < 4 or len(line) > 120:
        return False
    # Numbered headings: "1.", "1.2", "2.3.1", "UNIT 1", "CHAPTER 3"
    if re.match(r"^(\d+(\.\d+){0,4})[\)\.\-:]\s+\S", line, flags=re.I):
        return True
    if re.match(r"^(unit|chapter|lesson|module|topic)\s+\d+\b", line, flags=re.I):
        return True
    # ALL CAPS-ish (common in handouts)
    letters = re.findall(r"[A-Za-z]", line)
    if letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.85 and len(letters) >= 8:
            return True
    # Short title case, no trailing period
    if line[-1] not in ".;," and 4 <= len(line.split()) <= 12:
        # avoid sentences
        if not re.search(r"\b(is|are|was|were|have|has|had|will|shall|may)\b", line, flags=re.I):
            return True
    return False


def extract_headings(text: str, max_headings: int = 200) -> List[str]:
    text = _norm_ws(text)
    headings: List[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if _looks_like_heading(line):
            # de-dup with simple normalization
            line = re.sub(r"\s{2,}", " ", line)
            headings.append(line)
        if len(headings) >= max_headings:
            break
    # de-duplicate while preserving order
    seen = set()
    out = []
    for h in headings:
        key = h.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def read_some_chunks(module_dir: Path, doc_types: Iterable[str], max_files: int = 6, max_chars_per_file: int = 12000) -> List[Tuple[str, str]]:
    """
    Returns [(source_relpath, text_sample), ...] from chunk files for a module.
    We prefer notes + supplementary, then fall back to others.
    """
    results: List[Tuple[str, str]] = []
    for doc_type in doc_types:
        d = module_dir / doc_type
        if not d.exists():
            continue
        # pick metadata files (one per source doc), then read first few chunks for each
        meta_files = sorted(d.glob("*_metadata.json"))
        for mf in meta_files[:max_files]:
            try:
                items = json.loads(mf.read_text(encoding="utf-8"))
            except Exception:
                continue
            # keep only chunks that belong to the requested level (metadata includes level_id)
            items = [it for it in items if str(it.get("level_id", "")).strip().upper() == _TARGET_LEVEL_ID]
            if not items:
                continue
            # take first 3 chunks for this doc
            sample_parts: List[str] = []
            for it in items[:3]:
                cf = d / it["chunk_filename"]
                if cf.exists():
                    sample_parts.append(cf.read_text(encoding="utf-8", errors="ignore"))
            sample = _norm_ws("\n\n".join(sample_parts))[:max_chars_per_file]
            if sample:
                results.append((str(mf.relative_to(module_dir)).replace("\\", "/"), sample))
    return results


def infer_keywords(text: str, top_n: int = 20) -> List[str]:
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    stop = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "will",
        "shall",
        "into",
        "your",
        "their",
        "then",
        "than",
        "were",
        "been",
        "also",
        "such",
        "used",
        "using",
        "use",
        "over",
        "some",
        "more",
        "most",
        "between",
        "within",
        "about",
        "which",
        "when",
        "where",
        "what",
        "there",
        "these",
        "those",
        "because",
        "after",
        "before",
        "under",
        "into",
        "upon",
        "each",
        "other",
        "should",
        "must",
        "may",
        "might",
        "can",
        "could",
    }
    words = [w for w in words if w not in stop]
    c = Counter(words)
    return [w for (w, _n) in c.most_common(top_n)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vector_root", required=True, help="e.g. curriculum_data/vector_documents")
    ap.add_argument("--trade_id", required=True, help="e.g. ANH")
    ap.add_argument("--level_id", required=True, help="e.g. L3")
    ap.add_argument("--out_dir", required=True, help="e.g. curriculum_data/inferred_structure/ANH/L3")
    args = ap.parse_args()

    vector_root = Path(args.vector_root).resolve()
    trade_dir = vector_root / args.trade_id
    if not trade_dir.exists():
        raise SystemExit(f"trade not found under vector_root: {trade_dir}")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    module_dirs = [p for p in trade_dir.iterdir() if p.is_dir()]
    module_dirs.sort(key=lambda p: p.name.lower())

    # Prefer "notes" + "supplementary" for structure signals.
    preferred_doc_types = ["notes", "supplementary", "question_bank", "past_exam"]

    global _TARGET_LEVEL_ID
    _TARGET_LEVEL_ID = str(args.level_id).strip().upper()

    for module_dir in module_dirs:
        module_id = module_dir.name
        samples = read_some_chunks(module_dir, preferred_doc_types)
        if not samples:
            # No content for this level in this module directory.
            continue
        combined = "\n\n".join(s for _src, s in samples)
        headings = extract_headings(combined)
        keywords = infer_keywords(combined)

        out = {
            "trade_id": args.trade_id,
            "level_id": args.level_id,
            "module_id": module_id,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "source": {
                "type": "inferred_from_vector_chunks",
                "note": "This outline is automatically inferred from notes/supplementary/exams. It is NOT an official curriculum structure.",
                "samples_used": [{"from": src, "chars": len(txt)} for (src, txt) in samples],
            },
            "inferred": {
                "headings": headings,
                "keywords": keywords,
            },
        }

        (out_dir / f"{module_id}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

