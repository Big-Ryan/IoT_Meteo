from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, ConsistencyLevel
from cassandra.io.twistedreactor import TwistedConnection

EXEC_PROFILE_WRITE = "write"
EXEC_PROFILE_READ  = "read"

class DockerAddressTranslator:
    def translate(self, addr):
        return '127.0.0.1'

_cluster = None
_session = None

def get_session():
    global _cluster, _session
    if _session is not None:
        return _session, _cluster

    # Profil écriture — ONE : rapide, on peut se permettre une légère inconsistance
    profile_write = ExecutionProfile(
        load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
        consistency_level=ConsistencyLevel.ONE,
        request_timeout=30
    )

    # Profil lecture — TWO : au moins 2 nœuds confirment, meilleure cohérence
    profile_read = ExecutionProfile(
        load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
        consistency_level=ConsistencyLevel.TWO,
        request_timeout=30
    )

    # Profil défaut — ONE pour les opérations générales
    profile_default = ExecutionProfile(
        load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
        consistency_level=ConsistencyLevel.ONE,
        request_timeout=30
    )

    _cluster = Cluster(
        contact_points=['127.0.0.1'],
        port=9042,
        connection_class=TwistedConnection,
        execution_profiles={
            EXEC_PROFILE_DEFAULT:      profile_default,
            EXEC_PROFILE_WRITE:        profile_write,
            EXEC_PROFILE_READ:         profile_read,
        },
        address_translator=DockerAddressTranslator(),
        connect_timeout=15
    )
    _session = _cluster.connect('meteo_douala')
    return _session, _cluster