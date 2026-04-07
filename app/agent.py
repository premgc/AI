from app.llm import check_ollama_health, generate_response
from app.prompts import SMART_BANKING_PROMPT
from app.retriever import health_check as retriever_health_check
from app.retriever import search
from app.tools import TOOLS


SYSTEM_PROMPT = """
You are a smart banking assistant.

You can decide whether to call a tool or use retrieval-based answering.

Available tools:
- total_deposit
- total_withdrawal
- expense_breakdown
- daily_summary

Rules:
- If the user is clearly asking for one of the available tool actions,
  return ONLY the tool name.
- If the question needs transaction context or explanation, return ONLY: rag
- Do not add extra words.
"""


def run_agent(query: str) -> str:
    is_ollama_ok, ollama_msg = check_ollama_health()
    if not is_ollama_ok:
        return f"❌ {ollama_msg}"

    decision_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {query}\nAnswer:"
    decision = generate_response(decision_prompt).strip().lower()

    if decision in TOOLS:
        return TOOLS[decision]()

    is_qdrant_ok, qdrant_msg = retriever_health_check()
    if not is_qdrant_ok:
        return f"❌ {qdrant_msg}"

    docs = search(query, limit=8)
    context = "\n\n".join(docs) if docs else "No matching data found."
    prompt = SMART_BANKING_PROMPT.format(context=context, question=query)
    return generate_response(prompt)