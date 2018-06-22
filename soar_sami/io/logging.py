#!/usr/bin/env python
# -*- coding: utf8 -*-

import logging

__all__ = ['COLORS', 'get_logger', 'MyLogFormatter']

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

RESET_SEQ = '\033[0m'
COLOR_SEQ = '\033[1;%dm'
BOLD_SEQ = '\033[1m'

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': RED,
    'ERROR': RED
}


def get_logger(logger_name, use_color=True, overwrite=False):
    """
    Return a logger with the "logger_name".

    Args:
        logger_name (str) : the logger name to be used in different contexts.
        use_colors (bool, optional) : use colors on Stream Loggers.

    Returns:
        _logger (logging.Logger) : the logger to be used.
    """
    message_format = " [%(levelname).1s %(asctime)s %(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    _logger = logging.getLogger(logger_name)

    formatter = MyLogFormatter(message_format, datefmt=date_format, use_colours=use_color)

    if len(_logger.handlers) == 0:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(logging.DEBUG)

    return _logger


class MyLogFormatter(logging.Formatter):

    def __init__(self, fmt=" [%(levelname).1s %(asctime)s %(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
                 use_colours=True):

        logging.Formatter.__init__(self, fmt, datefmt=datefmt)
        self.use_colours = use_colours

    @staticmethod
    def color_format(message, levelname, left_char="[", right_char="]"):

        colour = COLOR_SEQ % (30 + COLORS[levelname])

        message = message.replace(left_char, "{:s} {:s}".format(colour, left_char))
        message = message.replace(right_char, "{:s} {:s}".format(right_char, RESET_SEQ))

        return message

    def format(self, record):

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        if self.use_colours:
            result = self.color_format(result, record.levelname)

        return result


if __name__ == "__main__":

    logger = get_logger('TestColor')
    logger.setLevel(logging.DEBUG)

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")