import random
import time
import sys
import requests
from datetime import datetime, date, timezone
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, ConsistencyLevel
from cassandra.io.twistedreactor import TwistedConnection
from cassandra.query import BatchStatement

QUARTIERS = [
    {"id": "SENSOR_AKWA",      "nom": "Akwa",      "lat": 4.0511, "lon": 9.7085},
    {"id": "SENSOR_BONANJO",   "nom": "Bonanjo",   "lat": 4.0469, "lon": 9.6966},
    {"id": "SENSOR_DEIDO",     "nom": "Deido",     "lat": 4.0631, "lon": 9.7192},
    {"id": "SENSOR_BEPANDA",   "nom": "Bepanda",   "lat": 4.0756, "lon": 9.7300},
    {"id": "SENSOR_MAKEPE",    "nom": "Makepe",    "lat": 4.0850, "lon": 9.7450},
    {"id": "SENSOR_NEWBELL",   "nom": "New Bell",  "lat": 4.0600, "lon": 9.7100},
    {"id": "SENSOR_BONAPRISO", "nom": "Bonapriso", "lat": 4.0420, "lon": 9.7020},
    {"id": "SENSOR_LOGBABA",   "nom": "Logbaba",   "lat": 4.0300, "lon": 9.7600},
    {"id": "SENSOR_CITE_SIC",  "nom": "Cite SIC",  "lat": 4.0700, "lon": 9.7250},
    {"id": "SENSOR_KOTTO",     "nom": "Kotto",     "lat": 4.0900, "lon": 9.7550},
]

BASE_URL = "http://127.0.0.1:8000/api"
INTERVALLE_SECONDES = 2

PROFILS = {
    "Akwa":      {"temp_base": 28.5, "hum_base": 78},
    "Bonanjo":   {"temp_base": 27.8, "hum_base": 75},
    "Deido":     {"temp_base": 29.2, "hum_base": 80},
    "Bepanda":   {"temp_base": 30.1, "hum_base": 82},
    "Makepe":    {"temp_base": 29.5, "hum_base": 79},
    "New Bell":  {"temp_base": 31.0, "hum_base": 85},
    "Bonapriso": {"temp_base": 27.5, "hum_base": 73},
    "Logbaba":   {"temp_base": 30.5, "hum_base": 83},
    "Cite SIC":  {"temp_base": 29.8, "hum_base": 81},
    "Kotto":     {"temp_base": 30.2, "hum_base": 84},
}

# Connexion directe Cassandra
class DockerAddressTranslator:
    def translate(self, addr):
        return '127.0.0.1'

def get_session():
    profile = ExecutionProfile(
        load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
        consistency_level=ConsistencyLevel.QUORUM
    )
    cluster = Cluster(
        contact_points=['127.0.0.1'],
        port=9042,
        connection_class=TwistedConnection,
        execution_profiles={EXEC_PROFILE_DEFAULT: profile},
        address_translator=DockerAddressTranslator(),
        connect_timeout=15
    )
    return cluster, cluster.connect('meteo_douala')

def gen_mesure(capteur):
    profil = PROFILS.get(capteur["nom"], {"temp_base": 29, "hum_base": 80})
    heure = datetime.now().hour
    if 6 <= heure <= 14:
        variation = (heure - 6) * 0.4
    elif 14 < heure <= 20:
        variation = (20 - heure) * 0.3
    else:
        variation = -1.5
    return (
        capteur["id"],
        date.today(),
        datetime.now(timezone.utc),
        capteur["nom"],
        round(profil["temp_base"] + variation + random.uniform(-1.5, 1.5), 2),
        round(profil["hum_base"] + random.uniform(-5, 5), 2),
        round(random.uniform(1008.0, 1015.0), 2)
    )

# Mode injection massive directe
def injection_massive(nb_mesures=50000, batch_size=50):
    print(f"Connexion a Cassandra...", flush=True)
    cluster, session = get_session()
    print(f"Connecte ! Injection de {nb_mesures} mesures (batch={batch_size})...\n", flush=True)

    prepared = session.prepare("""
        INSERT INTO mesures_capteurs
        (sensor_id, date, timestamp, quartier, temperature, humidite, pression)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)

    debut = time.time()
    erreurs = 0
    inserees = 0

    while inserees < nb_mesures:
        taille = min(batch_size, nb_mesures - inserees)
        batch = BatchStatement(consistency_level=ConsistencyLevel.QUORUM)
        for _ in range(taille):
            capteur = random.choice(QUARTIERS)
            batch.add(prepared, gen_mesure(capteur))
        try:
            session.execute(batch)
            inserees += taille
        except Exception as e:
            erreurs += 1

        if inserees % 5000 == 0 or inserees == nb_mesures:
            elapsed = time.time() - debut
            vitesse = inserees / elapsed if elapsed > 0 else 0
            print(
                f"  {inserees:>6}/{nb_mesures} | "
                f"{vitesse:>6.0f} lignes/s | "
                f"erreurs: {erreurs}",
                flush=True
            )

    elapsed = time.time() - debut
    print(f"\nInjection terminee !", flush=True)
    print(f"  Total   : {inserees} mesures", flush=True)
    print(f"  Temps   : {elapsed:.1f}s", flush=True)
    print(f"  Vitesse : {inserees/elapsed:.0f} lignes/s", flush=True)
    print(f"  Erreurs : {erreurs}", flush=True)
    cluster.shutdown()

# Mode temps réel via API
def creer_capteurs_api():
    print("Creation des capteurs...", flush=True)
    for q in QUARTIERS:
        try:
            r = requests.post(f"{BASE_URL}/capteurs/", json={
                "sensor_id": q["id"], "quartier": q["nom"],
                "latitude": q["lat"], "longitude": q["lon"], "actif": True
            })
            print(f"  {q['nom']:<15} : {r.status_code}", flush=True)
        except Exception as e:
            print(f"  Erreur {q['nom']} : {e}", flush=True)
    print("Capteurs crees !\n", flush=True)

def mode_temps_reel():
    creer_capteurs_api()
    print(f"Mode temps reel demarre ({INTERVALLE_SECONDES}s entre cycles)", flush=True)
    print("CTRL+C pour arreter\n", flush=True)
    compteur = 0
    try:
        while True:
            for capteur in QUARTIERS:
                profil = PROFILS[capteur["nom"]]
                try:
                    requests.post(f"{BASE_URL}/mesures/", json={
                        "sensor_id":   capteur["id"],
                        "quartier":    capteur["nom"],
                        "temperature": round(profil["temp_base"] + random.uniform(-1.5, 1.5), 2),
                        "humidite":    round(profil["hum_base"]  + random.uniform(-5, 5), 2),
                        "pression":    round(random.uniform(1008.0, 1015.0), 2)
                    }, timeout=3)
                except Exception:
                    pass
            compteur += len(QUARTIERS)
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"{len(QUARTIERS)} mesures | Total: {compteur}",
                flush=True
            )
            time.sleep(INTERVALLE_SECONDES)
    except KeyboardInterrupt:
        print(f"\nArret. {compteur} mesures envoyees.", flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "massif":
        nb = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
        injection_massive(nb)
    else:
        mode_temps_reel()