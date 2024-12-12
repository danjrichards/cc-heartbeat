from threading import Lock

class HeartbeatStore:
    def __init__(self, config):
        self.store = {
            "config": config,
            "topic": config["admin"]["heartbeat.topic"] or "cc-heartbeat",
            "cluster_info": {},
            "metadata": {},
            "brokers": [],
            "broker_ip": {},
            "consumer_groups": {},
            "connection_checks": 0,
            "connection_checks_delta": 0,     # count since last metrics scrape
            "connection_latency_ms": {},
            "messages_produced": 0,
            "messages_produced_delta": 0,
            "average_produce_latency_ms": 0,
            "messages_consumed": 0,
            "messages_consumed_delta": 0,
            "average_consume_latency_ms": 0
        }
        self.lock = Lock()  # this will be blocking

    def resetMetrics(self):
        # don't reset the connection_checks, messages_produced and messages_consumed counters
        #  - we can use rate() in Grafana to plot these at the desired granularity
        # use deltas instead to help calcaulate the rolling average
        # 
        # if metrics are scraped too frequently then some numbers will be zero, so don't reset them
        with self.lock:
            if self.store['connection_checks_delta'] > 0:
                self.store['connection_checks_delta'] = 0
                self.store['connection_latency_ms'] = {}
                for b in self.store['brokers']:
                    self.store['connection_latency_ms'][b] = 0
            if self.store['messages_produced_delta'] > 0:
                self.store['messages_produced_delta'] = 0
                self.store['average_produce_latency_ms'] = 0
            if self.store['messages_consumed_delta'] > 0:
                self.store['messages_consumed_delta'] = 0
                self.store['average_consume_latency_ms'] = 0

    def get(self, key): 
        return self.store[key] 

    def setClusterInfo(self, cluster_info):
        with self.lock:
            self.store['cluster_info'] = cluster_info

    def setMetadata(self, metadata):
        with self.lock:
            self.store['metadata'] = metadata
            self.store['brokers'] = metadata.brokers
            # self.store['controller'] = metadata.controller_id

    def setConsumerGroups(self, consumer_groups):
        with self.lock:
            self.store['consumer_groups'] = consumer_groups

    def addConnectionCheck(self, broker, latency, broker_ip=''):
        if broker not in self.store['connection_latency_ms']:
            with self.lock:
                self.store['connection_checks'] = 1
                self.store['connection_checks_delta'] = 1
                self.store['connection_latency_ms'][broker] = latency
                self.store['broker_ip'][broker] = broker_ip
        else:
            prev_checks = self.store['connection_checks_delta']
            prev_latency = self.store['connection_latency_ms'][broker]
            rolling_avg = ((prev_checks * prev_latency) + latency) / (prev_checks + 1)
            with self.lock:
                self.store['connection_latency_ms'][broker] = rolling_avg
                self.store['connection_checks'] += 1
                self.store['connection_checks_delta'] += 1
                self.store['broker_ip'][broker] = broker_ip

    def addProduce(self, latency):
        with self.lock:
            self.store['messages_produced'] += 1
            self.store['messages_produced_delta'] += 1
            self.store['average_produce_latency_ms'] = latency

    def addConsume(self, latency):
        prev_consumed = self.store['messages_consumed_delta']
        prev_latency = self.store['average_consume_latency_ms']
        rolling_avg = ((prev_consumed * prev_latency) + latency) / (prev_consumed + 1)
        with self.lock:
            self.store['messages_consumed'] += 1
            self.store['messages_consumed_delta'] += 1
            self.store['average_consume_latency_ms'] = rolling_avg
