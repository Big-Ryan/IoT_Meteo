from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy
from cassandra.io.twistedreactor import TwistedConnection

class DockerAddressTranslator:
    def translate(self, addr):
        return '127.0.0.1'

print("Connexion en cours...", flush=True)

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

try:
    session = cluster.connect('meteo_douala')
    print("Cassandra OK !", flush=True)
    row = session.execute("SELECT release_version FROM system.local").one()
    print(f"Version : {row.release_version}", flush=True)
except Exception as e:
    print(f"Erreur : {e}", flush=True)
finally:
    cluster.shutdown()
    print("Fin.", flush=True)