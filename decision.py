from typing import List, Literal
from pydantic import BaseModel, Field
import json, os
import google.genai as genai
from typing import Optional, Dict, Any

AllowedFn = Literal[
    "get_financial_data",
    "calculate_roi",
    "apply_inflation_adjustment",
    "generate_chart",
]

class Step(BaseModel):
    function_name: AllowedFn
    parameters: Dict[str, Any] = Field(default_factory=dict)

class DecisionInput(BaseModel):
    perception: Dict[str, Any]
    preferences: Dict[str, Any] = Field(default_factory=dict)

class DecisionOutput(BaseModel):
    next_step: Optional[Step] = None
    done: bool = False
    rationale: Optional[str] = None

def decide_next_step(di: DecisionInput, context: Dict[str, Any], executed_steps: list[Step]) -> DecisionOutput:
    """
    Returns the next step (Step) as a Pydantic object, given:
    - perception & preferences (DecisionInput)
    - current context
    - already executed steps
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    executed_fn_names = [s.function_name for s in executed_steps]

    prompt_v1 = f"""
You are a finance decision planner. Suggest **only the next safe tool call** 
based on current context & already executed steps.

Allowed functions: get_financial_data(symbol, period), calculate_roi(revenue, investment),
apply_inflation_adjustment(values, rate), generate_chart(data, type)

Context: {json.dumps(context, ensure_ascii=False)}
Executed steps: {json.dumps(executed_fn_names, ensure_ascii=False)}
Perception: {json.dumps(di.perception, ensure_ascii=False)}
Preferences: {json.dumps(di.preferences, ensure_ascii=False)}

Rules:
1. Return only one next step at a time.
2. Respect dependencies: revenue/investment → ROI → inflation → chart.
3. If the user or perception mentions **multiple periods (e.g., "Q1_2024 and Q2_2024 or two quarters")**, treat each period as a **separate get_financial_data step**.
   - Example: if perception.extracted_periods = ["Q1_2024","Q2_2024"], then plan get_financial_data(..., "Q1_2024") first, then "Q2_2024".
4. Skip steps whose outputs exist in context.
5. Only include parameters resolvable from context/perception.
6. Return STRICT JSON: {{ "function_name": "...", "parameters": {{...}} }}
7. If all steps completed, return {{}} (empty object).
"""

    prompt = f"""
You are a **Finance Decision Planner AI**.

Your task is to suggest **only the next safe and logically required tool call**
based on the current context, user perception, preferences, and previously executed steps.

---

### 🔹 Allowed functions
- get_financial_data(symbol, period)
- calculate_roi(revenue, investment)
- apply_inflation_adjustment(values, rate)
- generate_chart(data, type)

---

### 🔹 Inputs
Context: {json.dumps(context, ensure_ascii=False)}
Executed steps: {json.dumps(executed_fn_names, ensure_ascii=False)}
Perception: {json.dumps(di.perception, ensure_ascii=False)}
Preferences: {json.dumps(di.preferences, ensure_ascii=False)}

---

### 🔹 Reasoning Rules
1. **Sequential Dependency Logic**
- Order: get_financial_data → calculate_roi → apply_inflation_adjustment → generate_chart
- Do not skip intermediate steps.
- If a dependency’s output is already in context, skip that step and move forward.

2. **Multi-period Handling**
If the user or perception mentions **multiple periods (e.g., "Q1_2024 and Q2_2024 or two quarters")**, treat each period as a **separate get_financial_data step**.
   - Example: if perception.extracted_periods = ["Q1_2024","Q2_2024"], then plan get_financial_data(..., "Q1_2024") first, then "Q2_2024".

3. **Parameter Resolution**
- Only include parameters that can be resolved from perception, preferences, or context.
- If a parameter cannot be resolved confidently, return the original name as a placeholder.

4. **Internal Self-Checks**
- Before finalizing your decision, verify that:
    - The suggested step’s prerequisites exist or will be produced by prior steps.
    - The step does not duplicate any already executed function.
- If uncertain or conflicting information exists, mention `"confidence": "low"` in output.

5. **Reasoning Type Awareness**
- In your internal reasoning (not output), classify your logic as one of:
    - “dependency reasoning” (step sequencing)
    - “lookup reasoning” (retrieving existing context)
    - “temporal reasoning” (multi-period inference)

6. **Error Handling and Fallbacks**
- If no valid next step can be determined, return:
    ```json
    {{ "function_name": null, "parameters": {{}}, "reason": "no further steps or missing data", "confidence": "low" }}
    ```
- Never hallucinate function names or parameters.
- Always prefer returning an empty or null step over guessing.

---

### 🔹 Output Format (STRICT)
Return **only one JSON object** with no text outside it.
Return STRICT JSON: {{ "function_name": "...", "parameters": {{...}} }}
If all steps completed, return {{}} (empty object).
"""

    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = resp.text.strip()
        if "```json" in text:
            text = text.split("```json",1)[1].split("```",1)[0].strip()
        elif text.startswith("```"):
            text = text.strip("`")
        data = json.loads(text)
        
        if not data or "function_name" not in data:
            return DecisionOutput(done=True, rationale="All steps completed")

        step = Step(function_name=data["function_name"], parameters=data.get("parameters", {}))
        return DecisionOutput(next_step=step, done=False, rationale="Next actionable step")
    
    except Exception as e:
        return DecisionOutput(done=True, rationale=f"LLM decision failed: {e}")
