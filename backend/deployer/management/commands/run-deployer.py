import logging

from django.core.management.base import BaseCommand

from common.ids import is_valid_id
from common.redis_client import BUILD_QUEUE, STATUS_HASH, get_redis
from deployer.services import process_deployment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Worker: consumes deployment ids from the Redis build queue, builds them and publishes dist/."

    def handle(self, *args, **options):
        r = get_redis()
        self.stdout.write(
            self.style.SUCCESS(f"Deployer listening on '{BUILD_QUEUE}'...")
        )
        try:
            while True:
                _, deploy_id = r.brpop(BUILD_QUEUE, timeout=0)
                if not is_valid_id(deploy_id):
                    logger.warning("Ignoring malformed deployment id: %r", deploy_id)
                    continue

                r.hset(STATUS_HASH, deploy_id, "building")
                try:
                    process_deployment(deploy_id)
                except Exception:
                    logger.exception("Deployment %s failed", deploy_id)
                    r.hset(STATUS_HASH, deploy_id, "failed")
                else:
                    r.hset(STATUS_HASH, deploy_id, "deployed")
                    logger.info("Deployment %s is live", deploy_id)
        except KeyboardInterrupt:
            self.stdout.write("Deployer stopped.")
