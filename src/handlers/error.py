from loguru import logger


def log_error(update, context):
    logger.warning('Caught error={}! \n update={} \n context={}', context.error, update)
    return
