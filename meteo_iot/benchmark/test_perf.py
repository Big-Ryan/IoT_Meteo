import time
import random
import statistics
import psycopg2
from datetime import datetime, date, timezone
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, ConsistencyLevel
from cassandra.io.twistedreactor import TwistedConnection

# CONFIG CASSANDRA
class DockerAddressTranslator:
    def translate(self, addr):
        return '127.0.0.1'

def get_cassandra_session():
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

# CONFIG POSTGRESQL
def get_pg_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="meteo_benchmark",
        user="postgres",
        password="postgreesql"
    )

def setup_postgres(conn):
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE mesures RESTART IDENTITY")
    conn.commit()
    cur.close()

# DONNÉES DE TEST
CAPTEURS = [
    "SENSOR_AKWA", "SENSOR_BONANJO", "SENSOR_DEIDO",
    "SENSOR_BEPANDA", "SENSOR_MAKEPE", "SENSOR_NEWBELL",
    "SENSOR_BONAPRISO", "SENSOR_LOGBABA", "SENSOR_CITE_SIC", "SENSOR_KOTTO"
]

QUARTIER_MAP = {
    "SENSOR_AKWA": "Akwa", "SENSOR_BONANJO": "Bonanjo",
    "SENSOR_DEIDO": "Deido", "SENSOR_BEPANDA": "Bepanda",
    "SENSOR_MAKEPE": "Makepe", "SENSOR_NEWBELL": "New Bell",
    "SENSOR_BONAPRISO": "Bonapriso", "SENSOR_LOGBABA": "Logbaba",
    "SENSOR_CITE_SIC": "Cite SIC", "SENSOR_KOTTO": "Kotto"
}

def gen_mesure():
    sensor = random.choice(CAPTEURS)
    return (
        sensor,
        date.today(),
        datetime.now(timezone.utc),
        QUARTIER_MAP[sensor],   # ← bon quartier
        round(random.uniform(24.0, 35.0), 2),
        round(random.uniform(60.0, 95.0), 2),
        round(random.uniform(1008.0, 1015.0), 2)
    )

# BENCHMARK ÉCRITURE
def bench_write_cassandra(session, n):
    print(f"  Cassandra : ecriture de {n} lignes...", flush=True)
    prepared = session.prepare("""
        INSERT INTO mesures_capteurs
        (sensor_id, date, timestamp, quartier, temperature, humidite, pression)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    start = time.time()
    for _ in range(n):
        session.execute(prepared, gen_mesure())
    return time.time() - start

def bench_write_postgres(conn, n):
    print(f"  PostgreSQL: ecriture de {n} lignes...", flush=True)
    cur = conn.cursor()
    start = time.time()
    for _ in range(n):
        m = gen_mesure()
        cur.execute("""
            INSERT INTO mesures (sensor_id, date, timestamp, quartier, temperature, humidite, pression)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, m)
    conn.commit()
    cur.close()
    return time.time() - start

# BENCHMARK LECTURE
def bench_read_cassandra(session, n):
    print(f"  Cassandra : {n} lectures...", flush=True)
    today = date.today()
    prepared = session.prepare("""
        SELECT * FROM mesures_capteurs
        WHERE sensor_id = ? AND date = ? LIMIT 50
    """)
    times = []
    for _ in range(n):
        sensor = random.choice(CAPTEURS)
        start = time.time()
        list(session.execute(prepared, (sensor, today)))
        times.append(time.time() - start)
    return sum(times), statistics.mean(times) * 1000

def bench_read_postgres(conn, n):
    print(f"  PostgreSQL: {n} lectures...", flush=True)
    today = date.today()
    cur = conn.cursor()
    times = []
    for _ in range(n):
        sensor = random.choice(CAPTEURS)
        start = time.time()
        cur.execute("""
            SELECT * FROM mesures
            WHERE sensor_id = %s AND date = %s
            ORDER BY timestamp DESC LIMIT 50
        """, (sensor, today))
        cur.fetchall()
        times.append(time.time() - start)
    cur.close()
    return sum(times), statistics.mean(times) * 1000

