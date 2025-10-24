import os
import google.genai as genai
from dotenv import load_dotenv


load_dotenv()

# Configure Gemini API
#api_key = os.environ.get("GEMINI_API_KEY")
api_key = os.getenv("GEMINI_API_KEY")
#print(api_key)
client = genai.Client(api_key=api_key)

input_prompt_old = f"""
You are a financial data analyst assistant. Interpret the user's query and output ONLY JSON.

Return exactly this JSON shape:

{{
  "interpreted_request": "string",
  "function_calls": [
    {{
      "function_name": "get_financial_data" | "calculate_roi" | "apply_inflation_adjustment" | "generate_chart",
      "parameters": {{ }}
    }}
  ]
}}

Conventions for parameters:
- Use exact function names listed above.
- For references to previously produced values, use string keys like:
  "<SYMBOL>_<PERIOD>_<metric>" where:
    - SYMBOL ∈ {{AAPL, MSFT, AMZN}}
    - PERIOD ∈ {{Q1_2023, Q2_2023, Q3_2023, Q4_2023, Q1_2024, Q2_2024}}
    - metric ∈ {{revenue, investment, profit, expenses, ROI}}
- After inflation adjustment, refer to "<ref>_adjusted" (e.g., "AAPL_Q1_2024_revenue_adjusted").
- If you need multiple adjusted values or ROIs, you can pass a list of references. Optionally include "output_keys" to name each output.

Example for: "Compare ROI for AAPL for the last two quarters adjusted for inflation":
{{
  "interpreted_request": "Compute inflation-adjusted ROI for AAPL for Q1_2024 and Q2_2024 and show a bar chart.",
  "function_calls": [
    {{"function_name":"get_financial_data","parameters":{{"symbol":"AAPL","period":"Q1_2024"}}}},
    {{"function_name":"get_financial_data","parameters":{{"symbol":"AAPL","period":"Q2_2024"}}}},
    {{"function_name":"apply_inflation_adjustment","parameters":{{"values":["AAPL_Q1_2024_revenue","AAPL_Q1_2024_investment","AAPL_Q2_2024_revenue","AAPL_Q2_2024_investment"],"rate":0.031}}}},
    {{"function_name":"calculate_roi","parameters":{{"revenue":"AAPL_Q1_2024_revenue_adjusted","investment":"AAPL_Q1_2024_investment_adjusted"}}}},
    {{"function_name":"calculate_roi","parameters":{{"revenue":"AAPL_Q2_2024_revenue_adjusted","investment":"AAPL_Q2_2024_investment_adjusted"}}}},
  ]
}}

Now generate the JSON for the user's query:
"""

input_prompt_old1 = f"""
You are a **financial data analyst assistant**. Your goal is to interpret the user's financial query logically and produce ONLY JSON output that conforms exactly to the specified schema.

---

### 🎯 Your Reasoning Process (INTERNAL, do not output)
1. **Think step-by-step** about what the user is asking.
   - Identify the requested operations (e.g., ROI, inflation adjustment, comparison, chart).
   - Determine which functions must be called in sequence to fulfill the request.
   - Verify that all inputs are available or derivable from previous steps.
2. **Check for internal consistency**:
   - Are all required parameters defined before they are referenced?
   - Do output keys follow naming conventions correctly?
   - If information is missing, make the best assumption and tag it in the `"interpreted_request"`.
3. **Self-verify** your JSON:
   - Ensure no syntax errors.
   - Ensure all keys and functions are valid.
   - If unsure, provide your best estimate but mark `"confidence": "low"` inside the JSON.

---

### 📤 Output Format
Return **only** a single JSON object with this shape:

{{
  "interpreted_request": "string",
  "function_calls": [
    {{
      "function_name": "get_financial_data" | "calculate_roi" | "apply_inflation_adjustment" | "generate_chart",
      "parameters": {{ }}
    }}
  ],
  "confidence": "high" | "medium" | "low"
}}

---

### 📘 Conventions for Parameters
- Use exact function names listed above.
- When referencing previously computed values, follow this convention:
  "<SYMBOL>_<PERIOD>_<metric>"
  where:
  - SYMBOL ∈ {{AAPL, MSFT, AMZN}}
  - PERIOD ∈ {{Q1_2023, Q2_2023, Q3_2023, Q4_2023, Q1_2024, Q2_2024}}
  - metric ∈ {{revenue, investment, profit, expenses, ROI}}
- After inflation adjustment, append `_adjusted` (e.g., "AAPL_Q1_2024_revenue_adjusted").
- For multiple adjusted or derived values, pass them as a list.
- Optionally include `"output_keys"` to name specific outputs.
- If a tool or function call cannot be inferred confidently, include a `"note"` key explaining the uncertainty.

---

### 💡 Example
User query: "Compare ROI for AAPL for the last two quarters adjusted for inflation"

{{
  "interpreted_request": "Compute inflation-adjusted ROI for AAPL for Q1_2024 and Q2_2024 and show a bar chart.",
  "function_calls": [
    {{"function_name": "get_financial_data", "parameters": {{"symbol": "AAPL", "period": "Q1_2024"}}}},
    {{"function_name": "get_financial_data", "parameters": {{"symbol": "AAPL", "period": "Q2_2024"}}}},
    {{"function_name": "apply_inflation_adjustment", "parameters": {{"values": ["AAPL_Q1_2024_revenue", "AAPL_Q1_2024_investment", "AAPL_Q2_2024_revenue", "AAPL_Q2_2024_investment"], "rate": 0.031}}}},
    {{"function_name": "calculate_roi", "parameters": {{"revenue": "AAPL_Q1_2024_revenue_adjusted", "investment": "AAPL_Q1_2024_investment_adjusted"}}}},
    {{"function_name": "calculate_roi", "parameters": {{"revenue": "AAPL_Q2_2024_revenue_adjusted", "investment": "AAPL_Q2_2024_investment_adjusted"}}}},
    {{"function_name": "generate_chart", "parameters": {{"values": ["AAPL_Q1_2024_ROI", "AAPL_Q2_2024_ROI"], "chart_type": "bar"}}}}
  ],
  "confidence": "high"
}}

---

Now, analyze the user's query carefully and generate the JSON.
"""

