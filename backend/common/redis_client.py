import redis
from django.conf import settings

BUILD_QUEUE = "build-queue"
STATUS_HASH = "status"

_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client
