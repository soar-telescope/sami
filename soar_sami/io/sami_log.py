
import logging

__all__ = ['SAMIFormatter', 'SAMILog']


class SAMIFormatter(logging.Formatter):
    """
    Custom Log Formatter for SAMI's messages.
    """
    def __init__(self, fmt="%(levelno)s: %(msg)s"):

        logging.Formatter.__init__(self, fmt)

        self.err_fmt = "[E] %(msg)s"
        self.dbg_fmt = "[D] %(module)s: %(lineno)d: %(msg)s"
        self.info_fmt = "    %(msg)s"
        self.warn_fmt = "[W] %(msg)s"

    def disable_colors(self):

        self.err_fmt = "[E] %(msg)s"
        self.dbg_fmt = "[D] %(module)s: %(lineno)d: %(msg)s"
        self.info_fmt = "    %(msg)s"
        self.warn_fmt = "[W] %(msg)s"

    def enable_colors(self):

        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

        self.err_fmt = FAIL + "[E]" + ENDC + " %(msg)s"
        self.dbg_fmt = OKBLUE + "[D]" + ENDC + " %(module)s: %(lineno)d: %(msg)s"
        self.info_fmt = "   %(msg)s"
        self.warn_fmt = WARNING + "[W]" + ENDC + " %(msg)s"

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = self.dbg_fmt

        elif record.levelno == logging.INFO:
            self._fmt = self.info_fmt

        elif record.levelno == logging.ERROR:
            self._fmt = self.err_fmt

        elif record.levelno == logging.WARNING:
            self._fmt = self.warn_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result

    def use_colors(self, colors):

        if colors:
            self.enable_colors()
        else:
            self.disable_colors()


class SAMILog(logging.Logger):

    def __init__(self, name, verbose=True, debug=False, use_colors=False):

        logging.Logger.__init__(self, name)

        # Set log format
        self.formatter = SAMIFormatter()
        self.formatter.use_colors(use_colors)

        # Set log handler to the terminal
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setFormatter(self.formatter)

        # Set the logger itself
        self.addHandler(self.stream_handler)

        if verbose:
            self.set_verbose()

        if debug:
            self.set_debug()

    def set_verbose(self, verbose=True):
        if verbose:
            self.setLevel(logging.INFO)
        else:
            self.setLevel(logging.NOTSET)

    def set_debug(self, debug=True):
        if debug:
            self.setLevel(logging.DEBUG)