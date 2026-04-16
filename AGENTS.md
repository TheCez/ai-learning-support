# AGENTS - Frontend App

## Mission Profile
AI Learning Support UI built with Flask for nursing education. Features include Onboarding, Course Learning, Quizzes, and an interactive audio-visual KI-Lehrer (AI Teacher).

## Current Implementation Status
- **Architecture:** Flask app (`app.py`), SQLAlchemy (`models.py`), AI services (`services.py`).
- **Audio (CRITICAL):** ElevenLabs integrated via proxy endpoints (`/api/tts-proxy`, `/api/stt`) for KI-Lehrer. **These proxies must remain untouched.**
- **AI/LLM:** Currently uses local Google Gemini SDK (`google-genai`) for KI-Professor, KI-Lehrer, and Quizzes. *This is deprecated and must be replaced.*
- **Upload:** Content Upload prototype exists but is not wired to our new RAG ingestion backend.

## Next Steps
Execute Full Backend Integration:
1. Remove `google-genai` SDK.
2. Wire document uploads and polling to the external `rag_api`.
3. Wire AI-Professor, KI-Lehrer (Presentation Mode), and Quizzes to the external `llm_api`.