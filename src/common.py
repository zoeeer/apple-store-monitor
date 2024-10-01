import logging
import os

log_formatter = logging.Formatter(
    '[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

is_debugging = os.environ.get('APP_DEBUG')
log_level = os.environ.get('APP_LOG_LEVEL', 'INFO')
if is_debugging:
    log_level = logging.DEBUG


def config_logger(logger_or_name, level=log_level):
    if isinstance(logger_or_name, str):
        logger = logging.getLogger(logger_or_name)
    else:
        logger = logger_or_name
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)

    return logger
