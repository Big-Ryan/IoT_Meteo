import time
import random
from datetime import datetime, date, timezone
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, ConsistencyLevel
from cassandra.query import SimpleStatement
from cassandra.io.twistedreactor import TwistedConnection

class DockerAddressTranslator:
    def translate(self, addr):
        return '127.0.0.1'

def get_session():
    profile = ExecutionProfile(
        load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1'])
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

CAPTEURS = ["SENSOR_AKWA", "SENSOR_BONANJO", "SENSOR_DEIDO",
            "SENSOR_BEPANDA", "SENSOR_MAKEPE"]


def demo_consistency(session):
    print("\n" + "="*55, flush=True)
    print(" OPTIMISATION 1 : CONSISTENCY LEVEL", flush=True)
    print("="*55, flush=True)

    levels = [
        (ConsistencyLevel.ONE,    "ONE    — Rapide, moins fiable"),
        (ConsistencyLevel.QUORUM, "QUORUM — Équilibre fiabilité/vitesse"),
        (ConsistencyLevel.ALL,    "ALL    — Fiable, plus lent"),
    ]

    today = date.today()
    sensor = "SENSOR_AKWA"

    for level, description in levels:
        query = SimpleStatement(
            f"SELECT * FROM mesures_capteurs WHERE sensor_id = %s AND date = %s LIMIT 100",
            consistency_level=level
        )
        times = []
        for _ in range(10):
            start = time.time()
            list(session.execute(query, (sensor, today)))
            times.append((time.time() - start) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  [{description}]", flush=True)
        print(f"   Temps moyen : {avg:.2f} ms", flush=True)
        print(f"   Min : {min(times):.2f} ms | Max : {max(times):.2f} ms", flush=True)


def demo_prepared_vs_simple(session):
    print("\n" + "="*55, flush=True)
    print(" OPTIMISATION 2 : PREPARED vs SIMPLE STATEMENTS", flush=True)
    print("="*55, flush=True)

    today = date.today()
    n = 200

    times_simple = []
    for _ in range(n):
        sensor = random.choice(CAPTEURS)
        start = time.time()
        list(session.execute(
            f"SELECT * FROM mesures_capteurs WHERE sensor_id = '{sensor}' AND date = '{today}' LIMIT 20"
        ))
        times_simple.append((time.time() - start) * 1000)

    prepared = session.prepare(
        "SELECT * FROM mesures_capteurs WHERE sensor_id = ? AND date = ? LIMIT 20"
    )
    times_prepared = []
    for _ in range(n):
        sensor = random.choice(CAPTEURS)
        start = time.time()
        list(session.execute(prepared, (sensor, today)))
        times_prepared.append((time.time() - start) * 1000)

    avg_simple   = sum(times_simple)   / len(times_simple)
    avg_prepared = sum(times_prepared) / len(times_prepared)
    gain = ((avg_simple - avg_prepared) / avg_simple) * 100

    print(f"\n  Simple Statement   : {avg_simple:.2f} ms/requête", flush=True)
    print(f"  Prepared Statement : {avg_prepared:.2f} ms/requête", flush=True)
    print(f"  Gain de performance : {gain:.1f}%", flush=True)


def demo_batch_vs_individual(session):
    print("\n" + "="*55, flush=True)
    print(" OPTIMISATION 3 : BATCH vs INSERTIONS INDIVIDUELLES", flush=True)
    print("="*55, flush=True)

    from cassandra.query import BatchStatement

    n = 50
    today = date.today()

    def gen_row():
        return (
            random.choice(CAPTEURS), today,
            datetime.now(timezone.utc),
            "Douala",
            round(random.uniform(24.0, 35.0), 2),
            round(random.uniform(60.0, 95.0), 2),
            round(random.uniform(1008.0, 1015.0), 2)
        )

    insert_cql = """
        INSERT INTO mesures_capteurs
        (sensor_id, date, timestamp, quartier, temperature, humidite, pression)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    prepared = session.prepare(insert_cql.replace('%s', '?'))

    start = time.time()
    for _ in range(n):
        session.execute(prepared, gen_row())
    t_individual = time.time() - start

    start = time.time()
    batch = BatchStatement()
    for _ in range(n):
        batch.add(prepared, gen_row())
    session.execute(batch)
    t_batch = time.time() - start

    gain = ((t_individual - t_batch) / t_individual) * 100
    print(f"\n  Insertions individuelles ({n} lignes) : {t_individual:.3f}s", flush=True)
    print(f"  Batch ({n} lignes)                   : {t_batch:.3f}s", flush=True)
    print(f"  Gain de performance : {gain:.1f}%", flush=True)


def demo_partitioning(session):
    print("\n" + "="*55, flush=True)
    print(" OPTIMISATION 4 : ANALYSE DU PARTITIONING", flush=True)
    print("="*55, flush=True)

    today = date.today()
    print("\n  Distribution des données par partition :", flush=True)
    print(f"  {'Capteur':<20} {'Date':<12} {'Nb mesures'}", flush=True)
    print(f"  {'─'*50}", flush=True)

    total = 0
    for sensor in CAPTEURS:
        rows = list(session.execute("""
            SELECT COUNT(*) FROM mesures_capteurs
            WHERE sensor_id = %s AND date = %s
        """, (sensor, today)))
        count = rows[0][0] if rows else 0
        total += count
        print(f"  {sensor:<20} {str(today):<12} {count}", flush=True)

    print(f"  {'─'*50}", flush=True)
    print(f"  {'TOTAL':<20} {'':12} {total}", flush=True)
    print(f"\n  Clé de partition : (sensor_id, date)", flush=True)
    print(f"  → Chaque partition = 1 capteur × 1 jour", flush=True)
    print(f"  → Évite les 'hot partitions' et garantit une distribution uniforme", flush=True)


if __name__ == "__main__":
    print("Connexion à Cassandra...", flush=True)
    cluster, session = get_session()
    print("Connecté !\n", flush=True)

    demo_consistency(session)
    demo_prepared_vs_simple(session)
    demo_batch_vs_individual(session)
    demo_partitioning(session)

    cluster.shutdown()
    print("\n" + "="*55, flush=True)
    print(" Optimisation terminée !", flush=True)
    print("="*55, flush=True)