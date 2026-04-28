from fastapi import APIRouter
from app.models import MesureCreate
from app.database import get_session, EXEC_PROFILE_WRITE, EXEC_PROFILE_READ
from datetime import datetime, date, timezone

router = APIRouter()

@router.post("/mesures/", summary="Insérer une mesure")
def inserer_mesure(mesure: MesureCreate):
    session, _ = get_session()
    now   = datetime.now(timezone.utc)
    today = date.today()
    session.execute("""
        INSERT INTO mesures_capteurs
        (sensor_id, date, timestamp, quartier, temperature, humidite, pression)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (mesure.sensor_id, today, now, mesure.quartier,
          mesure.temperature, mesure.humidite, mesure.pression),
    execution_profile=EXEC_PROFILE_WRITE)
    return {"message": "Mesure insérée", "timestamp": str(now)}

@router.get("/mesures/{sensor_id}", summary="Récupérer mesures d'un capteur")
def get_mesures(sensor_id: str, limit: int = 100):
    session, _ = get_session()
    today = date.today()
    rows = session.execute("""
        SELECT * FROM mesures_capteurs
        WHERE sensor_id = %s AND date = %s
        LIMIT %s
    """, (sensor_id, today, limit),
    execution_profile=EXEC_PROFILE_READ)
    return [dict(row._asdict()) for row in rows]

@router.get("/mesures/{sensor_id}/stats", summary="Statistiques d'un capteur")
def get_stats(sensor_id: str):
    session, _ = get_session()
    today = date.today()
    rows = session.execute("""
        SELECT temperature, humidite, pression
        FROM mesures_capteurs
        WHERE sensor_id = %s AND date = %s
    """, (sensor_id, today),
    execution_profile=EXEC_PROFILE_READ)
    data = list(rows)
    if not data:
        return {"message": "Aucune donnée disponible"}
    temps = [r.temperature for r in data]
    hums  = [r.humidite    for r in data]
    press = [r.pression    for r in data]
    return {
        "sensor_id":   sensor_id,
        "nb_mesures":  len(data),
        "temperature": {"min": min(temps), "max": max(temps), "moy": round(sum(temps)/len(temps), 2)},
        "humidite":    {"min": min(hums),  "max": max(hums),  "moy": round(sum(hums)/len(hums),   2)},
        "pression":    {"min": min(press), "max": max(press), "moy": round(sum(press)/len(press),  2)}
    }