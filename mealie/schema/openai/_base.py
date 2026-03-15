import json
import re
from typing import Self

from pydantic import BaseModel

from mealie.core.root_logger import get_logger

RE_NULLS = re.compile(r"[\x00\u0000]|\\u0000")

logger = get_logger()


class OpenAIBase(BaseModel):
    """
    Base class for OpenAI structured output schemas. These models are passed
    to OpenAI's response_format parameter with strict schema validation.
    """

    __doc__ = ""  # we don't want to include the docstring in the JSON schema

    @classmethod
    def _fix_json(cls, json_str: str) -> str:
        """
        Attempt to fix common JSON issues from LLM outputs.
        """
        # Fix missing commas between array elements (common LLM issue)
        # Pattern: "value"\n"value" or "value"\n  "value" (missing comma)
        json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
        
        # Fix missing commas between object properties
        # Pattern: "value"\n  "key": (missing comma before next key)
        json_str = re.sub(r'"\s*\n\s*"(\w+)":', '",\n"\1":', json_str)
        
        # Fix missing commas after numbers before next key
        # Pattern: 123\n  "key":
        json_str = re.sub(r'(\d)\s*\n\s*"(\w+)":', r'\1,\n"\2":', json_str)
        
        # Fix missing commas after closing braces/brackets before next element
        # Pattern: }\n  { or ]\n  [
        json_str = re.sub(r'}\s*\n\s*{', '},\n{', json_str)
        json_str = re.sub(r']\s*\n\s*\[', '],\n[', json_str)
        
        # Fix missing commas after closing brace before next key
        json_str = re.sub(r'}\s*\n\s*"(\w+)":', r'},\n"\1":', json_str)
        
        # Fix trailing commas before closing brackets/braces
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        return json_str

    @classmethod
    def _preprocess_response(cls, response: str | None) -> str:
        if not response:
            return ""

        response = re.sub(RE_NULLS, "", response)
        
        # Handle Gemini's markdown code blocks (```json...```)
        response = response.strip()
        if response.startswith('```json') and response.endswith('```'):
            # Remove ```json from start and ``` from end
            response = response[7:-3].strip()
        elif response.startswith('```') and response.endswith('```'):
            # Remove generic ``` from start and end
            response = response[3:-3].strip()
        
        # Try to fix common JSON issues
        response = cls._fix_json(response)
            
        return response

    @classmethod
    def _process_response(cls, response: str) -> Self:
        try:
            return cls.model_validate_json(response)
        except Exception as first_error:
            logger.debug(f"First parse attempt failed for {cls}. Trying additional fixes...")
            
            # Try more aggressive JSON fixing
            try:
                # Parse and re-serialize to fix formatting issues
                # First, try to extract just the JSON object/array
                json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', response)
                if json_match:
                    extracted = json_match.group(1)
                    extracted = cls._fix_json(extracted)
                    
                    # Try parsing the extracted and fixed JSON
                    try:
                        parsed = json.loads(extracted)
                        return cls.model_validate(parsed)
                    except json.JSONDecodeError:
                        pass
                
                logger.debug(f"Failed to parse OpenAI response as {cls}. Response: {response}")
                raise first_error
            except Exception:
                logger.debug(f"All parse attempts failed for {cls}. Response: {response}")
                raise first_error

    @classmethod
    def parse_openai_response(cls, response: str | None) -> Self:
        """
        Parse the OpenAI response into a class instance.
        """

        response = cls._preprocess_response(response)
        return cls._process_response(response)
