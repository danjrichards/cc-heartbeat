import asyncio
from time import time, sleep
from log_config import logger


def checkConnectivity(store):
    # store.brokers is populated by checkMetadata so wait until that's had a chance to run if we don't have brokers yet
    if len(store.get('brokers')) == 0:
        sleep(5)

    asyncio.run(checkConnectivityAsync(store))


async def checkConnectivityAsync(store):
    period = int(store.get('config')["admin"]["check.connectivity.period.seconds"] or 5)
    log = logger(__name__)
    log.info(f"checkConnectivity started - will run every {period} seconds")
    loop = asyncio.get_event_loop()
    timeout = 2

    class NoopProtocol(asyncio.Protocol):
        def connection_made(self, transport):
            nonlocal connection_made_time
            connection_made_time = time()
            transport.close()

    while True:
        start = time()
        brokers = store.get('brokers')
        for b in brokers:
            conn = None
            connection_made_time = None

            try:
                async with asyncio.timeout(timeout):
                    conn = await loop.create_connection(NoopProtocol, brokers[b].host, brokers[b].port)
                    # this next line returns the remote IP and port as a tuple - e.g. ('54.225.197.43', 9092)
                    sock = conn[0]._extra['peername']  # type: ignore
                    latency_ms = (time() - connection_made_time) * 1000000 if connection_made_time else -1
                    if sock is not None:
                        # result[brokers[b].host] = { "timestamp": time(), "ip": sock[0], "latency": latency_ms }
                        log.debug(f"✅ {brokers[b].host} = {sock[0]} - {latency_ms:0.2f}ms")
                        store.addConnectionCheck(b, latency_ms, sock[0])
                    else:
                        log.warning(f"Connection failed to {brokers[b].host}:{brokers[b].port}")
                        store.addConnectionCheck(b, timeout*1000)   # TODO: what's the right value to signify a failed connection that didn't time out?

            except TimeoutError:
                log.warning(f"Connection timed out to {brokers[b].host}:{brokers[b].port}")
                store.addConnectionCheck(b, timeout*1000)

        # take the elapsed time out of the repeat period and sleep for that long
        delay = time() - start
        if delay > 0 and delay < period:
            sleep(period - delay)
