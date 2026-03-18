from neo4j import GraphDatabase
from data_prep.config import settings
from data_prep.utils.logger import logger

class Neo4jClient:
    def __init__(self):
        if not all([settings.NEO4J_URI, settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD]):
            logger.warning("Neo4j credentials not fully provided. Client will not be functional.")
            self.driver = None
            return
            
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )

    def close(self):
        if self.driver:
            self.driver.close()

    def upsert_trade(self, trade_id: str, trade_name: str):
        query = "MERGE (t:Trade {id: $id}) SET t.name = $name RETURN t"
        self._run_query(query, {"id": trade_id, "name": trade_name})

    def upsert_level(self, level_id: str, trade_id: str):
        query = """
        MERGE (l:Level {id: $level_id})
        WITH l
        MATCH (t:Trade {id: $trade_id})
        MERGE (t)-[:HAS_LEVEL]->(l)
        RETURN l
        """
        self._run_query(query, {"level_id": level_id, "trade_id": trade_id})

    def upsert_module(self, module_id: str, module_name: str, level_id: str):
        query = """
        MERGE (m:Module {id: $module_id})
        SET m.name = $name
        WITH m
        MATCH (l:Level {id: $level_id})
        MERGE (l)-[:HAS_MODULE]->(m)
        RETURN m
        """
        self._run_query(query, {"module_id": module_id, "name": module_name, "level_id": level_id})

    def upsert_unit(self, unit_id: str, unit_name: str, module_id: str):
        query = """
        MERGE (u:Unit {id: $unit_id})
        SET u.name = $name
        WITH u
        MATCH (m:Module {id: $module_id})
        MERGE (m)-[:HAS_UNIT]->(u)
        RETURN u
        """
        self._run_query(query, {"unit_id": unit_id, "name": unit_name, "module_id": module_id})

    def _run_query(self, query: str, parameters: dict):
        if not self.driver:
            logger.error("Neo4j Driver not initialized.")
            return
        with self.driver.session() as session:
            try:
                session.run(query, parameters)
            except Exception as e:
                logger.error(f"Neo4j query error: {e}")
                raise

neo4j_client = Neo4jClient()
