import socket
import json
from confluent_kafka import Producer
from time import time, sleep
import logging
import sys


def produce(config, store):
    period = int(config['admin']['produce.period.seconds'] or 1)
    log = logging.getLogger(__name__)
    log.info(f"producer started - messages will be sent every {period} seconds")

    def acked(err, msg):
        if err is not None:
            log.error(f"Failed to deliver message: {str(msg)}, {str(err)}")
        else:
            latency_ms = msg.latency()*1000
            store.addProduce(latency_ms)
            log.debug(f"Message produced to partition {str(msg.partition())}, offset {str(msg.offset())} - latency: {latency_ms:0.2f}")


    p_conf = config['default'] | config['producer'] # this merges the dictionaries
    if p_conf['client.id'] == None:
        p_conf['client.id'] = socket.gethostname()
    
    producer = Producer(p_conf)
    # loop over partitions and produce 1 message to each
    while True:
        # wait for metadata if we haven't got it
        if store.get('metadata') == {}:
            sleep(5)

        try:
            partitions = store.get('metadata').topics[store.get('topic')].partitions
            payload = json.dumps({
                'timestamp': time()
            })

            for i in range(0, len(partitions)):
                producer.produce(config['admin']['heartbeat.topic'], key="heartbeat", partition=i, value=payload, callback=acked)
            producer.poll(0)
            producer.flush()
            sleep(period)

        except Exception as e:
            log.error(f"Producer error: {e}")
            sys.exit(1)

        finally:
            pass
