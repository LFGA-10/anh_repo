from data_prep.config import settings
from data_prep.utils.logger import logger
from data_prep.services.openrouter_client import openrouter_client
from data_prep.services.neo4j_client import neo4j_client
from data_prep.services.qdrant_client import qdrant_client

def smoke_test():
    logger.info("Starting Service Smoke Test...")
    
    # Check Settings
    if not settings.OPEN_ROUTER_API_KEY:
        logger.error("❌ OPEN_ROUTER_API_KEY is missing from .env")
    else:
        logger.info("✅ OpenRouter API Key detected")
        
    # OpenRouter Client
    try:
        logger.info(f"Using Model: {openrouter_client.model}")
        logger.info("✅ OpenRouter Client initialized")
    except Exception as e:
        logger.error(f"❌ OpenRouter Client failure: {e}")

    # Neo4j Client
    if neo4j_client.driver:
        logger.info("✅ Neo4j Client initialized (Driver ready)")
    else:
        logger.warning("⚠️ Neo4j Client limited (check credentials)")

    # Qdrant Client
    if qdrant_client.client:
        logger.info("✅ Qdrant Client initialized")
    else:
        logger.warning("⚠️ Qdrant Client limited (check credentials)")

    logger.info("Smoke Test Complete.")

if __name__ == "__main__":
    smoke_test()