# BENCHMARK AGRÉGATION
def bench_aggregation_cassandra(session):
    print(f"  Cassandra : agregation...", flush=True)
    today = date.today()
    sensor = "SENSOR_AKWA"
    start = time.time()
    rows = list(session.execute("""
        SELECT temperature, humidite, pression
        FROM mesures_capteurs
        WHERE sensor_id = %s AND date = %s
    """, (sensor, today)))
    if rows:
        temps = [r.temperature for r in rows]
        _ = (min(temps), max(temps), sum(temps)/len(temps))
    return (time.time() - start) * 1000, len(rows)

def bench_aggregation_postgres(conn):
    print(f"  PostgreSQL: agregation...", flush=True)
    today = date.today()
    sensor = "SENSOR_AKWA"
    cur = conn.cursor()
    start = time.time()
    cur.execute("""
        SELECT MIN(temperature), MAX(temperature), AVG(temperature),
               MIN(humidite),    MAX(humidite),    AVG(humidite),
               COUNT(*)
        FROM mesures
        WHERE sensor_id = %s AND date = %s
    """, (sensor, today))
    result = cur.fetchone()
    elapsed = (time.time() - start) * 1000
    cur.close()
    return elapsed, result[-1] if result else 0

# MAIN
def run_benchmark():
    print("=" * 60, flush=True)
    print("   BENCHMARK  Cassandra (cluster)  vs  PostgreSQL", flush=True)
    print("=" * 60, flush=True)

    print("\nConnexion aux bases...", flush=True)
    cass_cluster, cass_session = get_cassandra_session()
    pg_conn = get_pg_connection()
    setup_postgres(pg_conn)
    print("Connecte !\n", flush=True)

    volumes = [500, 2000, 5000]
    results = []

    for n in volumes:
        print(f"\n{'─'*60}", flush=True)
        print(f" Volume : {n} operations", flush=True)
        print(f"{'─'*60}", flush=True)

        # Écriture
        print("\n[ECRITURE]", flush=True)
        t_cass_w = bench_write_cassandra(cass_session, n)
        t_pg_w   = bench_write_postgres(pg_conn, n)
        print(f"  Cassandra  : {t_cass_w:.3f}s  ({n/t_cass_w:.0f} ops/s)", flush=True)
        print(f"  PostgreSQL : {t_pg_w:.3f}s  ({n/t_pg_w:.0f} ops/s)", flush=True)

        # Lecture
        print("\n[LECTURE]", flush=True)
        t_cass_r, avg_cass = bench_read_cassandra(cass_session, n)
        t_pg_r,   avg_pg   = bench_read_postgres(pg_conn, n)
        print(f"  Cassandra  : {t_cass_r:.3f}s  (moy {avg_cass:.2f} ms/req)", flush=True)
        print(f"  PostgreSQL : {t_pg_r:.3f}s  (moy {avg_pg:.2f} ms/req)", flush=True)

        results.append({
            "volume": n,
            "cass_write": t_cass_w, "pg_write": t_pg_w,
            "cass_read":  t_cass_r, "pg_read":  t_pg_r,
            "cass_avg_ms": avg_cass, "pg_avg_ms": avg_pg
        })

    # Agrégation
    print(f"\n{'─'*60}", flush=True)
    print(" AGREGATION (MIN/MAX/AVG sur toutes les mesures du jour)", flush=True)
    print(f"{'─'*60}", flush=True)
    t_cass_agg, nb_cass = bench_aggregation_cassandra(cass_session)
    t_pg_agg,   nb_pg   = bench_aggregation_postgres(pg_conn)
    print(f"  Cassandra  : {t_cass_agg:.2f} ms ({nb_cass} lignes)", flush=True)
    print(f"  PostgreSQL : {t_pg_agg:.2f} ms ({nb_pg} lignes)", flush=True)

    # Résumé
    print(f"\n{'='*60}", flush=True)
    print("   RESUME FINAL", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"{'Volume':<8} {'Cass W(s)':<12} {'PG W(s)':<12} {'Cass R(s)':<12} {'PG R(s)':<12}", flush=True)
    print(f"{'─'*56}", flush=True)
    for r in results:
        print(f"{r['volume']:<8} {r['cass_write']:<12.3f} {r['pg_write']:<12.3f} {r['cass_read']:<12.3f} {r['pg_read']:<12.3f}", flush=True)

    cass_cluster.shutdown()
    pg_conn.close()
    print("\nBenchmark termine !", flush=True)
    return results

if __name__ == "__main__":
    run_benchmark()