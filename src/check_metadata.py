import logging
from time import time, sleep


def checkMetadata(adminApi, store):
    """
    Re-fetch metadata and log any changes
    """
    period = int(store.get('config')["admin"]["check.metadata.period.seconds"] or 60)
    log = logging.getLogger(__name__)
    log.info(f"checkMetadata started - will run every {period} seconds")

    while True:
        start = time()
        log.debug(f"checkMetadata iteration")

        prevBrokers = store.get('brokers')
        metadata = adminApi.list_topics(timeout=30)
        store.setMetadata(metadata)     # this populates store.metadata and store.brokers

        # compare previous and latest metadata & flag changes
        if len(prevBrokers) > 0 and len(prevBrokers) != len(store.get('brokers')):
            log.warn(f"Broker count changed from {len(prevBrokers)} to {len(store.get('brokers'))}")
        else:
            for b in store.get('brokers'):
                if len(prevBrokers) > 0 and prevBrokers[b].host != store.get('brokers')[b].host:
                    log.info(f"Broker {store.get('brokers')[b].name} IP changed from {prevBrokers[b].host} to {store.get('brokers')[b].host}")

        # take the elapsed time out of the repeat period and sleep for that long
        delay = time() - start
        if delay > 0 and delay < period:
            sleep(period - delay)
