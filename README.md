# VideoMind

VideoMind's YouTube vertical slice loads an English YouTube transcript, indexes timestamped chunks with multilingual E5 and Chroma, reranks retrieval results with a CrossEncoder, and generates grounded answers with Gemini.

## Run locally

1. Install [uv](https://docs.astral.sh/uv/) and run `uv sync` from the repository root.
2. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.
3. Run `uv run uvicorn app.main:app --reload`.
4. Open `http://127.0.0.1:8000`.

Models are loaded once when the first video is loaded. Chroma data is persisted under `CHROMA_PATH` (defaults to `chroma/`).

## YouTube API

- `POST /api/youtube/load` with `{"url":"https://www.youtube.com/watch?v=..."}`
- `GET /api/youtube/{video_id}`
- `POST /api/chat/query` with `{"video_id":"...","question":"..."}`
- `GET /health`

The browser UI embeds the video and seeks in place when a source timestamp is selected. Video session state is in memory; persistent chat history and cross-restart loaded-video discovery are not included.
