import redis
from django.conf import settings

BUILD_QUEUE = "build-queue"
STATUS_HASH = "status"

_client = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            socket_timeout=30,
            health_check_interval=30,  # pings and reconnects if the connection sat idle
        )
    return _client