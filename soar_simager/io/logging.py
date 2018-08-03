#!/usr/bin/env python
# -*- coding: utf8 -*-

# ToDo - Implement logging to file

import logging as _logging

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

LOG_FORMAT = " [%(levelname).1s %(asctime)s %(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(logger_name, use_color=True, message_format=LOG_FORMAT):
    """
    Return a logger with the "logger_name".

    Args:
        logger_name (str) : the logger name to be used in different contexts.

        use_color (bool, optional) : use colors on Stream Loggers.

        message_format (str, optional) : change the logger format.

    Returns:
        _logger (logging.Logger) : the logger to be used.
    """
    _logger = _logging.getLogger(logger_name)

    date_format = DATE_FORMAT

    formatter = MyLogFormatter(
        message_format, datefmt=date_format, use_colours=use_color)

    if len(_logger.handlers) == 0:

        handler = _logging.StreamHandler()
        handler.setFormatter(formatter)

        _logger.addHandler(handler)
        _logger.setLevel(_logging.INFO)

    return _logger


class MyLogFormatter(_logging.Formatter):

    def __init__(self, fmt=LOG_FORMAT, datefmt=DATE_FORMAT, use_colours=True):
        _logging.Formatter.__init__(self, fmt, datefmt=datefmt)
        self.use_colours = use_colours

    @staticmethod
    def color_format(message, levelname, left_char="[", right_char="]"):

        colour = COLOR_SEQ % (30 + COLORS[levelname])

        message = message.replace(left_char, "{:s} {:s}".format(colour, left_char))
        message = message.replace(right_char, "{:s} {:s}".format(right_char, RESET_SEQ))

        return message

    def format(self, record):

        # Call the original formatter class to do the grunt work
        result = _logging.Formatter.format(self, record)

        if self.use_colours:
            result = self.color_format(result, record.levelname)

        return result


if __name__ == "__main__":

    logger = get_logger('TestColor')
    logger.setLevel(_logging.DEBUG)

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")