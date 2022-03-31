#!/usr/bin/env python3
"""
Main worker process.
"""

# Python native modules
from os import path
import logging
import sys
import json
import csv
import subprocess

# External modules

# Private modules
from . import shared
from . import template_text as tmpl

# Begin logging inside module, parent initializes configuration
log = logging.getLogger(__name__)

def read_ext_keystore(ext_keystore_file):
    """
    Read external keystore fields / rows
        Parameters:
            ext_keystore_file (str): Absolute or relative path
        Returns:
            headers (list): Set of header values
                ex. ['keystore_id', 'var_1', 'var_x']
            csv_data (dict): Row data using 'keystore_id' as key value
                ex. {'MYHOST': {'keystore_id': 'myhost', 'var': 'value'}}
    """
    headers = None
    csv_data = None

    if path.exists(ext_keystore_file):
        with open(ext_keystore_file, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames
            csv_data = {}
            counter = 0
            # Create dictionary wrapper keyed on keystore_id.
            for row in reader:
                csv_data[row['keystore_id'].upper()] = row
                counter += 1
            log.info('Read %d line(s) from external keystore.', counter)

        log.debug('Imported external keystore from file, %s',  ext_keystore_file)

    else:
        log.warning('Referenced keystore is missing and execution mode is '
                    'CSV. Create keystore file or re-run setup.')

    return headers, csv_data

def write_ext_keystore(ext_keystore_file, headers, csv_data):
    """
    Update external keystore fields / rows from JotForm Data
        Parameters:
            ext_keystore_file (str): Absolute or relative path
            headers (list): Set of header values
                ex. ['keystore_id', 'var_1', 'var_x']
            csv_data (dict): Row data using 'keystore_id' as key value
                ex. {'MYHOST': {'keystore_id': 'myhost', 'var': 'value'}}
        Returns:
            None
    """
    counter = 0

    with open(ext_keystore_file, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        # Strip off dictionary wrapper and write data
        for value in csv_data.values():
            writer.writerow(value)
            counter += 1
        log.info('Wrote %d line(s) to external keystore.', counter)

def update_csv_data(csv_data, headers, keystore_id, csv_update):
    """
    Update row data
        Parameters:
            csv_data (dict): Row data using 'keystore_id' as key value
                ex. {'MYHOST': {'keystore_id': 'myhost', 'var': 'value'}}
            headers (list): Set of header values
                ex. ['keystore_id', 'var_1', 'var_x']
            keystore_id (str): ID value, typically device hostname
            csv_update (dict): var:data pairs to update csv_data entry
        Returns:
            headers (list): Header values, possibly updated
            csv_data (dict): Data with updated row for 'keystore_id'
    """
    data = csv_data[keystore_id.upper()]

    for key, value in csv_update.items():
        # On rare chance that source file is empty, create first header.
        # Only occurs if Import Unknown is enabled.
        if not headers:
            headers = ['keystore_id']
            log.warning('Blank external keystore found. Creating keystore_id '
                        'header.')
        # Check CSV headers for variable. Add if needed.
        if key not in headers:
            headers.append(key)
            log.debug('Header for "%s" missing. Adding now.', key)

        data.update({key: value})
        csv_data.update({keystore_id.upper(): data})
        log.debug('Updating "%s as %s for %s.', key, value, keystore_id)

    return headers, csv_data

def submission_to_cli(config, answer_set): # ans_set, data_map):
    """
    Generates ZTP CLI commands from JotForm Data
        Parameters:
            answer_set (dict): Set of answer dictionaries from Jotform
                ex. {'1': {'text': 'Question 1', 'answer': 'myhostname'}}
            config (dict): Full JFIT configuration
        Returns:
            cmd_set (list): Set of ZTP CLI commands to be issued.
                ex. ['ztp set idarray <name> <serial>', 'another ztp command']
            keystore_id (str): ID value, typically device hostname
    """
    cmd_set = []
    device_id_set = []

    # ex. {"keystore_id": {"a_id": "4", "a_idx": 1}}
    data_map = config['data_map']

    for key, value in data_map.items():
        q_id = answer_set[value['a_id']]
        ans_idx = value['a_idx']

        if 'keystore_id' in key:
            keystore_id = shared.get_answer_element(config, q_id, ans_idx)
            log.info('Processing submission for Keystore ID: %s', keystore_id)
            # continue
        elif 'idarray' in key:
            device_id = shared.get_answer_element(config, q_id, ans_idx)
            if device_id:
                device_id_set.append(device_id)
                log.debug('Device ID: %s',  device_id)
        elif 'association' in key:
            var_data = shared.get_answer_element(config, q_id, ans_idx)
            if var_data:
                cmd_set.append('ztp set association id ' + keystore_id
                               + ' template ' + var_data)
                log.debug('Association ID: %s',  var_data)
            else:
                # Default answer. Clear old association, if present.
                cmd_set.append('ztp clear association ' + keystore_id)
        else:
            var_data = shared.get_answer_element(config, q_id, ans_idx)
            var_name = key
            if var_data:
                cmd_set.append('ztp set keystore ' + keystore_id + ' '
                                  + var_name + ' ' + var_data)
                log.debug('Custom Variable: %s\t Value: %s', var_name, var_data)
            else:
                # Default answer. Clear old variable, if present.
                cmd_set.append('ztp clear keystore ' + keystore_id + ' '
                               + var_name)

    cmd_set.append('ztp set idarray ' + keystore_id + ' '
                   + ' '.join(device_id_set))
    log.info('Finished parsing values for %s',  keystore_id)
    return cmd_set, keystore_id

def submission_to_csv(config, answer_set, headers, csv_data): #, data_map, headers, csv_data):
    """
    Update external keystore fields / rows from JotForm Data
        Parameters:
            config (dict): Full JFIT configuration
            answer_set (dict): Set of answer dictionaries from Jotform
                ex. {'1': {'text': 'Question 1', 'answer': 'myhostname'}}
            headers (list): Set of header values
                ex. ['keystore_id', 'var_1', 'var_x']
            csv_data (dict): Row data using 'keystore_id' as key value
                ex. {'MYHOST': {'keystore_id': 'myhost', 'var': 'value'}}
        Returns:
            headers (list): Header values, possibly updated
            csv_data (dict): Data with updated row for 'keystore_id'
            True/False indicating whether changes were made (ztp restart)
            keystore_id (str): ID value, typically device hostname
    """
    import_unknown = config['import_unknown']
    data_map = config['data_map']
    csv_update = {}

    for key, value in data_map.items():
        q_id = answer_set[value['a_id']]
        ans_idx = value['a_idx']
        if 'keystore_id' in key:
            keystore_id = shared.get_answer_element(config, q_id, ans_idx)
            log.info('Processing submission for Keystore ID: %s',  keystore_id)
            # continue
        else:
            # If func returns None, then CSV field will be cleared.
            var_data = shared.get_answer_element(config, q_id, ans_idx)
            var_name = key
            csv_update.update({var_name: var_data})
            log.debug('Variable Name: %s\tValue: %s', var_name, var_data)

    # Create partial entry if Import Unknown is enabled
    if keystore_id.upper() not in csv_data and import_unknown:
        csv_data.update({keystore_id.upper(): {'keystore_id': keystore_id}})
        log.warning('Unknown ID, %s, added to external keystore. Incomplete'
                    ' data may cause merge issues.', keystore_id)

    # Skip item otherwise. Return unchanged data to calling code.
    elif keystore_id.upper() not in csv_data and not import_unknown:
        log.warning('Received unknown ID, %s, and Unknown Import is disabled.'
                    ' Item skipped / ignored.', keystore_id)
        return headers, csv_data, False, None

    # Apply change list to CSV Data
    headers, csv_data = update_csv_data(csv_data, headers,
                                        keystore_id, csv_update)

    log.info('Finished updating CSV values for %s',  keystore_id)
    return headers, csv_data, True, keystore_id

def exec_cmds(cmd_set):
    """
    Send freeZTP commands to system CLI
        Parameters:
            cmd_set (list): List of commands to send to freeZTP CLI
                ex. ['ztp set idarray <name> <serial>', 'another ztp command']
        Returns:
            [no var] (bool): True / False indicating success / failure
    """
    for command in cmd_set:
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]

    # Last command restarts ZTP. Verify status. Error check in calling code.
    if '(running)' in output:
        return True
    else:
        return False

def process_data(config_file, test_mode):
    """
    Operational data processing
    """
    cfg = shared.read_config(config_file)
    if not cfg:
        # Error logged in read_config
        sys.exit()

    restart_ztp = False
    submission_ids = []
    cmd_set = []

    response = shared.get_new_submissions(cfg['api_key'], cfg['form_id'])

    # Process data only if new entries exist
    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        response_count = response.json()['resultSet']['count']
        api_calls_left = response.json()['limit-left']

        log.debug('Full Jotform Response (JSON):\r\n%s',
                  json.dumps(response.json(), indent=4))
        log.info('New Submissions: %d', response_count)
        log.info('Remaining API Calls: %d', api_calls_left)

        if api_calls_left < response_count:
            log.warning('Insufficient remaining API calls to service current '
                  'submissions.  Stopping script without processing.')
            sys.exit()

        if cfg['keystore_type'] == 'csv':
            headers, csv_data = read_ext_keystore(cfg['csv_path'])
            if csv_data is None:
                # Error logged in read_ext_keystore
                sys.exit()

        # Loop through all entries
        for submission in response.json()['content']:
            # Build submission list.  Process all before marking as read.
            submission_ids.append(submission['id'])
            ans_set = submission['answers']
            # Prepare ZTP updates based on keystore method: cli or csv.
            if cfg['keystore_type'] == 'cli':
                more_cmds, keystore_id = submission_to_cli(cfg, ans_set)
                restart_ztp = True
                cmd_set.extend(more_cmds)
            else:
                headers, csv_data, change_flag, keystore_id = (
                    submission_to_csv(cfg, ans_set, headers, csv_data)
                )
                restart_ztp = True if change_flag else restart_ztp

            if cfg['bot_token'] and keystore_id:
                merge_dict = shared.build_merge_data(cfg)
                shared.send_webex_msg(merge_dict, tmpl.WEBEX_WORKER_MSG)

            if cfg['webhook_url'] and keystore_id:
                merge_dict = shared.build_merge_data(cfg)
                shared.send_webhook_msg(merge_dict, tmpl.WEBHOOK_WORKER_DICT)

        # Post processing tasks (e.g. restart ZTP)
        log.info('All submissions processed.')
        log.debug('Submission Set: %s', ' '.join(submission_ids))

        if restart_ztp:
            if cfg['keystore_type'] == 'csv' and csv_data:
                # Test harness to write to alternate external keystore file
                write_ext_keystore(cfg['csv_path'], headers, csv_data)
            elif cfg['keystore_type'] == 'csv' and not csv_data:
                log.warning('Referenced keystore empty (0 bytes) and Unknown '
                    'Import disabled. Stopping script without marking new '
                    'submissions as "read".')
                sys.exit()

            cmd_set.append('ztp service restart')
            log.debug('Commands to be sent to freeZTP CLI:\r\n%s',
                      '\r\n'.join(cmd_set))
            if not test_mode:
                exec_cmds(cmd_set)
                log.info('%d command(s) successfully sent to freeZTP CLI.',
                         len(cmd_set))
                response = shared.mark_submissions_read(cfg['api_key'], submission_ids)
                if not response:
                    log.info('Submissions successfully marked as read.')
                else:
                    log.warning('Submissions failed to be marked as read.')

        else:
            log.info('No data changes! ZTP not restarted.')

    elif response.status_code == 200:
        log.debug('Full Jotform Response (JSON):\r\n%s',
                  json.dumps(response.json(), indent=4))
        log.info('No new submissions!')
    else:
        log.warning('Jotform Response & Headers (Plain):\r\n%s',
                  response.text + '\r\n\r\n' + response.headers)

    log.info('Script Execution Complete')
