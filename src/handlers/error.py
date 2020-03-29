from loguru import logger


def log_error(update, context):
    logger.warning('Caught eror={}! \n update={}', context.error, update)
