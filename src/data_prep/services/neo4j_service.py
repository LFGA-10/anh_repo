import json
from pathlib import Path
from neo4j import GraphDatabase
from data_prep.config import settings
from data_prep.utils.logger import logger

class JsonGraphClient:
    """
    Serverless fallback for Neo4j. Stores the curriculum graph in a JSON file.
    """
    def __init__(self, storage_path: str = "data/curriculum_graph.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {"trades": {}, "levels": {}, "modules": {}, "units": {}, "relationships": []}

    def _save(self):
        self.storage_path.write_text(json.dumps(self.data, indent=2))

    def upsert_trade(self, trade_id: str, trade_name: str):
        self.data["trades"][trade_id] = {"id": trade_id, "name": trade_name}
        self._save()

    def upsert_level(self, level_id: str, trade_id: str):
        self.data["levels"][level_id] = {"id": level_id, "trade_id": trade_id}
        self.data["relationships"].append({"from": trade_id, "to": level_id, "type": "HAS_LEVEL"})
        self._save()

    def upsert_module(self, module_id: str, module_name: str, level_id: str):
        self.data["modules"][module_id] = {"id": module_id, "name": module_name, "level_id": level_id}
        self.data["relationships"].append({"from": level_id, "to": module_id, "type": "HAS_MODULE"})
        self._save()

    def upsert_unit(self, unit_id: str, unit_name: str, module_id: str):
        self.data["units"][unit_id] = {"id": unit_id, "name": unit_name, "module_id": module_id}
        self.data["relationships"].append({"from": module_id, "to": unit_id, "type": "HAS_UNIT"})
        self._save()

class Neo4jClient:
    def __init__(self):
        if settings.USE_LOCAL_STORAGE:
            logger.info("Using LOCAL GRAPH MODE (JSON surrogate)")
            self.local_client = JsonGraphClient()
            self.driver = None
            return

        self.local_client = None
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
        if self.local_client:
            return self.local_client.upsert_trade(trade_id, trade_name)
        query = "MERGE (t:Trade {id: $id}) SET t.name = $name RETURN t"
        self._run_query(query, {"id": trade_id, "name": trade_name})

    def upsert_level(self, level_id: str, trade_id: str):
        if self.local_client:
            return self.local_client.upsert_level(level_id, trade_id)
        query = """
        MERGE (l:Level {id: $level_id})
        WITH l
        MATCH (t:Trade {id: $trade_id})
        MERGE (t)-[:HAS_LEVEL]->(l)
        RETURN l
        """
        self._run_query(query, {"level_id": level_id, "trade_id": trade_id})

    def upsert_module(self, module_id: str, module_name: str, level_id: str):
        if self.local_client:
            return self.local_client.upsert_module(module_id, module_name, level_id)
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
        if self.local_client:
            return self.local_client.upsert_unit(unit_id, unit_name, module_id)
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
