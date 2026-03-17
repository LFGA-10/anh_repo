import json
from openai import OpenAI
from data_prep.config import settings
from data_prep.utils.logger import logger

class OpenRouterClient:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPEN_ROUTER_API_KEY,
        )
        self.model = settings.OPEN_ROUTER_MODEL

    def clean_curriculum_text(self, raw_text: str, module_context: str) -> dict:
        """
        Cleans raw document text and extracts a structured curriculum hierarchy.
        """
        system_prompt = (
            "You are an expert curriculum data scientist working with sensitive government educational data. "
            "Your task is to take raw text (from PDF/DOCX OCR) and return a CLEANED, STRUCTURED version. "
            "\n\nRULES:\n"
            "1. DO NOT alter any educational facts, dates, or names. This is sensitive data.\n"
            "2. Fix parsing artifacts, weird characters, and formatting inconsistencies.\n"
            "3. Identify the hierarchy: Modules -> Units -> Topics -> Subtopics.\n"
            "4. Return strictly valid JSON.\n"
            f"Context: {module_context}"
        )

        user_content = (
            "Please clean and structure the following text. "
            "Identify units and topics clearly.\n\n"
            f"RAW TEXT:\n{raw_text[:8000]}"  # Limit context for now
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
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error during OpenRouter inference: {e}")
            raise

openrouter_client = OpenRouterClient()
