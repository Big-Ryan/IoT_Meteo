from fastapi import APIRouter
from app.models import CapteurCreate
from app.database import get_session, EXEC_PROFILE_WRITE, EXEC_PROFILE_READ

router = APIRouter()

@router.post("/capteurs/", summary="Créer un capteur")
def creer_capteur(capteur: CapteurCreate):
    session, _ = get_session()
    session.execute("""
        INSERT INTO capteurs (sensor_id, quartier, latitude, longitude, actif)
        VALUES (%s, %s, %s, %s, %s)
    """, (capteur.sensor_id, capteur.quartier, capteur.latitude,
          capteur.longitude, capteur.actif),
    execution_profile=EXEC_PROFILE_WRITE)
    return {"message": "Capteur créé", "sensor_id": capteur.sensor_id}

@router.get("/capteurs/", summary="Lister tous les capteurs")
def lister_capteurs():
    session, _ = get_session()
    rows = session.execute(
        "SELECT * FROM capteurs",
        execution_profile=EXEC_PROFILE_READ
    )
    return [dict(row._asdict()) for row in rows]

@router.put("/capteurs/{sensor_id}", summary="Mettre à jour un capteur")
def modifier_capteur(sensor_id: str, actif: bool):
    session, _ = get_session()
    session.execute("""
        UPDATE capteurs SET actif = %s WHERE sensor_id = %s
    """, (actif, sensor_id),
    execution_profile=EXEC_PROFILE_WRITE)
    return {"message": f"Capteur {sensor_id} mis à jour"}

@router.delete("/capteurs/{sensor_id}", summary="Supprimer un capteur")
def supprimer_capteur(sensor_id: str):
    session, _ = get_session()
    session.execute(
        "DELETE FROM capteurs WHERE sensor_id = %s",
        (sensor_id,),
        execution_profile=EXEC_PROFILE_WRITE
    )
    return {"message": f"Capteur {sensor_id} supprimé"}