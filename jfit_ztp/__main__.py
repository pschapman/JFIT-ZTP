#!/usr/bin/env python3
"""
JFIT-ZTP - JotForm Form Import Tool for freeZTP
https://github.com/pschapman/JFIT-ZTP
"""
# Python native modules
import logging

# External modules.

# Private modules
from . import logger
from . import shared
from . import worker
from . import setup

CFG_NAME = 'datamap.json'
LOG_NAME = 'jfit-ztp.log'
F_LEV = logging.INFO
# F_LEV = logging.DEBUG

def main():
    """ Main """
    setup_mode, test_mode, c_lev = shared.parse_args()
    logger.init_logging(LOG_NAME, file_level=F_LEV, console_level=c_lev)
    log = logging.getLogger(__name__)

    if test_mode:
        log.info('Test Mode: No ZTP updates / JotForm left unread.')
    else:
        log.info('Prod Mode')

    if setup_mode:
        setup.setup(CFG_NAME, test_mode)
    else:
        worker.process_data(CFG_NAME, test_mode)

if __name__ == '__main__':
    main()
