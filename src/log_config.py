from os import path
import logging
from logging.handlers import RotatingFileHandler


def configureLogging(config):
    logger = logging.getLogger()

    # set logging level
    levels = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR }
    if "log.level" in config["admin"]:
        ll = levels.get(config["admin"]["log.level"])
    log_level=ll or levels.get('INFO')
    logger.setLevel(log_level) # type: ignore

    # files to log to
    f_stdout = 'cc-heartbeat.log'
    f_err = 'cc-heartbeat-error.log'
    filename = path.join(path.dirname(path.abspath(__file__)), f_stdout)
    handler = RotatingFileHandler(filename=filename, maxBytes=1048576, backupCount=10)

    # output format
    handler.setFormatter(logging.Formatter('%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s'))
    logger.addHandler(handler)
    return logger





# def configureLogging():
#   f_stdout = 'cc-heartbeat.log'
#   f_err = 'cc-heartbeat-error.log'
#   filename = path.join(path.dirname(path.abspath(__file__)), f_stdout)

#   LOGGING_CONFIG = {
#     'version': 1,
#     'loggers': {
#       '': {  # root logger
#         'level': 'NOTSET',
#         'handlers': ['debug_console_handler', 'info_rotating_file_handler', 'error_file_handler', 'critical_mail_handler'],
#       },
#       'my.package': {
#         'level': 'WARNING',
#         'propagate': False,
#         'handlers': ['info_rotating_file_handler', 'error_file_handler'],
#       },
#     },
#     'handlers': {
#       'debug_console_handler': {
#         'level': 'DEBUG',
#         'formatter': 'info',
#         'class': 'logging.StreamHandler',
#         'stream': 'ext://sys.stdout',
#       },
#       'info_rotating_file_handler': {
#         'level': 'INFO',
#         'formatter': 'info',
#         'class': 'logging.handlers.RotatingFileHandler',
#         'filename': f_stdout,
#         'mode': 'a',
#         'maxBytes': 1048576,
#         'backupCount': 10
#       },
#       'error_file_handler': {
#         'level': 'WARNING',
#         'formatter': 'error',
#         'class': 'logging.FileHandler',
#         'filename': f_err,
#         'mode': 'a',
#       }
#     },
#     'formatters': {
#       'info': {
#         'format': '%(asctime)s-%(levelname)s-%(name)s::%(module)s|%(lineno)s:: %(message)s'
#       },
#       'error': {
#         'format': '%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s'
#       },
#     },

#   }

#   return dictConfig(LOGGING_CONFIG)
