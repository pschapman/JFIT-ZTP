"""
##                             JFIT-ZTP                              ##
##               JotForm Form Import Tool for freeZTP                ##

Author: Paul S. Chapman
Version: 2.0.1

Open Caveats / Bugs / Limitations: See README.md
To Do List: See README.md
"""
# Python native modules
import logging

# External modules.

# Private modules
from jfit_ztp import logger
from jfit_ztp import shared
from jfit_ztp import worker
from jfit_ztp import setup

LOG_NAME = 'jfit-ztp.log'
F_LEV = logging.INFO
# F_LEV = logging.DEBUG
CFG_NAME = 'datamap.json'

if __name__ == '__main__':
    setup_mode, test_mode, c_lev = shared.parse_args()
    logger.init_logging(LOG_NAME, file_level=F_LEV, console_level=c_lev)
    log = logging.getLogger(__name__)

    # Author's test harness. Disables ZTP updates and Jotform will be left
    # unread. (setup and process_data)
    if test_mode:
        log.info('Test Mode Enabled - No ZTP updates / JotForm left unread.')
    else:
        log.info('Test Mode Disabled')

    if setup_mode:
        setup.setup(CFG_NAME, test_mode)
    else:
        worker.process_data(CFG_NAME, test_mode)

    # main()
