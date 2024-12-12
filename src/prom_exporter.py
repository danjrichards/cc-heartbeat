from aiohttp import web
import logging


async def promExporter(store):
    admin_config = store.get('config')['admin']
    host = '0.0.0.0'
    port = 8080
    if 'metrics.listener.host' in admin_config:
        host = admin_config['metrics.listener.host']
    if 'metrics.listener.port' in admin_config:
        port = admin_config['metrics.listener.port']
    log = logging.getLogger(__name__)
    # don't log each web access unless we're in debug mode
    ll = log if ("log.level" in admin_config and admin_config["log.level"] == "DEBUG") else None
        
    log.info(f"promExporter started - listening on {host}:{port}")

    routes = web.RouteTableDef()

    @routes.get('/')
    @routes.get('/metrics')
    async def metrics(request):
        log.debug(f"Metrics: {request.scheme} request from {request.remote}")

        try:
            txt = f"""# Confluent Cloud heartbeat metrics
# HELP heartbeat_messages_produced Count of messages produced since cc_heartbeat was started
# TYPE heartbeat_messages_produced counter
heartbeat_messages_produced{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('messages_produced')}
# HELP heartbeat_avg_produce_latency_ms Average latency for the messages produced since the last metric scrape
# TYPE heartbeat_avg_produce_latency_ms gauge
heartbeat_avg_produce_latency_ms{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('average_produce_latency_ms'):0.2f}
# HELP heartbeat_messages_consumed Count of messages consumed since cc_heartbeat was started
# TYPE heartbeat_messages_consumed counter
heartbeat_messages_consumed{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('messages_consumed')}
# HELP heartbeat_avg_consume_latency_ms Average end-to-end latency for the messages consumed since the last metric scrape
# TYPE heartbeat_avg_consume_latency_ms gauge
heartbeat_avg_consume_latency_ms{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('average_consume_latency_ms'):0.2f}
# HELP heartbeat_broker_count Count of brokers
# TYPE heartbeat_broker_count counter
heartbeat_broker_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {len(store.get('brokers'))}
# HELP heartbeat_connection_check_count Count of network connection checks to the brokers since cc_heartbeat was started
# TYPE heartbeat_connection_check_count counter
heartbeat_connection_check_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('connection_checks')}
# HELP heartbeat_connection_latency_ms Average latency for the network connection checks to each broker since the last metric scrape
# TYPE heartbeat_connection_latency_ms gauge
"""
            # the TCP peername is available, but it changes so frequently in CC (at least with a public networking cluster) that it confuses the metrics presentation
            # broker_ip="{store.get('broker_ip')[b]
            for b in store.get('brokers'):
                txt += f"""heartbeat_connection_latency_ms{{broker="{b}", cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('connection_latency_ms')[b]:0.2f}\n"""

            # add topic, partition and consumer group counts
            topics = store.get('metadata').topics
            topic_count = len(topics)
            partition_count = 0
            for t in topics:
                partition_count += len(topics[t].partitions)
            cg_count = len(store.get('consumer_groups'))

            txt += f"""
# HELP heartbeat_topic_count The number of topics per cluster
# TYPE heartbeat_topic_count gauge
heartbeat_topic_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {topic_count}

# HELP heartbeat_partition_count The number of partitions per cluster
# TYPE heartbeat_partition_count gauge
heartbeat_partition_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {partition_count}

# HELP heartbeat_cg_count The number of consumer groups
# TYPE heartbeat_cg_count gauge
heartbeat_cg_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {cg_count}"""


            # clear the latencies - is this the right thing to do?
            store.resetMetrics()
        
        except Exception as e:
            txt = f"# cc-heartbeat Error\n{e}"

        return web.Response(text=txt)


    @routes.get('/topics')
    async def topics(request):
        log.debug(f"Topics: {request.scheme} request from {request.remote}")
        m = store.get('metadata')
        partition_count = 0

        txt = f"""# Confluent Cloud heartbeat - topics
# HELP heartbeat_topic_count The number of topics per cluster
# TYPE heartbeat_topic_count gauge
heartbeat_topic_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {len(m.topics)}
# HELP heartbeat_topic_partition_count The number of partitions in this topic
# TYPE heartbeat_topic_partition_count gauge
# HELP heartbeat_topic_partition_leader The partition leader for each topic
# TYPE heartbeat_topic_partition_leader gauge
"""
        for topic_name in m.topics:
            partitions = m.topics[topic_name].partitions
            partition_count += len(partitions)
            txt += f"""heartbeat_topic_partition_count{{cluster_id="{store.get('cluster_info').cluster_id}", topic_name="{topic_name}"}} {len(partitions)}\n"""
            for partition_id in partitions:
                txt += f"""heartbeat_topic_partition_leader{{cluster_id="{store.get('cluster_info').cluster_id}", topic_name="{topic_name}", partition="{partition_id}"}} {partitions[partition_id].leader}\n"""

        txt += f"""# HELP heartbeat_partition_count The number of partitions per cluster
# TYPE heartbeat_partition_count gauge
heartbeat_partition_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {partition_count}"""

        return web.Response(text=txt)


    @routes.get('/consumer-groups')
    async def consumer_groups(request):
        log.debug(f"Consumer Groups: {request.scheme} request from {request.remote}")
        all_cg = store.get('consumer_groups')
        member_count = 0

        txt = f"""# Confluent Cloud heartbeat - consumer groups
# HELP heartbeat_cg_count The number of consumer groups
# TYPE heartbeat_cg_count gauge
heartbeat_cg_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {len(all_cg)}
# HELP heartbeat_cg_member_count The number of members of the consumer group
# TYPE heartbeat_cg_member_count gauge
"""
        for cg in all_cg:
            member_count += len(cg.members)
            txt += f"""heartbeat_cg_member_count{{cluster_id="{store.get('cluster_info').cluster_id}"}}, group_id="{cg.id}"}} {len(cg.members)}\n"""

        txt += f"""# HELP heartbeat_cg_members_total_count The number of consumer group members per cluster
# TYPE heartbeat_cg_members_total_count gauge
heartbeat_cg_members_total_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {member_count}"""


        return web.Response(text=txt)


    app = web.Application()
    app.add_routes(routes)

    runner = web.AppRunner(app, access_log=ll)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
