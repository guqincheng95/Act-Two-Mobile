from fastapi import FastAPI

app = FastAPI(
    title="Act-Two-Mobile API",
    version="0.0.1",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
