# Financial Data Analyst JSON Interpreter — README

A production-ready, evaluation-friendly prompt that converts natural-language finance questions into a **strict JSON plan** of function calls. Designed to maximize step-by-step reasoning, enforce schema compliance, and support multi-turn workflows without leaking chain-of-thought.

## 🏗️ Modular Architecture

This application follows a modular architecture with clear separation of concerns:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User UI   │────▶│ Perception  │────▶│  Decision   │────▶│   Action    │
│  (main.py)  │     │ (LLM-based) │     │ (LLM-based) │     │ (Functions) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Memory Layer                               │
│                        (Persistence)                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 1. Perception Module (`perception.py`)
- **Purpose**: Interprets user queries and extracts key information
- **Input**: User's natural language query and preferences
- **Output**: Structured interpretation with extracted entities (symbols, periods, etc.)
- **Process**: Uses Gemini AI to analyze the query without planning function calls
- **Key Classes**: `UserPreferences`, `PerceptionInput`, `PerceptionOutput`

### 2. Decision Module (`decision.py`)
- **Purpose**: Determines the next action to take based on perception results
- **Input**: Perception output, current context, and previously executed steps
- **Output**: The next function to call with appropriate parameters
- **Process**: Uses Gemini AI to plan one step at a time with dependency awareness
- **Key Classes**: `Step`, `DecisionInput`, `DecisionOutput`

### 3. Action Module (`action.py`)
- **Purpose**: Executes the functions determined by the decision module
- **Input**: Function name and parameters
- **Output**: Results of the function execution
- **Process**: Contains implementations of financial tools and functions
- **Key Functions**: `get_financial_data()`, `calculate_roi()`, `apply_inflation_adjustment()`, `generate_chart()`
- **Key Classes**: `ActionInput`, `ActionOutput`

### 4. Memory Module (`memory.py`)
- **Purpose**: Persists data between interactions and maintains context
- **Input**: User goals, preferences, perception results, decisions, and context
- **Output**: Stored data for future reference
- **Process**: Saves and loads data to/from JSON files
- **Key Classes**: `MemoryRecord`, `MemoryState`

### 5. Main Application (`main.py`)
- **Purpose**: Orchestrates the entire workflow and provides the user interface
- **Process**:
  1. Collects user query and preferences through Streamlit UI
  2. Calls perception module to interpret the query
  3. Iteratively calls decision module to plan next steps
  4. Executes actions via the action module
  5. Updates and persists context via the memory module
  6. Displays results to the user

---

## ✨ What this prompt does
- **Interprets** a user's financial query into a **single JSON object**.
- **Plans** the required tool/function sequence (data fetch → adjust → compute → visualize).
- **Guards** against ambiguity with explicit **fallback rules** and **confidence tiers**.
- **Supports** multi-turn conversations by **reusing prior outputs**.
- **Passes** structured prompt-evaluation rubrics across nine criteria (reasoning, structure, separation, multi-turn, framing, self-checks, reasoning-type, fallbacks, clarity).

---

## ✅ At-a-Glance Schema
The assistant must output **only** a single JSON object with this exact shape:

```json
{
  "interpreted_request": "string",
  "function_calls": [
    {
      "function_name": "get_financial_data" | "calculate_roi" | "apply_inflation_adjustment" | "generate_chart",
      "parameters": {}
    }
  ],
  "confidence": "high" | "medium" | "low"
}
```

### Reasoning-Type Tag
Prefix `interpreted_request` with reasoning tags:
```
[reasoning: arithmetic + lookup + tool_use]
```
Allowed tags: `arithmetic`, `logic`, `lookup`, `planning`, `tool_use`, `comparison`, `aggregation`.

---

## 🧩 Authoritative Prompt (copy-paste)
> Use **one** of these depending on your runtime. The first is **Python f-string safe**.

