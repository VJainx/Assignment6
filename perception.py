# perception.py
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import json
import google.genai as genai
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env file

# finance-flavored prefs you’ll collect in main
class UserPreferences(BaseModel):
    name: Optional[str] = None
    preferred_symbol: Optional[str] = None           # e.g., AAPL/MSFT/AMZN
    preferred_period: Optional[str] = None           # e.g., Q2_2024
    preferred_chart: Optional[str] = None            # bar|line|pie
    want_inflation_adjustment: Optional[bool] = None # True/False

class PerceptionInput(BaseModel):
    system_prompt: str
    user_goal: str
    preferences: UserPreferences

class PerceptionOutput(BaseModel):
    interpreted_request: str
    extracted_symbols: List[str] = Field(default_factory=list)
    extracted_periods: List[str] = Field(default_factory=list)
    wants_inflation: Optional[bool] = None
    wants_chart: Optional[bool] = None
    confidence: Literal["high","medium","low"] = "medium"

def perceive(pi: PerceptionInput) -> PerceptionOutput:
    """
    Uses Gemini to INTERPRET the user's natural-language query.
    No function planning here—only interpretation & light extraction.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
{pi.system_prompt}

Task: Interpret the user's finance question and the preferences. DO NOT propose any function calls.
Return STRICT JSON with this schema (no extra keys):

{{
  "interpreted_request": "string",
  "extracted_symbols": ["AAPL"|"MSFT"|"AMZN"...],   // may be empty
  "extracted_periods": ["Q1_2024","Q2_2024", ...],  // may be empty
  "wants_inflation": true|false|null,
  "wants_chart": true|false|null,
  "confidence": "high"|"medium"|"low"
}}

Rules:
- Deduce inflation/chart wishes from wording if clearly implied; else null.
- If nothing explicit, leave arrays empty and booleans as null.

User query: "{pi.user_goal}"
Preferences: {pi.preferences.model_dump_json()}
Ensure that final interpretation aligns with both the query and preferences.
"""

    resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    text = resp.text.strip()

    # strip fences if model used ```json
    if "```json" in text:
        text = text.split("```json",1)[1].split("```",1)[0].strip()
    elif text.startswith("```"):
        text = text.strip("`")

    data = json.loads(text)
    return PerceptionOutput(**data)
