# memory.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MEM_FILE = DATA_DIR / "memory.json"

class MemoryRecord(BaseModel):
    timestamp: str
    user_goal: str
    preferences: Dict[str, Any]
    perception: Dict[str, Any]
    decision: Dict[str, Any]

class MemoryState(BaseModel):
    preferences: Dict[str, Any] = Field(default_factory=dict)
    last_record: Optional[MemoryRecord] = None
    history: List[MemoryRecord] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)

def _load_state() -> MemoryState:
    if MEM_FILE.exists():
        try:
            return MemoryState(**json.loads(MEM_FILE.read_text()))
        except Exception:
            pass
    return MemoryState()

def _save_state(state: MemoryState) -> None:
    # In memory.py — replace MEM_FILE.write_text(...) with something like:
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2, ensure_ascii=False))

    #MEM_FILE.write_text(state.model_dump_json(indent=2))

def save_preferences(prefs: Dict[str, Any]) -> None:
    state = _load_state()
    state.preferences = prefs
    _save_state(state)

def load_preferences() -> Dict[str, Any]:
    return _load_state().preferences

def save_run(user_goal: str, preferences: Dict[str, Any],
             perception: Dict[str, Any], decision: Dict[str, Any]) -> None:
    state = _load_state()
    rec = MemoryRecord(
        timestamp=datetime.utcnow().isoformat(),
        user_goal=user_goal,
        preferences=preferences,
        perception=perception,
        decision=decision
    )
    state.last_record = rec
    state.history.append(rec)
    _save_state(state)

def load_last_run() -> Optional[MemoryRecord]:
    return _load_state().last_record

def save_context(context: Dict[str, Any]) -> None:
    """Persist the latest execution context (outputs of functions)."""
    state = _load_state()
    state.context = context
    _save_state(state)

def load_context() -> Dict[str, Any]:
    """Load the most recent context, or empty if none."""
    return _load_state().context

