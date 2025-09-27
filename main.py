from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import scrape, monitor, account

app = FastAPI(title="Lagibosan API (full-api)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape)
app.include_router(monitor)
app.include_router(account)

@app.get("/")
def root():
    return {"message": "Lagibosan API (full-api)", "endpoints": ["/scrape", "/monitor", "/account"]}
