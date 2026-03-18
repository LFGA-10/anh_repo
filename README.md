# UWERA AI – Curriculum Data Layer

This project implements a professional data preparation pipeline for the UWERA AI tutor. It transforms raw curriculum documents into a structured graph and searchable vector chunks using cloud-based databases and LLM-powered data cleaning.

## Key Features
- **Professional Structure**: Organized as a proper Python package (`src/data_prep`).
- **Cloud Infrastructure**: Integration with **Neo4j** (Graph) and **Qdrant** (Vector).
- **LLM Cleaning**: Automated text cleaning and hierarchy extraction via **OpenRouter** (Claude 3.5 Sonnet).
- **Local Embeddings**: Fast and efficient embedding generation using `FastEmbed`.

## Architecture Overview
1. **Extraction**: Raw text is extracted from PDF, DOCX, and TXT files in `data/RAW/`.
2. **LLM Refinement**: OpenRouter cleans the text, fixing OCR artifacts and identifying Units/Topics.
3. **Graph Population**: Curriculum hierarchy (Trade -> Level -> Module -> Unit) is synced to **Neo4j**.
4. **Vector Storage**: Cleaned text is chunked, embedded locally, and pushed to **Qdrant** with Neo4j relationship links.

## Project Structure
```text
src/data_prep/
├── cli/          # Entry points (ingest.py)
├── core/         # Orchestration logic (processor.py)
├── services/     # Cloud clients (OpenRouter, Neo4j, Qdrant)
└── utils/        # Document processing & Logging
```

## Setup & Configuration

1. **Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   OPEN_ROUTER_API_KEY="your_key"
   NEO4J_URI="bolt://..."
   NEO4J_USERNAME="neo4j"
   NEO4J_PASSWORD="password"
   QDRANT_URL="https://..."
   QDRANT_API_KEY="your_key"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the ingestion pipeline via the CLI:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 -m data_prep.cli.ingest \
    --raw_dir data/RAW/AnimalHealth/L3_curriculum \
    --trade_id ANH \
    --trade_name "Animal Health" \
    --level_id L3 \
    --module_id AHNRF302 \
    --module_name "Ruminant farming"
```

## Maintenance
- **Health Check**: Run `python3 src/data_prep/services/health_check.py` to verify service connectivity.
- **Tests**: Use `pytest` for automated verification.

