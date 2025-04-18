import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="sample_task")
def sample_task(name="World"):
    """A simple task that says hello."""
    message = f"Hello, {name}!"
    logger.info(message)
    return message
