from confluent_kafka import Consumer
from time import time, sleep
import logging
import json


def consume(config, store):
    log = logging.getLogger(__name__)
    log.info('consumer started')

    # loop = asyncio.get_event_loop()

    c_conf = config['default'] | config['consumer']
    consumer = Consumer(c_conf)
    consumer.subscribe([config['admin']['heartbeat.topic']])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to `session.timeout.ms` for the consumer group to rebalance and start consuming
                sleep(0.1)
            elif msg.error():
                log.error(f"ERROR: {msg.error()}")
            else:
                key = msg.key().decode('utf-8')
                value = msg.value().decode('utf-8')
                val_time = json.loads(value)['timestamp']
                latency_ms = (time() - float(val_time)) * 1000
                store.addConsume(latency_ms)
                log.debug(f"Consumed event - end to end latency: {latency_ms:0.2f}")
            
            consumer.commit(asynchronous=True)
            sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()

