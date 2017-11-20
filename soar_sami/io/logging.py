
import logging


class SAMIFormatter(logging.Formatter):
    """
    Custom Log Formatter for SAMI's messages.
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    err_fmt = FAIL + "[E]" + ENDC + " %(msg)s"
    dbg_fmt = OKBLUE + "[D]" + ENDC + " %(module)s: %(lineno)d: %(msg)s"
    info_fmt = "   %(msg)s"
    warn_fmt = WARNING + "[W]" + ENDC + " %(msg)s"

    def __init__(self, fmt="%(levelno)s: %(msg)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = SAMIFormatter.dbg_fmt

        elif record.levelno == logging.INFO:
            self._fmt = SAMIFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._fmt = SAMIFormatter.err_fmt

        elif record.levelno == logging.WARNING:
            self._fmt = SAMIFormatter.warn_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result


class SAMILog(logging.Logger):

    def __init__(self, name, verbose=True, debug=False):

        logging.Logger.__init__(self, name)

        # Set log format
        self.formatter = SAMIFormatter()

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