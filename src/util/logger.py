import coloredlogs, logging

logging_format = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"

def get_logger(className):

    logger = logging.getLogger(className)
    
    coloredlogs.install(
        fmt=logging_format,
        level='INFO'
    )
    
    return logger