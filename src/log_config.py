import logging

levels = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR }

def logger(log_name = 'cc-heartbeat.log', log_level = logging.INFO):
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s'))
    logger.addHandler(handler)
    return logger

