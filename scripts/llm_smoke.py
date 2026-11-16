"""One tiny real call to check your key and model work. Costs a fraction of a cent.

Run:  python scripts/llm_smoke.py
"""
from ketana_drishti.llm import ClaudeClient, LLMError

try:
    c = ClaudeClient(max_tokens=50)
    r = c.complete("Reply with one short word.", "Say hello.")
    print("model:", r.model)
    print("reply:", r.text.strip())
except LLMError as e:
    print("FAILED:", e)
