""" blah """

# Python native modules
from os import path
import logging
import argparse
import json

# Begin logging inside module, parent initializes configuration
log = logging.getLogger(__name__)

def parse_args():
    """
    Start argparse to provide help and read back CLI arguments
        Returns:
            args.setup (bool): State of setup mode parameter
            args.test (bool): State of test mode parameter
            console_log_level (str): Logging level for console
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--setup', action='store_true', help='Run setup')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print informational messages to console')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print debug messages to console')
    # Hidden option(s)
    parser.add_argument('-t', '--test', action='store_true',
                        help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.debug:
        console_log_level = logging.DEBUG
    elif args.verbose:
        console_log_level = logging.INFO
    else:
        console_log_level = None

    return args.setup, args.test, console_log_level

def read_config(config_file):
    """
    Read config file and return dictionary. Return none if file absent.
        Parameters:
            config_file (str): Relative or absolute path.
        Returns:
            config (dict): {
                'api_key': '<key>'
                '<vars>': '<values>'
                'data_map': {<map>}
                }
    """
    config = None
    if path.exists(config_file):
        with open(config_file, encoding='utf-8') as cfg_file:
            config = json.load(cfg_file)
        log.debug('Imported configuration from file, %s',  config_file)
    else:
        log.info('Unable to import configuration. Run setup.')

    return config
