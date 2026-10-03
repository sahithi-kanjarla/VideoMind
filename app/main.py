from fastapi import FastAPI

app = FastAPI(
    title="VideoMind API",
    description="Multimodal knowledge ingestion and conversational retrieval backend",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "VideoMind API",
    }