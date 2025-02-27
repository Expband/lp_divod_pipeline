from loguru import logger


class LoguruLogger:
    def __init__(self):
        logger.add(
            "logs/info.log",
            rotation="10 MB",
            retention="30 days",
            level="INFO",
            colorize=True
            )
        logger.add(
            "logs/error.log",
            rotation="30 MB",
            retention="100 days",
            level="ERROR",
            colorize=True
        )

    @property
    def logger(self):
        return logger
