from fastapi import FastAPI

app = FastAPI(title="lab-server")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
