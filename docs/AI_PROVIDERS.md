# AI provider setup

Financial values and payment eligibility are computed by the deterministic backend. `backend/ai/providers.py` supplies mock, OpenAI, Gemini, Groq and OpenAI-compatible explanation adapters. Explanations can be disabled with `AI_PROVIDER=mock`. Optional provider credentials stay on the server. Provider output is text only and cannot update calculations or authorize payments. LLM text may still be inaccurate; the numeric analysis remains authoritative.
