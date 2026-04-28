import csv
import os
import time
import psycopg2
from datetime import date, datetime, timezone
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, ConsistencyLevel
from cassandra.io.twistedreactor import TwistedConnection

# ─── Connexion Cassandra ───
class DockerAddressTranslator:
    def translate(self, addr):
        return '127.0.0.1'

def get_cassandra_session():
    profile = ExecutionProfile(
        load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
        consistency_level=ConsistencyLevel.ONE,
        request_timeout=60
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

# ─── Connexion PostgreSQL ───
def get_pg():
    return psycopg2.connect(
        host="localhost", port=5432,
        database="meteo_benchmark",
        user="postgres", password="postgreesql"
    )

# ─── Config ───
CAPTEURS = [
    "SENSOR_AKWA", "SENSOR_BONANJO", "SENSOR_DEIDO",
    "SENSOR_BEPANDA", "SENSOR_MAKEPE", "SENSOR_NEWBELL",
    "SENSOR_BONAPRISO", "SENSOR_LOGBABA", "SENSOR_CITE_SIC", "SENSOR_KOTTO"
]

COORDONNEES = {
    "Akwa":      {"lat": 4.0511, "lon": 9.7085},
    "Bonanjo":   {"lat": 4.0469, "lon": 9.6966},
    "Deido":     {"lat": 4.0631, "lon": 9.7192},
    "Bepanda":   {"lat": 4.0756, "lon": 9.7300},
    "Makepe":    {"lat": 4.0850, "lon": 9.7450},
    "New Bell":  {"lat": 4.0600, "lon": 9.7100},
    "Bonapriso": {"lat": 4.0420, "lon": 9.7020},
    "Logbaba":   {"lat": 4.0300, "lon": 9.7600},
    "Cite SIC":  {"lat": 4.0700, "lon": 9.7250},
    "Kotto":     {"lat": 4.0900, "lon": 9.7550},
}

OUTPUT_DIR = "powerbi_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Setup PostgreSQL ───
def setup_postgres_tables():
    pg = get_pg()
    cur = pg.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pb_mesures (
            id          SERIAL PRIMARY KEY,
            sensor_id   VARCHAR(50),
            date        DATE,
            timestamp   TIMESTAMP,
            quartier    VARCHAR(50),
            latitude    DOUBLE PRECISION,
            longitude   DOUBLE PRECISION,
            temperature DOUBLE PRECISION,
            humidite    DOUBLE PRECISION,
            pression    DOUBLE PRECISION
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pb_stats (
            sensor_id   VARCHAR(50) PRIMARY KEY,
            quartier    VARCHAR(50),
            latitude    DOUBLE PRECISION,
            longitude   DOUBLE PRECISION,
            nb_mesures  INTEGER,
            temp_min    DOUBLE PRECISION,
            temp_max    DOUBLE PRECISION,
            temp_moy    DOUBLE PRECISION,
            hum_min     DOUBLE PRECISION,
            hum_max     DOUBLE PRECISION,
            hum_moy     DOUBLE PRECISION,
            pres_min    DOUBLE PRECISION,
            pres_max    DOUBLE PRECISION,
            pres_moy    DOUBLE PRECISION,
            maj_at      TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pb_evolution (
            id              SERIAL PRIMARY KEY,
            tranche_horaire TIMESTAMP,
            quartier        VARCHAR(50),
            temp_moy        DOUBLE PRECISION,
            hum_moy         DOUBLE PRECISION,
            pres_moy        DOUBLE PRECISION,
            nb_mesures      INTEGER
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pb_ts  ON pb_mesures(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pb_qrt ON pb_mesures(quartier)")
    pg.commit()
    cur.close()
    pg.close()
    print("Tables PostgreSQL creees !", flush=True)

# ─── Sync mesures ───
def sync_mesures(cass_session):
    today = date.today()
    pg = get_pg()
    cur = pg.cursor()

    cur.execute("SELECT MAX(timestamp) FROM pb_mesures WHERE date = %s", (today,))
    result = cur.fetchone()
    last_ts = result[0] if result and result[0] else None

    total = 0
    quartier_map = {
        "SENSOR_AKWA": "Akwa", "SENSOR_BONANJO": "Bonanjo",
        "SENSOR_DEIDO": "Deido", "SENSOR_BEPANDA": "Bepanda",
        "SENSOR_MAKEPE": "Makepe", "SENSOR_NEWBELL": "New Bell",
        "SENSOR_BONAPRISO": "Bonapriso", "SENSOR_LOGBABA": "Logbaba",
        "SENSOR_CITE_SIC": "Cite SIC", "SENSOR_KOTTO": "Kotto"
    }

    for sensor in CAPTEURS:
        quartier = quartier_map.get(sensor, sensor)
        coords = COORDONNEES.get(quartier, {"lat": 4.05, "lon": 9.70})

        rows = list(cass_session.execute("""
            SELECT sensor_id, date, timestamp, quartier, temperature, humidite, pression
            FROM mesures_capteurs
            WHERE sensor_id = %s AND date = %s
        """, (sensor, today)))

        for r in rows:
            if last_ts and r.timestamp <= last_ts:
                continue
            # Convertir le type Date Cassandra en string pour psycopg2
            date_str = str(r.date)
            cur.execute("""
                INSERT INTO pb_mesures
                (sensor_id, date, timestamp, quartier, latitude, longitude,
                 temperature, humidite, pression)
                VALUES (%s, %s::date, %s, %s, %s, %s, %s, %s, %s)
            """, (r.sensor_id, date_str, r.timestamp, r.quartier,
                  coords["lat"], coords["lon"],
                  r.temperature, r.humidite, r.pression))
            total += 1

    pg.commit()
    cur.close()
    pg.close()
    print(f"  pb_mesures     : +{total} nouvelles lignes", flush=True)

# ─── Sync stats ───
def sync_stats(cass_session):
    today = date.today()
    pg = get_pg()
    cur = pg.cursor()
    now = datetime.now()

    quartier_map = {
        "SENSOR_AKWA": "Akwa", "SENSOR_BONANJO": "Bonanjo",
        "SENSOR_DEIDO": "Deido", "SENSOR_BEPANDA": "Bepanda",
        "SENSOR_MAKEPE": "Makepe", "SENSOR_NEWBELL": "New Bell",
        "SENSOR_BONAPRISO": "Bonapriso", "SENSOR_LOGBABA": "Logbaba",
        "SENSOR_CITE_SIC": "Cite SIC", "SENSOR_KOTTO": "Kotto"
    }

    for sensor in CAPTEURS:
        quartier = quartier_map.get(sensor, sensor)
        coords = COORDONNEES.get(quartier, {"lat": 4.05, "lon": 9.70})

        rows = list(cass_session.execute("""
            SELECT temperature, humidite, pression
            FROM mesures_capteurs
            WHERE sensor_id = %s AND date = %s
        """, (sensor, today)))

        if not rows:
            continue

        temps = [r.temperature for r in rows]
        hums  = [r.humidite    for r in rows]
        press = [r.pression    for r in rows]

        cur.execute("""
            INSERT INTO pb_stats
            (sensor_id, quartier, latitude, longitude, nb_mesures,
             temp_min, temp_max, temp_moy,
             hum_min,  hum_max,  hum_moy,
             pres_min, pres_max, pres_moy, maj_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (sensor_id) DO UPDATE SET
                nb_mesures = EXCLUDED.nb_mesures,
                temp_min   = EXCLUDED.temp_min,
                temp_max   = EXCLUDED.temp_max,
                temp_moy   = EXCLUDED.temp_moy,
                hum_min    = EXCLUDED.hum_min,
                hum_max    = EXCLUDED.hum_max,
                hum_moy    = EXCLUDED.hum_moy,
                pres_min   = EXCLUDED.pres_min,
                pres_max   = EXCLUDED.pres_max,
                pres_moy   = EXCLUDED.pres_moy,
                maj_at     = EXCLUDED.maj_at
        """, (sensor, quartier, coords["lat"], coords["lon"], len(rows),
              round(min(temps),2), round(max(temps),2), round(sum(temps)/len(temps),2),
              round(min(hums),2),  round(max(hums),2),  round(sum(hums)/len(hums),2),
              round(min(press),2), round(max(press),2), round(sum(press)/len(press),2),
              now))

    pg.commit()
    cur.close()
    pg.close()
    print(f"  pb_stats       : {len(CAPTEURS)} capteurs mis a jour", flush=True)

# ─── Sync évolution ───
def sync_evolution(cass_session):
    today = date.today()
    pg = get_pg()
    cur = pg.cursor()

    cur.execute("DELETE FROM pb_evolution WHERE DATE(tranche_horaire) = %s", (str(today),))

    tranches = {}
    quartier_map = {
        "SENSOR_AKWA": "Akwa", "SENSOR_BONANJO": "Bonanjo",
        "SENSOR_DEIDO": "Deido", "SENSOR_BEPANDA": "Bepanda",
        "SENSOR_MAKEPE": "Makepe", "SENSOR_NEWBELL": "New Bell",
        "SENSOR_BONAPRISO": "Bonapriso", "SENSOR_LOGBABA": "Logbaba",
        "SENSOR_CITE_SIC": "Cite SIC", "SENSOR_KOTTO": "Kotto"
    }

    for sensor in CAPTEURS:
        quartier = quartier_map.get(sensor, sensor)
        rows = list(cass_session.execute("""
            SELECT timestamp, temperature, humidite, pression
            FROM mesures_capteurs
            WHERE sensor_id = %s AND date = %s
        """, (sensor, today)))

        for r in rows:
            ts = r.timestamp
            tranche = ts.replace(minute=(ts.minute // 10) * 10,
                                  second=0, microsecond=0)
            key = (tranche, quartier)
            if key not in tranches:
                tranches[key] = {'temps': [], 'hums': [], 'press': []}
            tranches[key]['temps'].append(r.temperature)
            tranches[key]['hums'].append(r.humidite)
            tranches[key]['press'].append(r.pression)

    for (tranche, quartier), vals in tranches.items():
        cur.execute("""
            INSERT INTO pb_evolution
            (tranche_horaire, quartier, temp_moy, hum_moy, pres_moy, nb_mesures)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (tranche, quartier,
              round(sum(vals['temps'])/len(vals['temps']), 2),
              round(sum(vals['hums'])/len(vals['hums']),   2),
              round(sum(vals['press'])/len(vals['press']), 2),
              len(vals['temps'])))

    pg.commit()
    cur.close()
    pg.close()
    print(f"  pb_evolution   : {len(tranches)} tranches mises a jour", flush=True)

# ─── Export continu ───
def export_continu(intervalle=30):
    print("Connexion a Cassandra...", flush=True)
    cluster, session = get_cassandra_session()
    print("Setup PostgreSQL...", flush=True)
    setup_postgres_tables()
    print(f"Connecte ! Sync toutes les {intervalle}s\n", flush=True)
    print("CTRL+C pour arreter\n", flush=True)

    try:
        while True:
            now = datetime.now().strftime('%H:%M:%S')
            print(f"[{now}] Synchronisation...", flush=True)
            try:
                sync_mesures(session)
                sync_stats(session)
                sync_evolution(session)
                print(f"[{now}] OK. Prochain dans {intervalle}s\n", flush=True)
            except Exception as e:
                print(f"[{now}] Erreur (retry) : {e}\n", flush=True)
            time.sleep(intervalle)
    except KeyboardInterrupt:
        print("\nExport arrete.", flush=True)
    finally:
        cluster.shutdown()

if __name__ == "__main__":
    import sys
    intervalle = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    export_continu(intervalle)