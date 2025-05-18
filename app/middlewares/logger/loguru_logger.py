from loguru import logger
import os


class LoguruLogger:
    def __init__(self):
        pid: int = os.getpid()
        logger.add(
            f"logs/info{pid}.log",
            retention="30 days",
            level="INFO",
            colorize=True,
            enqueue=True
            )
        logger.add(
            f"logs/error{pid}.log",
            retention="100 days",
            level="ERROR",
            colorize=True,
            enqueue=True
        )

    @property
    def logger(self):
        return logger
