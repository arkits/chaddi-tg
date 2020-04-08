from loguru import logger


def log_error(update, context):
    logger.warning('Caught eror={}! \n update={} \n context={}', context.error, update, context)