### 1) Python f-string–SAFE version (double-brace escaping)
```python
prompt = f"""
You are a **financial data analyst assistant**. Interpret the user's query and output **ONLY JSON** that matches the schema below.

---

### INTERNAL REASONING (do not output)
1) Think step-by-step to plan the function call sequence.
2) Validate references and naming before emitting JSON.
3) Self-check: ensure schema conformity and reference availability; then emit.

---

### Output Schema (emit exactly this shape; no extra keys)
{{ 
  "interpreted_request": "string",
  "function_calls": [
    {{ 
      "function_name": "get_financial_data" | "calculate_roi" | "apply_inflation_adjustment" | "generate_chart",
      "parameters": {{}} 
    }} 
  ],
  "confidence": "high" | "medium" | "low"
}}

---

### Conventions
- Use only the listed function names.
- Reference previously produced values as "<SYMBOL>_<PERIOD>_<metric>" where:
  - SYMBOL ∈ {{AAPL, MSFT, AMZN}}
  - PERIOD ∈ {{Q1_2023, Q2_2023, Q3_2023, Q4_2023, Q1_2024, Q2_2024}}
  - metric ∈ {{revenue, investment, profit, expenses, ROI}}
- After inflation adjustment, append "_adjusted".
- You may include a "note" inside **parameters** to explain assumptions/uncertainties.
- You may include "output_keys" in **parameters** when returning multiple outputs.

---

### Reasoning-Type Tag (to satisfy reasoning-type awareness)
- Begin "interpreted_request" with a bracketed tag describing the dominant reasoning modes you use:
  - Allowed tags: arithmetic, logic, lookup, planning, tool_use, comparison, aggregation.
- Format: "[reasoning: arithmetic + lookup + tool_use] <plain-English interpretation>"

---

### Fallback & Error-Handling Policy (without changing schema)
1) **Ambiguity/Missing specifics** (e.g., period or symbol not provided):
   - Choose the safest, minimal interpretation needed to proceed.
   - If period(s) are missing:
     - For comparisons, default to the **most recent available periods in the allowed set**, in descending order (e.g., Q2_2024 then Q1_2024).
   - If symbol missing and clearly implied, pick the most likely; otherwise set "confidence" to "low".
   - Add a brief "note" inside the first relevant **parameters** explaining the assumption.
2) **Data unavailability**:
   - Always include needed `get_financial_data` calls first to produce required references.
   - If any referenced period isn’t in the allowed set, omit it and proceed with those that are; set "confidence" to "medium" and add a "note".
3) **Tool failure / unsupported step**:
   - If visualization is non-essential, omit `generate_chart` and still return computed steps; add a "note" and reduce "confidence".
4) **Inflation rate unspecified**:
   - Do **not** invent a rate. Proceed without inflation adjustment unless the user asks for it; or, if strongly implied, add a "note" requesting the rate and set "confidence" to "medium".
5) **Validation before emit**:
   - Ensure JSON is valid, keys are exact, references exist (or are produced earlier), and the sequence is executable.

---

### Example (for: "Compare ROI for AAPL for the last two quarters adjusted for inflation")
{{ 
  "interpreted_request": "[reasoning: arithmetic + lookup + comparison + tool_use] Compute inflation-adjusted ROI for AAPL for Q1_2024 and Q2_2024 and show a bar chart.",
  "function_calls": [
    {{ "function_name": "get_financial_data", "parameters": {{ "symbol": "AAPL", "period": "Q1_2024" }} }},
    {{ "function_name": "get_financial_data", "parameters": {{ "symbol": "AAPL", "period": "Q2_2024" }} }},
    {{ "function_name": "apply_inflation_adjustment", "parameters": {{ "values": ["AAPL_Q1_2024_revenue", "AAPL_Q1_2024_investment", "AAPL_Q2_2024_revenue", "AAPL_Q2_2024_investment"], "rate": 0.031 }} }},
    {{ "function_name": "calculate_roi", "parameters": {{ "revenue": "AAPL_Q1_2024_revenue_adjusted", "investment": "AAPL_Q1_2024_investment_adjusted" }} }},
    {{ "function_name": "calculate_roi", "parameters": {{ "revenue": "AAPL_Q2_2024_revenue_adjusted", "investment": "AAPL_Q2_2024_investment_adjusted" }} }}
  ],
  "confidence": "high"
}}

---

### 🔁 Conversation Continuation Rules
- In a multi-turn setting, you may receive new user input referring to prior results.
- Use previously emitted JSON keys (especially output references or output_keys) as context.
- Example:
  - Previous output: "AAPL_Q2_2024_ROI"
  - User: "Now chart that against MSFT."
  - Action: reuse "AAPL_Q2_2024_ROI" and add new `get_financial_data` for MSFT + `generate_chart`.
- Always append new `function_calls` to build on prior ones, preserving consistency.
- Keep prior reasoning tags and update the "interpreted_request" to reflect the new combined goal.

Now analyze the user's query carefully and generate the JSON.

User query: "{query}"
"""
```

---

## 📄 License & Version
- **License**: MIT (example; adapt to your org’s policy)
- **Prompt Version**: 1.0.0
- **Last updated**: 2025-10-11


---

## 🧮 Prompt Evaluation Score

Below is the latest evaluation result for this prompt when tested using the `evaluator_prompt`:

