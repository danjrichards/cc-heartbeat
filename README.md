# Confluent Cloud Heartbeat Health Check

An app to monitor a Confluent Cloud cluster, and:
- verify each broker in a CC cluster is reachable
- verify messages can be produced and consumed
- output latency figures in OpenTelemetry format

In CC the replication factor is always 3 and can't be changed, so we can't ensure a topic has a partition on every broker in a cluster.  Instead, we can do a network connectivity check to each broker, and have a heartbeat of topic produce/consume to verify end-to-end functioning of the cluster and networks between client and brokers.


## Setup
Copy `example_config.ini` to `config.ini` and enter the cluster bootstrap URL and authentication details

```sh
python3 -m venv ./venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python src/app.py
```


## Example OpenTelemetry response
```yaml
# Confluent Cloud heartbeat metrics
# HELP heartbeat_controller The cluster controller broker ID
# TYPE heartbeat_controller gauge
heartbeat_controller{cluster_id=lkc-z306v3} 2
# HELP heartbeat_messages_produced Count of messages produced since the last metric scrape
# TYPE heartbeat_messages_produced counter
heartbeat_messages_produced{cluster_id=lkc-z306v3} 44
# HELP heartbeat_avg_produce_latency_ms Average latency for the messages produced since the last metric scrape
# TYPE heartbeat_avg_produce_latency_ms gauge
heartbeat_avg_produce_latency_ms{cluster_id=lkc-z306v3} 93.12
# HELP heartbeat_messages_consumed Count of messages consumed since the last metric scrape
# TYPE heartbeat_messages_consumed counter
heartbeat_messages_consumed{cluster_id=lkc-z306v3} 46
# HELP heartbeat_avg_consume_latency_ms Average end-to-end latency for the messages consumed since the last metric scrape
# TYPE heartbeat_avg_consume_latency_ms gauge
heartbeat_avg_consume_latency_ms{cluster_id=lkc-z306v3} 251.95
# HELP heartbeat_broker_count Count of brokers
# TYPE heartbeat_broker_count counter
heartbeat_broker_count{cluster_id=lkc-z306v3} 4
# HELP heartbeat_connection_check_count Count of network connection checks to the brokers since the last metric scrape
# TYPE heartbeat_connection_check_count counter
heartbeat_connection_check_count{cluster_id=lkc-z306v3} 8
# HELP heartbeat_connection_latency_ms Average latency for the network connection checks to each broker since the last metric scrape
# TYPE heartbeat_connection_latency_ms gauge
heartbeat_connection_latency_ms{broker=0, cluster_id=lkc-z306v3, broker_ip=54.226.213.183} 299.36
heartbeat_connection_latency_ms{broker=1, cluster_id=lkc-z306v3, broker_ip=54.165.2.234} 180.70
heartbeat_connection_latency_ms{broker=2, cluster_id=lkc-z306v3, broker_ip=54.208.145.132} 130.14
heartbeat_connection_latency_ms{broker=3, cluster_id=lkc-z306v3, broker_ip=52.44.8.37} 106.34
```


## Example log output
```log
2024-06-03 12:56:42,481 INFO     Starting cc-heartbeat against pkc-5roon.us-east-1.aws.confluent.cloud:9092
2024-06-03 12:56:44,362 INFO     4 brokers in lkc-z306v3 - controller is -1
2024-06-03 12:56:44,362 INFO       0: name: b0, rack: use1-az5
2024-06-03 12:56:44,362 INFO       1: name: b1, rack: use1-az5
2024-06-03 12:56:44,362 INFO       2: name: b2, rack: use1-az5
2024-06-03 12:56:44,362 INFO       3: name: b3, rack: use1-az5
2024-06-03 12:56:44,362 INFO     checkTopic started - will run every 3600 seconds
2024-06-03 12:56:44,362 INFO     checkMetadata started - will run every 60 seconds
2024-06-03 12:56:44,363 INFO     producer started - messages will be sent every 1 seconds
2024-06-03 12:56:44,363 INFO     consumer started
2024-06-03 12:56:44,393 INFO     promExporter started - listening on localhost:8080
%4|1717415807.161|OFFSET|rdkafka#consumer-3| [thrd:main]: cc-heartbeat [0]: offset reset (at offset 554 (leader epoch 0), broker 1) to offset END (leader epoch -1): fetch failed due to requested offset not available on the broker: Broker: Offset out of range
%4|1717415807.261|OFFSET|rdkafka#consumer-3| [thrd:main]: cc-heartbeat [1]: offset reset (at offset 559 (leader epoch 0), broker 2) to offset END (leader epoch -1): fetch failed due to requested offset not available on the broker: Broker: Offset out of range
2024-06-03 12:56:49,366 INFO     checkConnectivity started - will run every 5 seconds
...
```

It's expected to get the "Offset out of range" errors on initial startup.


## TODO:
- [fetch topic offsets](https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/get_watermark_offsets.py)

- [fetch consumer group lags](https://medium.com/@satadru1998/monitoring-kafka-topic-consumer-lag-efficiently-using-python-airflow-435e9651c4f1)

- consider schema registry monitoring too?

