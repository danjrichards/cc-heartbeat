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
        log.debug(f"{request.scheme} request from {request.remote}")

        txt = f"""# Confluent Cloud heartbeat metrics
# HELP heartbeat_controller The cluster controller broker ID
# TYPE heartbeat_controller gauge
heartbeat_controller{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('controller')}

# HELP heartbeat_messages_produced Count of messages produced since cc_heartbeat was started
# TYPE heartbeat_messages_produced counter
heartbeat_messages_produced{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('messages_produced')}
# HELP heartbeat_avg_produce_latency_ms Average latency for the messages produced since the last metric scrape
# TYPE heartbeat_avg_produce_latency_ms gauge
heartbeat_avg_produce_latency_ms{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('average_produce_latency_ms'):0.2f}
# HELP heartbeat_messages_consumed Count of messages consumed since the last metric scrape
# TYPE heartbeat_messages_consumed counter
heartbeat_messages_consumed{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('messages_consumed')}
# HELP heartbeat_avg_consume_latency_ms Average end-to-end latency for the messages consumed since the last metric scrape
# TYPE heartbeat_avg_consume_latency_ms gauge
heartbeat_avg_consume_latency_ms{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('average_consume_latency_ms'):0.2f}
# HELP heartbeat_broker_count Count of brokers
# TYPE heartbeat_broker_count counter
heartbeat_broker_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {len(store.get('brokers'))}
# HELP heartbeat_connection_check_count Count of network connection checks to the brokers since the last metric scrape
# TYPE heartbeat_connection_check_count counter
heartbeat_connection_check_count{{cluster_id="{store.get('cluster_info').cluster_id}"}} {store.get('connection_checks')}
# HELP heartbeat_connection_latency_ms Average latency for the network connection checks to each broker since the last metric scrape
# TYPE heartbeat_connection_latency_ms gauge
"""
        for b in store.get('brokers'):
            txt += f"""heartbeat_connection_latency_ms{{broker="{b}", cluster_id="{store.get('cluster_info').cluster_id}", broker_ip="{store.get('broker_ip')[b]}"}} {store.get('connection_latency_ms')[b]:0.2f}\n"""

        # optionally: add consumer group lag?

        # clear the latencies - is this the right thing to do?
        store.resetMetrics()
        return web.Response(text=txt)

    app = web.Application()
    app.add_routes(routes)

    runner = web.AppRunner(app, access_log=ll)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
