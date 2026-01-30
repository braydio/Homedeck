from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from collector import collect

app = FastAPI(title="Homelab Health")

# Serve the HTML dashboard
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/api/health")
def health():
    return JSONResponse(collect())
