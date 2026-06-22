import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

import ssl

# If using Upstash or any TLS-enabled Redis, ensure the broker uses SSL.
broker_use_ssl = None
if redis_url.startswith("rediss://"):
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED
    }

celery_app = Celery(
    "vaivi_tasks",
    broker=redis_url,
    backend=redis_url,
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=broker_use_ssl,
    # Good practices for reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1
)
