import asyncio
from confluent_kafka.admin import AdminClient
from config_parsing import readConfig
from store import HeartbeatStore
from check_topic import checkTopic
from check_metadata import checkMetadata
from check_connectivity import checkConnectivity
from producer import produce
from consumer import consume
from prom_exporter import promExporter
from log_config import configureLogging
import logging
import threading

async def main():
    conf = readConfig("config.ini")
    # TODO: support multiple cluster configs

    configureLogging(conf)
    log = logging.getLogger('main')
    
    log.info(f"Starting cc-heartbeat against {conf['default']['bootstrap.servers']}")

    adminApi = AdminClient(conf["default"])
    store = HeartbeatStore(conf)
    store.setClusterInfo(adminApi.describe_cluster().result())
    bootstrap = conf["default"]["bootstrap.servers"].split(":")[0]

    # startup messages
    log.info(
        f"{len(store.get('cluster_info').nodes)} brokers in {store.get('cluster_info').cluster_id} - controller is {store.get('controller')}"
    )
    for node in store.get('cluster_info').nodes:
        log.info(f"  {node.id}: name: {node.host.replace('-' + bootstrap, '')}, rack: {node.rack}")

    # ensure the heartbeat topic exists and has the same number of partitions and brokers in the cluster
    threading.Thread(target=checkTopic, args=(adminApi, store)).start()

    # resolve metadata regularly, and report if it changes plus restart producer / consumer
    threading.Thread(target=checkMetadata, args=(adminApi, store)).start()

    # make a network connection to each broker to ensure it's reachable
    threading.Thread(target=checkConnectivity, args=(store,)).start()


    # long-lived producer to send message to each partition in the heartbeat topic
    threading.Thread(target=produce, args=(conf, store)).start()
    
    # long-lived consumer to read the messages
    threading.Thread(target=consume, args=(conf, store)).start()

    # start the prometheus exporter
    await promExporter(store)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.create_task(main())
        loop.run_forever()
    except asyncio.CancelledError:
        pass
