# action.py
from __future__ import annotations
from typing import Any, Dict
from pydantic import BaseModel, Field
# import your tool functions from wherever they live (same file or finance_tools.py)

# Dummy financial data
DUMMY_DATA = {
    "AAPL": {
        "Q1_2023": {
            "revenue": 94.8,  # billions
            "investment": 25.1,
            "profit": 24.2,
            "expenses": 70.6
        },
        "Q2_2023": {
            "revenue": 81.8,
            "investment": 23.8,
            "profit": 19.9,
            "expenses": 61.9
        },
        "Q3_2023": {
            "revenue": 89.5,
            "investment": 24.3,
            "profit": 22.6,
            "expenses": 66.9
        },
        "Q4_2023": {
            "revenue": 119.6,
            "investment": 27.5,
            "profit": 33.9,
            "expenses": 85.7
        },
        "Q1_2024": {
            "revenue": 90.8,
            "investment": 24.6,
            "profit": 23.1,
            "expenses": 67.7
        },
        "Q2_2024": {
            "revenue": 85.3,
            "investment": 24.1,
            "profit": 21.5,
            "expenses": 63.8
        }
    },
    "MSFT": {
        "Q1_2023": {
            "revenue": 52.7,
            "investment": 15.3,
            "profit": 18.3,
            "expenses": 34.4
        },
        "Q2_2023": {
            "revenue": 56.2,
            "investment": 16.1,
            "profit": 20.1,
            "expenses": 36.1
        },
        "Q3_2023": {
            "revenue": 56.5,
            "investment": 16.3,
            "profit": 20.5,
            "expenses": 36.0
        },
        "Q4_2023": {
            "revenue": 62.0,
            "investment": 17.5,
            "profit": 21.9,
            "expenses": 40.1
        },
        "Q1_2024": {
            "revenue": 61.9,
            "investment": 17.2,
            "profit": 21.8,
            "expenses": 40.1
        },
        "Q2_2024": {
            "revenue": 64.7,
            "investment": 18.1,
            "profit": 22.5,
            "expenses": 42.2
        }
    },
    "AMZN": {
        "Q1_2023": {
            "revenue": 127.4,
            "investment": 42.5,
            "profit": 3.2,
            "expenses": 124.2
        },
        "Q2_2023": {
            "revenue": 134.4,
            "investment": 44.8,
            "profit": 6.7,
            "expenses": 127.7
        },
        "Q3_2023": {
            "revenue": 143.1,
            "investment": 47.2,
            "profit": 9.9,
            "expenses": 133.2
        },
        "Q4_2023": {
            "revenue": 169.9,
            "investment": 52.3,
            "profit": 10.6,
            "expenses": 159.3
        },
        "Q1_2024": {
            "revenue": 143.3,
            "investment": 46.8,
            "profit": 10.4,
            "expenses": 132.9
        },
        "Q2_2024": {
            "revenue": 148.2,
            "investment": 48.1,
            "profit": 13.7,
            "expenses": 134.5
        }
    }
}

# Inflation rates (annual)
INFLATION_RATES = {
    "2023": 0.041,  # 4.1%
    "2024": 0.031   # 3.1%
}

def resolve_params(params: dict, context: dict) -> dict:
    """Replace references like 'AAPL_Q1_2024_revenue' with actual values from context."""
    resolved = {}
    for k, v in params.items():
        if isinstance(v, str) and v in context:
            resolved[k] = context[v]
        elif isinstance(v, list):
            resolved[k] = [context.get(x, x) for x in v]
        else:
            resolved[k] = v
    return resolved

# Define the available financial functions
def get_financial_data(symbol, period=None):
    """
    Fetch financial data for a given symbol and time period
    
    Args:
        symbol (str): Stock symbol (e.g., AAPL, MSFT)
        period (str, optional): Time period (e.g., Q1_2023, Q2_2024, or 2023, 2024)
        
    Returns:
        dict: Financial data for the specified symbol and period
    """
    if symbol not in DUMMY_DATA:
        return {"error": f"No data available for symbol {symbol}"}
    
    # If no period specified, return all data for the symbol
    if not period:
        return DUMMY_DATA[symbol]
    
    # If period is a year (e.g., 2023), return all quarters for that year
    if period in ["2023", "2024"]:
        year_data = {}
        for quarter, data in DUMMY_DATA[symbol].items():
            if period in quarter:
                year_data[quarter] = data
        return year_data
    
    # If period is a specific quarter
    if period in DUMMY_DATA[symbol]:
        return {period: DUMMY_DATA[symbol][period]}
    
    return {"error": f"No data available for period {period}"}


def calculate_roi(revenue, investment):
    """
    Calculate Return on Investment
    
    Args:
        revenue (float or list): Revenue amount(s)
        investment (float or list): Investment amount(s)
        
    Returns:
        float or list: ROI value(s) as percentage(s)
    """
    if isinstance(revenue, list) and isinstance(investment, list):
        if len(revenue) != len(investment):
            return {"error": "Revenue and investment lists must be the same length"}
        
        return [((r - i) / i) * 100 if i > 0 else 0 for r, i in zip(revenue, investment)]
    
    if isinstance(revenue, (int, float)) and isinstance(investment, (int, float)):
        return ((revenue - investment) / investment) * 100 if investment > 0 else 0
    
    return {"error": "Invalid input types for revenue and investment"}

def apply_inflation_adjustment(values, rate):
    """
    Adjust values for inflation
    
    Args:
        values (float or list): Value(s) to adjust
        rate (float): Inflation rate as decimal (e.g., 0.03 for 3%)
        
    Returns:
        float or list: Inflation-adjusted value(s)
    """
    if isinstance(values, list):
        return [value / (1 + rate) for value in values]
    
    if isinstance(values, (int, float)):
        return values / (1 + rate)
    
    return {"error": "Invalid input type for values"}


class ActionInput(BaseModel):
    function_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ActionOutput(BaseModel):
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""

def execute_action(ai: ActionInput) -> ActionOutput:
    try:
        if ai.function_name == "get_financial_data":
            res = get_financial_data(**ai.parameters)
        elif ai.function_name == "calculate_roi":
            res = calculate_roi(**ai.parameters)
        elif ai.function_name == "apply_inflation_adjustment":
            res = apply_inflation_adjustment(**ai.parameters)
        elif ai.function_name == "generate_chart":
            res = generate_chart(**ai.parameters)
        else:
            return ActionOutput(success=False, message=f"Unknown tool {ai.function_name}")
        return ActionOutput(success=True, result={ai.function_name: res}, message=f"{ai.function_name} executed.")
    except Exception as e:
        return ActionOutput(success=False, message=str(e))
