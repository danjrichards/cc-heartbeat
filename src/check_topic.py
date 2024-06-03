from confluent_kafka.admin import NewTopic
from confluent_kafka import KafkaError
from time import time, sleep
import logging
import sys


def checkTopic(adminApi, store):
    """
    Create or update the heartbeat topic
    """
    period = int(store.get('config')["admin"]["check.topic.period.seconds"] or 3600)
    log = logging.getLogger(__name__)
    log.info(f"checkTopic started - will run every {period} seconds")

    while True:
        start = time()
        log.debug(f"checkTopic iteration")
        
        metadata = adminApi.list_topics(timeout=30)
        brokerCount = len(metadata.brokers)
        topic = store.get('topic')

        if metadata.topics[topic]:
            # if it exists check the number of partitions matches the number of brokers
            partitions = metadata.topics[topic].partitions
            if len(partitions) == brokerCount:
                log.debug('checkTopic - no action required')
            else:
                dt = adminApi.delete_topics([topic], operation_timeout=30)

                # Wait for operation to finish.
                for topic, f in dt.items():
                    try:
                        f.result()  # The result itself is None
                        log.info(f"Deleted `{topic}` topic that had {len(partitions)} partitions to recreate with {brokerCount} partitions")
                    except Exception as e:
                        log.error(f"Failed to delete topic `{topic}`: {e}")
                        sys.exit(1)

                ct = adminApi.create_topics(
                    [
                        NewTopic(
                            topic,
                            num_partitions=brokerCount,
                            replication_factor=3,  # in CC replication factor must always be 3
                            config={"retention.ms": 1440000}    # retention = 1 day
                        )
                    ]
                )
                for t, fut in ct.items():
                    try:
                        fut.result()  # the result is None
                        log.info(f"Created heartbeat topic: {topic}")

                    except Exception as e:
                        # continue if TOPIC_ALREADY_EXISTS, otherwise fail fast
                        if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                            log.debug(f"Heartbeat topic '{topic}' already exists")
                        else:
                            log.error(f"Failed to create heartbeat topic '{topic}': {e}")
                            sys.exit(1)

        # take the elapsed time out of the repeat period and sleep for that long
        delay = time() - start
        if delay > 0 and delay < period:
            sleep(period - delay)
