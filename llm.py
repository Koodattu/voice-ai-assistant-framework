import requests
from config import LLM_API_URL, LLM_MODEL, OLLAMA_JSON_SCHEMA
from logger import logger

class LLMModule:
    def generate_response(prompt: str) -> str:
        """
        Sends a prompt to the LLM and retrieves the response.
        """
        logger.debug("LLMModule: AI is now thinking.")

        try:
            payload = {
                "prompt": prompt,
                "model": LLM_MODEL,
                "stream": False
            }
            logger.info("LLMModule: Sending prompt to LLM.")
            logger.debug(f"LLMModule: Payload: {payload}")
            response = requests.post(LLM_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            ai_response = data.get("response", "")
            logger.debug(f"LLMModule: Received response: {ai_response}")
        except requests.exceptions.RequestException as e:
            logger.error(f"LLMModule: Error communicating with LLM API: {e}")
            ai_response = "(Error retrieving response)"
        except KeyError:
            logger.error("LLMModule: Unexpected response format from LLM API.")
            ai_response = "(Error retrieving response)"
        finally:
            logger.debug("LLMModule: AI has stopped thinking.")

        return ai_response

    def generate_json_response(prompt: str) -> dict:
        """
        Sends a prompt to the LLM in JSON mode.
        Expects the "response" field to contain valid JSON.
        """
        payload = {
            "model": LLM_MODEL,
            "prompt": prompt,
            # Enable Ollama's JSON or structured output
            "format": {
                "type": "object",
                "properties": OLLAMA_JSON_SCHEMA["properties"],
                "required": OLLAMA_JSON_SCHEMA["required"]
            },
            "stream": False
        }
        logger.info("LLMModule: Sending JSON prompt to LLM.")
        logger.debug(f"LLMModule: Payload: {payload}")

        try:
            response = requests.post(LLM_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            # The "response" field in the JSON is the model’s raw string.
            # It should be a JSON string we can parse again.
            raw_json_str = data.get("response", "{}").strip()
            logger.debug(f"LLMModule: Raw JSON string from LLM: {raw_json_str}")

            # Attempt to parse the JSON.
            # If the model returns invalid JSON, handle it gracefully.
            import json
            parsed = json.loads(raw_json_str)
            return parsed

        except requests.exceptions.RequestException as e:
            logger.error(f"LLMModule: Error communicating with LLM API: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"LLMModule: Unexpected/invalid JSON response: {e}")

        # Fallback
        return {
            "wantsToSpeak": False,
            "reply": "(Error retrieving JSON)",
            "internalMonologue": ""
        }