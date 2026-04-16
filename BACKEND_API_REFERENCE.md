# BACKEND API REFERENCE (Frontend Contract)

The frontend must communicate with our two backend microservices via HTTP using the `requests` library. 

## 1. RAG API (Base URL: `http://localhost:8000/api/v1`)
Handles file ingestion and index readiness.
* **Upload PDF:** `POST /courses/{course_id}/documents`
    * **Payload:** `multipart/form-data` with `week` (int) and `file` (PDF).
    * **Returns:** `{"message": "...", "metadata": {"doc_id": "..."}}`
* **Check Readiness:** `GET /courses/{course_id}/documents/{doc_id}/ready`
    * **Returns:** `{"ready": true/false, "indexed_chunks": int}`. 
    * *Rule:* Frontend must poll this after upload. Do not allow AI generation until `ready == true`.
* **Images:** Image URLs returned by the LLM API will point to `http://localhost:8000/api/v1/images/...`. Render them natively using `<img src="...">`.

## 2. LLM API (Base URL: `http://localhost:8001`)
Handles all user-facing AI generation. **Do not call Gemini directly.**
* **Standard QA:** `POST /generate_answer`
    * **Payload:** JSON `{"course_id": "string", "query": "string"}`
    * **Returns:** JSON `{"answer": "string", "images": ["/api/v1/images/...", ...]}`
* **Quiz Generation:** `POST /generate_quiz`
    * **Payload:** JSON `{"course_id": "string"}`
    * **Returns:** JSON `{"quiz": [{"question": "...", "options": ["A", "B", "C", "D"], "answer_index": 0, "explanation": "..."}]}`
* **KI-Professor/KI-Lehrer Presentation:** `POST /generate_presentation`
    * **Payload:** JSON `{"course_id": "string", "query": "string"}`
    * **Returns:** JSON `{"spoken_text": "...", "slide": {"title": "...", "bullets": ["...", "..."]}, "images": ["/api/v1/images/...", ...]}`
    * *Rule:* Pass `spoken_text` to ElevenLabs TTS. Render `slide` and `images` on the screen.