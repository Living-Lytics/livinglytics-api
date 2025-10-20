from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Living Lytics API",
    description="Analytics engine and data integration service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Living Lytics API",
        "status": "active",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/analytics")
async def get_analytics():
    return {
        "data": [],
        "message": "Analytics endpoint ready"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
