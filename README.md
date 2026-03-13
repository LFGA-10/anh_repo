UWERA_AI – Curriculum Data Layer
================================

This project stores the structured data needed for the UWERA AI tutor:

- A **curriculum graph** (trades → levels → modules → units → topics → subtopics).
- **Vector-ready text chunks** plus rich metadata for retrieval and filtering.

The raw curriculum content and source documents live in Google Drive:
- `https://drive.google.com/drive/folders/1T5mGrVrAdry3Rt-DIr0aUMM4Iiwrdhfo`

## Folder structure

- `curriculum_data/`
  - `graph_structure/` – JSON describing the curriculum hierarchy.
  - `vector_documents/` – plain-text chunks + metadata for embeddings.

### 1. Graph structure

Each trade and level has a `summary.json` describing its hierarchy.
Example path:

- `curriculum_data/graph_structure/AnimalHealth/L3/summary.json`

The JSON contains:

- Trade, level, academic year
- Modules (with IDs, names, hours, prerequisites)
- Units (with IDs, names, hours)
- Topics and subtopics (with learning outcomes and key deliverables)

### 2. Vector documents

Each learning resource in `curriculum_data/raw/...` is automatically split into small text chunks with metadata by the ingestion script.

Example generated paths (Animal Health L3):

- `curriculum_data/vector_documents/ANH/AHNRF302/notes/..._chunk_001.txt`
- `curriculum_data/vector_documents/ANH/AHNRF302/notes/..._metadata.json`

Each `*_metadata.json` file contains an array of objects with:

- `trade_id`, `trade_name`, `level_id`
- `module_id`, `module_name`
- `document_type` (`notes`, `past_exam`, `question_bank`, `supplementary`)
- `source_document`, `source_relpath`, `ingested_at`
- placeholders for `unit_id`, `topic_id` that can be filled later.

This structure lets ingestion scripts:

- Build a graph database from the `graph_structure` JSON.
- Build a vector database from the `vector_documents` chunks and metadata.

## How to run ingestion

1. Put raw documents under:
   - `curriculum_data/raw/<TradeName>/<Level>_curriculum/<MODULE_ID>-<Module Name>/<Notes|Past Exams|Question_Bank|Supplementary Materials>/`
2. Install Python dependencies:
   - `pip install -r requirements.txt`
3. Run the ingestion script, e.g. for Animal Health L3:
   - `python scripts/ingest_raw_to_vector.py --raw_root curriculum_data\raw\AnimalHealth\L3_curriculum --out_root curriculum_data\vector_documents --trade_id ANH --trade_name "Animal Health" --level_id L3`

Repeat step 3 for L4 and L5 by changing `--raw_root` and `--level_id`.

## Next steps

1. Fill in real curriculum information (units, topics, learning outcomes) for each trade/level in the corresponding `summary.json` files.
2. Optionally add simple mapping files so chunks can be tagged with `unit_id` / `topic_id`.

