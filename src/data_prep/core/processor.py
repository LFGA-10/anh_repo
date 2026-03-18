from pathlib import Path
from data_prep.services.openrouter_service import openrouter_client
from data_prep.services.neo4j_service import neo4j_client
from data_prep.services.qdrant_service import qdrant_client
from data_prep.utils.document_utils import extract_text, chunk_text, embedding_generator
from data_prep.utils.logger import logger

class CurriculumProcessor:
    def __init__(self, collection_name: str = "curriculum_chunks"):
        self.collection_name = collection_name
        qdrant_client.ensure_collection(self.collection_name)

    def process_document(self, doc_path: Path, trade_id: str, trade_name: str, level_id: str, module_id: str, module_name: str):
        logger.info(f"Processing document: {doc_path.name}")
        
        # 1. Extract Text
        raw_text = extract_text(doc_path)
        
        # 2. LLM Cleaning & Structuring
        context = f"Trade: {trade_name} ({trade_id}), Level: {level_id}, Module: {module_name} ({module_id})"
        structured_data = openrouter_client.clean_curriculum_text(raw_text, context)
        
        cleaned_text = structured_data.cleaned_text
        hierarchy = structured_data.hierarchy
        
        # 3. Update Neo4j Graph
        neo4j_client.upsert_trade(trade_id, trade_name)
        neo4j_client.upsert_level(level_id, trade_id)
        neo4j_client.upsert_module(module_id, module_name, level_id)
        
        # Upsert Units and Topics found by LLM
        for unit in hierarchy.units:
            unit_id = f"{module_id}_{unit.id}"
            unit_name = unit.name
            neo4j_client.upsert_unit(unit_id, unit_name, module_id)
            
            # Here you could extend neo4j_client to support upserting topics/outcomes
            # for topic in unit.topics:
            #     ...
            
        # 4. Chunk & Embed Cleaned Text
        chunks = chunk_text(cleaned_text)
        if not chunks:
            logger.warning(f"No chunks for {doc_path.name}")
            return
            
        vectors = embedding_generator.generate(chunks)
        
        # 5. Push to Qdrant
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            payload = {
                "source": doc_path.name,
                "trade_id": trade_id,
                "module_id": module_id,
                "level_id": level_id,
                "chunk_index": i,
                "text": chunk,
            }
            qdrant_client.upsert_chunk(self.collection_name, vector, payload)
            
        logger.info(f"Successfully ingested {len(chunks)} chunks for {doc_path.name}")

processor = CurriculumProcessor()
