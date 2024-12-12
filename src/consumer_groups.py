import logging
from time import time, sleep
from confluent_kafka import (Consumer, TopicPartition, KafkaException, OFFSET_INVALID)


def consumerGroups(adminApi, config, store):
    """
    Fetch consumer group details
    """
    # examples:
    # https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/adminapi.py#L654
    # https://github.com/linkedin/kafka-tools/blob/master/kafka/tools/client.py#L286
    # https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/get_watermark_offsets.py
    
    period = int(store.get('config')["admin"]["check.consumer.group.period.seconds"] or 60)
    log = logging.getLogger(__name__)
    log.info(f"consumerGroups started - will run every {period} seconds")

    while True:
        start = time()
        log.debug(f"consumerGroups iteration")

        try:
            all_cg = adminApi.list_groups(timeout=15)
            # all_cg = fut.result()

            # for cg in all_cg:
            #     log.debug(f"    CG id: {cg.id} members: {len(cg.members)} state: {cg.state}")

            # for g in groups:
                # print(" \"{}\" with {} member(s), protocol: {}, protocol_type: {}".format(
                #     g, len(g.members), g.protocol, g.protocol_type))

                # for m in g.members:
                #     print("id {} client_id: {} client_host: {}".format(m.id, m.client_id, m.client_host))
                # # need to instantiate a consumer to get the subscribed topics
                # c_conf = config['default'] | config['consumer']
                # c_conf['group.id'] = cg.group_id
                # consumer = Consumer(c_conf)
                # subscribed_topics = consumer.list_topics()
                # # *** the above is returning *all* topics, not just the ones subscribed to by this CG

                # for topic, topic_info in subscribed_topics.topics.items():
                #     metadata = consumer.list_topics(topic, timeout=10)
                #     if metadata.topics[topic].error is not None:
                #         raise KafkaException(metadata.topics[topic].error)

                #     # Construct TopicPartition list of partitions to query
                #     partitions = [TopicPartition(topic, p) for p in metadata.topics[topic].partitions]

                #     # Query committed offsets for this group and the given partitions
                #     committed = consumer.committed(partitions, timeout=10)

                #     for partition in committed:
                #         # Get the partitions low and high watermark offsets.
                #         (lo, hi) = consumer.get_watermark_offsets(partition, timeout=10, cached=False)

                #         if partition.offset == OFFSET_INVALID:
                #             offset = "-"
                #         else:
                #             offset = "%d" % (partition.offset)

                #         if hi < 0:
                #             lag = "no hwmark"  # Unlikely
                #         elif partition.offset < 0:
                #             # No committed offset, show total message count as lag.
                #             # The actual message count may be lower due to compaction
                #             # and record deletions.
                #             lag = "%d" % (hi - lo)
                #         else:
                #             lag = "%d" % (hi - partition.offset)

                #         print("%-50s  %9s  %9s" % (
                #             "{} [{}]".format(partition.topic, partition.partition), offset, lag))
 
                # consumer.close()

                # # TODO: do something with errors
                # for error in cg.errors:
                #     print("    error: {}".format(error))
            
            store.setConsumerGroups(all_cg)

        except Exception:
            raise

        # take the elapsed time out of the repeat period and sleep for that long
        delay = time() - start
        if delay > 0 and delay < period:
            sleep(period - delay)
