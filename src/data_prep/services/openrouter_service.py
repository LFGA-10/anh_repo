import json
from openai import OpenAI
from data_prep.config import settings
from data_prep.utils.logger import logger
from data_prep.core.schemas import DocumentCleaningSchema

class OpenRouterClient:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPEN_ROUTER_API_KEY,
        )
        self.model = settings.OPEN_ROUTER_MODEL
        self.embed_model = "openai/text-embedding-3-small"

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Retrieves embeddings for a list of texts using OpenRouter.
        """
        try:
            response = self.client.embeddings.create(
                model=self.embed_model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error during OpenRouter embedding: {e}")
            raise

    def clean_curriculum_text(self, raw_text: str, module_context: str) -> DocumentCleaningSchema:
        """
        Cleans raw document text and extracts a structured curriculum hierarchy.
        Enforces a strict Pydantic-defined schema.
        """
        # Generate JSON schema for prompt
        schema_json = DocumentCleaningSchema.model_json_schema()
        
        system_prompt = (
            "You are an expert curriculum data scientist working with sensitive government educational data. "
            "Your task is to take raw text (from PDF/DOCX OCR) and return a CLEANED, STRUCTURED version. "
            "\n\nRULES:\n"
            "1. DO NOT alter any educational facts, dates, or names. This is sensitive data.\n"
            "2. Fix parsing artifacts, weird characters, and formatting inconsistencies.\n"
            "3. Identify the nested hierarchy: Units -> Topics -> Learning Outcomes.\n"
            "4. Return strictly valid JSON that matches the provided schema.\n\n"
            f"REQUIRED SCHEMA:\n{json.dumps(schema_json, indent=2)}\n\n"
            f"Context: {module_context}"
        )

        user_content = (
            "Please clean and structure the following text according to the schema.\n\n"
            f"RAW TEXT:\n{raw_text[:8000]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return DocumentCleaningSchema.model_validate_json(content)
        except Exception as e:
            logger.error(f"Error during OpenRouter inference or validation: {e}")
            raise

openrouter_client = OpenRouterClient()
