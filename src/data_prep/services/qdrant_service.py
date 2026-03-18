from qdrant_client import QdrantClient as QClient
from qdrant_client.http import models
from data_prep.config import settings
from data_prep.utils.logger import logger
import uuid

class QdrantClient:
    def __init__(self):
        if settings.USE_LOCAL_STORAGE:
            logger.info("Using Qdrant LOCAL MODE (on-disk)")
            self.client = QClient(path="data/qdrant_local")
            return

        if not all([settings.QDRANT_URL, settings.QDRANT_API_KEY]):
            logger.warning("Qdrant credentials not fully provided. Client will not be functional.")
            self.client = None
            return

        self.client = QClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

    def ensure_collection(self, collection_name: str, vector_size: int = 1536):
        """
        Ensures a collection exists with the specified vector size (default for BGE-small).
        """
        if not self.client:
            return

        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            logger.info(f"Creating Qdrant collection: {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def upsert_chunk(self, collection_name: str, vector: list, payload: dict):
        if not self.client:
            return
            
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        return point_id

qdrant_client = QdrantClient()
