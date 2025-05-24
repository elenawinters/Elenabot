import structlog
import logging.config
import logging
import sys
import io

timestamper = structlog.processors.TimeStamper(fmt='iso')
pre_chain = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.ExtraAdder(),
    timestamper,
]

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=False),
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "class": "logging.handlers.WatchedFileHandler",
                "filename": "debug.log",
                "formatter": "plain",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "propagate": True,
            },
        },
    }
)
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# class DebugFilter(logging.Filter):
#     def filter(self, record):
#         if record.levelno >= 30:
#             return True
#         elif record.levelno > 10:
#             return False
#         return True

# you can write your own configuration if you want to, not here though. do it in your own class
# def configure_logger(_level=logging.INFO) -> None:
#     log.setLevel(_level)
#     handler = logging.StreamHandler(sys.stdout)
#     handler.setLevel(_level)
#     log.addHandler(handler)
#     d_log = logging.FileHandler('debug.log')
#     d_log.addFilter(DebugFilter())
#     d_log.setLevel(_level)
#     log.addHandler(d_log)


class LoggerConfig:
    def __init__(self, name: str, level: int = logging.INFO, stream: io.TextIOBase = sys.stdout):
        self.name = name
        self.level = level
        self.stream = stream

    def get_logger(self):
        logger = structlog.get_logger(self.name)
        logger.setLevel(self.level)
        # Set up the underlying stdlib logger to respect level and handlers
        # std_logger = logging.getLogger(self.name)
        # std_logger.setLevel(self.level)
        # handler = logging.StreamHandler(self.stream)
        # handler.setLevel(self.level)
        # std_logger.handlers = [handler]

        # # File handler without color codes
        # file_handler = logging.FileHandler('debug.log', encoding='utf-8')
        # file_handler.addFilter(DebugFilter())
        # file_handler.setLevel(self.level)
        # # Use a plain formatter (no color codes)
        # plain_formatter = logging.Formatter(
        #     fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        #     datefmt="%Y-%m-%d %H:%M:%S"
        # )
        # file_handler.setFormatter(plain_formatter)
        # std_logger.addHandler(file_handler)

        return logger