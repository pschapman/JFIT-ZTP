"""
Configures logging for all modules.
    Parameters:
        log_file (str): Relative or absolute path
        file_level (int): Logging level for file output
        console_level (int): Logging level for console output
    Returns:
        None

Modules instantiate logging with:

import logging
log = logging.getLogger(__name__)
"""
import logging

def init_logging(log_file, file_level, console_level=None):
    """
    Start up and configure logging
        Parameters:
            log_file = Log file location
            file_level = Logging level for file logging
            console_level = Logging level for console logging
    """
    # Create logger object
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s:'
        '%(funcName)s:%(lineno)s %(message)s', '%Y-%m-%d %H:%M:%S')

    # Create and configure file handler
    fh = logging.FileHandler(log_file) # pylint: disable=invalid-name
    fh.setLevel(file_level)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # Create and configure console handler, if needed
    if console_level:
        ch = logging.StreamHandler() # pylint: disable=invalid-name
        ch.setLevel(console_level)
        ch.setFormatter(formatter)
        log.addHandler(ch)
