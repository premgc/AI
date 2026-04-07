from __future__ import annotations

from app.llm import check_ollama_health, generate_response
from app.prompts import SMART_BANKING_PROMPT
from app.retriever import health_check as retriever_health_check
from app.retriever import search
from app.tools import TOOLS


# =========================================================
# SYSTEM PROMPT (AGENT BRAIN)
# =========================================================
SYSTEM_PROMPT = """
You are a smart banking assistant.

You can either:
1. Call a tool
2. Use retrieved transaction data (rag)

Available tools:
- total_deposit
- total_withdrawal
- expense_breakdown
- daily_summary
- financial_insights
- filtered_summary

STRICT RULES:
- Return ONLY ONE of these:
  total_deposit
  total_withdrawal
  expense_breakdown
  daily_summary
  financial_insights
  filtered_summary
  rag

- DO NOT explain
- DO NOT add extra words

Routing rules:
- totals → total_deposit / total_withdrawal
- expenses / spending → expense_breakdown
- daily → daily_summary
- insights / losing money / recommendations → financial_insights
- date queries (last 7 days, this month, march, last 30 days) → filtered_summary
- anything else → rag
"""


# =========================================================
# DECISION ENGINE
# =========================================================
def decide_action(query: str) -> str:
    try:
        decision_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {query}\nAnswer:"
        decision = generate_response(decision_prompt).strip().lower()

        # Clean response
        decision = decision.replace("\n", "").replace(".", "").strip()

        return decision

    except Exception:
        return "rag"


# =========================================================
# TOOL EXECUTION
# =========================================================
def execute_tool(tool_name: str, query: str) -> str:
    try:
        if tool_name not in TOOLS:
            return None

        # Special case: filtered summary needs query
        if tool_name == "filtered_summary":
            return TOOLS[tool_name](query)

        return TOOLS[tool_name]()

    except Exception as e:
        return f"❌ Tool execution error: {e}"


# =========================================================
# RAG FALLBACK
# =========================================================
def run_rag(query: str) -> str:
    try:
        is_qdrant_ok, qdrant_msg = retriever_health_check()
        if not is_qdrant_ok:
            return f"❌ {qdrant_msg}"

        docs = search(query, limit=8)
        context = "\n\n".join(docs) if docs else "No matching data found."

        prompt = SMART_BANKING_PROMPT.format(
            context=context,
            question=query,
        )

        return generate_response(prompt)

    except Exception as e:
        return f"❌ RAG error: {e}"


# =========================================================
# MAIN AGENT FUNCTION
# =========================================================
def run_agent(query: str) -> str:
    # -----------------------------------------------------
    # 1. Health Check
    # -----------------------------------------------------
    is_ollama_ok, ollama_msg = check_ollama_health()
    if not is_ollama_ok:
        return f"❌ {ollama_msg}"

    # -----------------------------------------------------
    # 2. Decide action
    # -----------------------------------------------------
    decision = decide_action(query)

    # Safety fallback
    if decision not in TOOLS and decision != "rag":
        decision = "rag"

    # -----------------------------------------------------
    # 3. Execute tool
    # -----------------------------------------------------
    if decision in TOOLS:
        result = execute_tool(decision, query)

        # fallback if tool failed
        if not result:
            return run_rag(query)

        return result

    # -----------------------------------------------------
    # 4. Default → RAG
    # -----------------------------------------------------
    return run_rag(query)