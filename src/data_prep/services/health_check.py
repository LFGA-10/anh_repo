from data_prep.config import settings
from data_prep.utils.logger import logger
from data_prep.services.openrouter_service import openrouter_client
from data_prep.services.neo4j_service import neo4j_client
from data_prep.services.qdrant_service import qdrant_client

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

    # Neo4j / Local Graph Client
    if neo4j_client.local_client:
        logger.info("✅ Local Graph Mode active (JSON surrogate)")
    elif neo4j_client.driver:
        try:
            with neo4j_client.driver.session() as session:
                result = session.run("RETURN 1").single()
                if result:
                    logger.info("✅ Neo4j Connection successful (Cloud ready)")
        except Exception as e:
            logger.error(f"❌ Neo4j Connection failure: {e}")
    else:
        logger.warning("⚠️ Graph service limited (check credentials or local mode)")

    # Qdrant Client
    if qdrant_client.client:
        try:
            logger.info("Checking Qdrant connectivity...")
            # Try to get collections
            collections = qdrant_client.client.get_collections()
            logger.info(f"✅ Qdrant Client initialized. Collections: {len(collections.collections)}")
        except Exception as e:
            logger.error(f"❌ Qdrant Connection failure: {e}")
    else:
        logger.warning("⚠️ Qdrant Client limited (check credentials)")

    logger.info("Smoke Test Complete.")

if __name__ == "__main__":
    smoke_test()