input_prompt_old2 = f"""
You are a finance decision planner. Suggest **only the next safe tool call** 
based on current context & already executed steps.

Allowed functions: get_financial_data(symbol, period), calculate_roi(revenue, investment),
apply_inflation_adjustment(values, rate), generate_chart(data, type)

Context: {{}}
Executed steps: {{}}
Perception: {{}}
Preferences: {{}}

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

input_prompt_new = f"""
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
Context: {{}}
Executed steps: {{}}
Perception: {{}}
Preferences: {{}}

---

### 🔹 Reasoning Rules
1. **Sequential Dependency Logic**
   - Order: get_financial_data → calculate_roi → apply_inflation_adjustment → generate_chart
   - Do not skip intermediate steps.
   - If a dependency’s output is already in context, skip that step and move forward.

2. **Multi-period Handling**
   - If the user or perception mentions multiple periods (e.g., “Q1_2024 and Q2_2024” or “two quarters of 2024”),
     treat each period as a **separate get_financial_data step**.
   - Example:
     - perception.extracted_periods = ["Q1_2024","Q2_2024"]
     - Then plan: get_financial_data(symbol, "Q1_2024") first, followed by "Q2_2024".

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

```json
{{
  "function_name": "...", 
  "parameters": {{ "param1": "...", "param2": "..." }},
  "confidence": "high"|"medium"|"low"
}}
"""

input_prompt = f"""
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
Context: {{}}
Executed steps: {{}}
Perception: {{}}
Preferences: {{}}

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


prompt = f"""You are a Prompt Evaluation Assistant.

You will receive a prompt written by a student. Your job is to review this prompt and assess how well it supports structured, step-by-step reasoning in an LLM (e.g., for math, logic, planning, or tool use).

Evaluate the prompt on the following criteria:

1. ✅ Explicit Reasoning Instructions  
   - Does the prompt tell the model to reason step-by-step?  
   - Does it include instructions like “explain your thinking” or “think before you answer”?

2. ✅ Structured Output Format  
   - Does the prompt enforce a predictable output format (e.g., FUNCTION_CALL, JSON, numbered steps)?  
   - Is the output easy to parse or validate?

3. ✅ Separation of Reasoning and Tools  
   - Are reasoning steps clearly separated from computation or tool-use steps?  
   - Is it clear when to calculate, when to verify, when to reason?

4. ✅ Conversation Loop Support  
   - Could this prompt work in a back-and-forth (multi-turn) setting?  
   - Is there a way to update the context with results from previous steps?

5. ✅ Instructional Framing  
   - Are there examples of desired behavior or “formats” to follow?  
   - Does the prompt define exactly how responses should look?

6. ✅ Internal Self-Checks  
   - Does the prompt instruct the model to self-verify or sanity-check intermediate steps?

7. ✅ Reasoning Type Awareness  
   - Does the prompt encourage the model to tag or identify the type of reasoning used (e.g., arithmetic, logic, lookup)?

8. ✅ Error Handling or Fallbacks  
   - Does the prompt specify what to do if an answer is uncertain, a tool fails, or the model is unsure?

9. ✅ Overall Clarity and Robustness  
   - Is the prompt easy to follow?  
   - Is it likely to reduce hallucination and drift?

---

Respond with a structured review in this format:
json
{{
  "explicit_reasoning": true,
  "structured_output": true,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": true,
  "internal_self_checks": false,
  "reasoning_type_awareness": false,
  "fallbacks": false,
  "overall_clarity": "Excellent structure, but could improve with self-checks and error fallbacks."
}}
Input Prompt: {input_prompt}
"""

try:
    # Generate content with Gemini
    #response = model.generate_content(prompt)
    response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
    print(prompt)
    response_text = response.text
    print(response_text)
except Exception as e:
    print(f"Error generating content: {str(e)}")