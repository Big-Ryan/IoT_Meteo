from fastapi import FastAPI
from app.routes import capteurs, mesures, cql
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Météo IoT Douala",
    description="API de surveillance météo avec Apache Cassandra",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(capteurs.router, prefix="/api", tags=["Capteurs"])
app.include_router(mesures.router,  prefix="/api", tags=["Mesures"])
app.include_router(cql.router,      prefix="/api", tags=["CQL"])

@app.get("/")
def root():
    return {"message": "API Météo IoT Douala opérationnelle"}