import requests
from constants import LLM_API_URL, LLM_MODEL
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