```json
{
  "explicit_reasoning": true,
  "structured_output": true,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": true,
  "internal_self_checks": true,
  "reasoning_type_awareness": true,
  "fallbacks": true,
  "overall_clarity": "Excellent structure, comprehensive rules, and clear examples. Promotes structured reasoning effectively."
}
```

✅ **Interpretation:**
- The prompt now **fully satisfies all nine evaluation criteria**.
- It supports **explicit reasoning**, **structured JSON**, **multi-turn planning**, **self-verification**, **reasoning-type tagging**, and **error fallback logic**.
- Rated as **"Excellent structure, comprehensive rules, and clear examples"** — meaning this is a production-ready, reasoning-optimized prompt.

---

## 🔄 Execution Flow

The application follows a systematic workflow for processing financial queries:

1. **User Input**
   - User enters a natural language financial query
   - Optional preferences can be specified (symbol, period, chart type, inflation adjustment)

2. **Perception Phase**
   - The query is sent to the perception module
   - Gemini AI interprets the query and extracts key information
   - No function planning occurs at this stage - only interpretation

3. **Decision-Action Loop**
   - The decision module determines the next step based on:
     - Perception results
     - Current context
     - Previously executed steps
   - Each step follows a logical dependency chain:
     - Data retrieval → Calculation → Adjustment → Visualization
   - For each step:
     - Parameters are resolved using context or LLM assistance
     - The action module executes the function
     - Results are added to the context
     - Memory is updated

4. **Memory Management**
   - Context is maintained throughout the session
   - Results from each step are stored for reference by future steps
   - User preferences and session history are persisted

5. **Result Presentation**
   - Results are displayed to the user through the Streamlit interface
   - Multiple results can be viewed through tabs
   - Detailed information is available through expandable sections

This modular approach provides several benefits:
- **Separation of concerns**: Each module has a specific responsibility
- **Maintainability**: Modules can be updated independently
- **Extensibility**: New functions can be added to the action module
- **Transparency**: The step-by-step process is visible to the user
- **Persistence**: Context is maintained between sessions

## 📊 Data Flow and Context Management

The application implements a sophisticated data flow pattern:

### Context Propagation
1. **Initial Context Loading**
   - On startup, the memory module loads any existing context
   - Default inflation rates are added to the context

2. **Context Enrichment**
   - Each successful action execution adds its results to the context
   - Complex nested results are flattened with prefixed keys
   - Example: `{'Q1_2024': {'revenue': 90.8}}` becomes `{'Q1_2024_revenue': 90.8}`

3. **Parameter Resolution**
   - The `resolve_params_with_llm()` function in main.py resolves parameters using:
     - Direct context matching
     - LLM-assisted resolution for ambiguous parameters
   - This ensures functions receive concrete values instead of references

4. **Context Persistence**
   - After each tool execution, the updated context is saved
   - This enables continuity between sessions and multi-turn interactions

### Reference Convention
The application uses a consistent reference convention for data:
- Format: `<SYMBOL>_<PERIOD>_<metric>`
- Example: `AAPL_Q1_2024_revenue`
- Adjusted values append `_adjusted` suffix
- This convention enables seamless data flow between modules

## 🧠 LLM Integration

The application leverages Gemini AI for two critical components:

### 1. Perception (Query Understanding)
- **Implementation**: The perception module uses Gemini to interpret natural language queries
- **Purpose**: Extract meaningful information without planning actions
- **Output**: Structured data including:
  - Interpreted request
  - Extracted symbols (e.g., AAPL, MSFT)
  - Extracted time periods (e.g., Q1_2024)
  - Flags for inflation adjustment and chart generation
  - Confidence level

### 2. Decision (Step Planning)
- **Implementation**: The decision module uses Gemini to determine the next action
- **Purpose**: Plan one step at a time based on dependencies and context
- **Process**:
  - Analyzes perception output, context, and executed steps
  - Follows dependency rules (data → calculation → adjustment → visualization)
  - Ensures prerequisites exist before suggesting a step
  - Avoids duplicate steps

### 3. Parameter Resolution
- **Implementation**: Main application uses Gemini to resolve ambiguous parameters
- **Purpose**: Map unresolved function parameters to correct context values
- **Process**:
  - Attempts direct context matching first
  - Falls back to LLM for semantic matching when needed
  - Preserves original values when no match is found

This LLM-powered approach enables:
- Natural language understanding without predefined patterns
- Dynamic planning based on context and dependencies
- Intelligent parameter resolution
- Adaptability to different query formulations
