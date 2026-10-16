import logging
import time

import redis
from django.core.management.base import BaseCommand

from common.ids import is_valid_id
from common.redis_client import BUILD_QUEUE, STATUS_HASH, get_redis
from deployer.services import process_deployment

logger = logging.getLogger(__name__)
REDIS_ERRORS = (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError)


def set_status(deploy_id, value, attempts=5):
    for _ in range(attempts):
        try:
            get_redis().hset(STATUS_HASH, deploy_id, value)
            return
        except REDIS_ERRORS:
            logger.warning("Redis unavailable while saving status, retrying...")
            time.sleep(2)
    logger.error("Could not save status %r for %s", value, deploy_id)


class Command(BaseCommand):
    help = "Worker: consumes deployment ids from the Redis build queue, builds them and publishes dist/."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Deployer listening on '{BUILD_QUEUE}'..."))
        try:
            while True:
                try:
                    item = get_redis().brpop(BUILD_QUEUE, timeout=5)
                except REDIS_ERRORS:
                    logger.warning("Lost Redis connection, retrying in 2s...")
                    time.sleep(2)
                    continue
                if item is None:  # nothing queued, loop again
                    continue

                _, deploy_id = item
                if not is_valid_id(deploy_id):
                    logger.warning("Ignoring malformed deployment id: %r", deploy_id)
                    continue

                set_status(deploy_id, "building")
                try:
                    process_deployment(deploy_id)
                except Exception:
                    logger.exception("Deployment %s failed", deploy_id)
                    set_status(deploy_id, "failed")
                else:
                    set_status(deploy_id, "deployed")
                    logger.info("Deployment %s is live", deploy_id)
        except KeyboardInterrupt:
            self.stdout.write("Deployer stopped.")