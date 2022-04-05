#!/usr/bin/env python3
"""
Functions used by multiple modules.
"""

# Python native modules
from os import path
import logging
import argparse
import json
from urllib.parse import quote
import socket

# External modules
import requests
from jinja2 import Template as jinja

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

def file_read_config(config_file):
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
        log.info('Unable to import configuration.')

    return config

def get_new_submissions(api_key, form_id):
    """
    Query JotForm for new Submissions
        Parameters:
            api_key (hex): Jotform API Key value
            form_id (int): Jotform Form ID value
        Returns:
            response (str): Requests Response object with all properties.
    """
    base_url = 'https://api.jotform.com/form'
    api_filter = quote('{"status":"ACTIVE","new":"1"}')
    url = (f'{base_url}/{form_id}/submissions?filter={api_filter}')
    headers = {'APIKEY': api_key}
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload)
    # Error checking in calling code.
    return response

def mark_submissions_read(api_key, submission_ids):
    """
    Query JotForm for new Submissions
        Parameters:
            api_key (hex): Jotform API Key value
            submission_ids (list): Set of Submission IDs to mark 'read'
                ex. ['<numeric string>', '<numeric string>']
        Returns:
            err_state (bool): True means 1 or more updates failed.
    """
    err_set = None
    err_state = False
    headers = {'APIKEY': api_key}
    payload = {'submission[new]': '0'}
    for item in submission_ids:
        url = (f'https://api.jotform.com/submission/{item}')
        response = requests.request('POST', url, headers=headers, data=payload)
        if response.status_code != 200:
            err_set += f'\r\n{response.text}'
            err_state = True
            log.warning('HTTP response from Jotform not 200. Full response '
                        'text:\r\n%s\r\n\r\nActual status code: %d',
                        response.text, response.status_code)

    # Error checking in calling code.
    return err_state

def get_answer_data(config, answer_dict, ans_idx):
    """
    Extract answer string. (Or answer substring, if delimiter present.)
        Parameters:
            ans_dict (dict): Jotform response data for a question
                ex. {'text': 'Question 2', 'answer': 'myserial : mymodel'}
            ans_idx (int): Index of sub-answer. 0 for first/only, or n for
            specific element of split string.
        Returns:
            sub_answer (str): Answer string or substring.
    """
    null_answer = config['null_answer']
    delimiter = config['delimiter']
    full_answer = answer_dict['answer']
    split_answer = full_answer.split(delimiter)
    sub_answer = None

    log.debug('Full Answer Text from JotForm: %s',  full_answer)

    if ans_idx + 1 > len(split_answer) and full_answer != null_answer:
        log.warning('JotForm answer has %d elements. Data map looking for'
                    ' value in element %d. Possible delimiter mismatch'
                    ' or Data Map is wrong. Re-run setup to alter Data Map.',
                    len(split_answer), (ans_idx + 1))

    elif full_answer != null_answer:
        answer_element = full_answer.split(delimiter)[int(ans_idx)]
        sub_answer = answer_element.strip()
        log.debug('Parsed "%s" from full answer.', answer_element)

    else:
        log.debug('Null answer found. Nothing returned to calling code.')

    return sub_answer


def build_merge_data(cfg, ks_id=None, sub_id=None):
    """
    Creates special dictionary for notification Jinja2 merges. Contains both
    configuration plus additional useful fields.
        Parameters:
            cfg (dict): Current configuration data
            ks_id (str): Keystore ID (typically hostname)
            sub_id (str): Jotform submission ID
        Returns:
            merge_dict (dict): Combined items + uniques defined here
    """
    merge_dict = cfg.copy()
    merge_dict['keystore_id'] = ks_id
    merge_dict['submission_id'] = sub_id
    merge_dict['host_fqdn'] = (socket.getfqdn().lower())
    return merge_dict

def send_webex_msg(merge_dict, template):
    """
    Query JotForm for new Submissions
        Parameters:
            markdown = '<message text in markdown format>'
            bot_token = '<string>'
            room_id = '<hex string>'
    """
    bot_token = merge_dict['bot_token']
    room_id = merge_dict['room_id']

    markdown = jinja(template).render(merge_dict)
    payload = json.dumps({'roomId': room_id, 'markdown': markdown})

    url = 'https://webexapis.com/v1/messages'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bot_token}'
        }
    response = requests.request('POST', url, headers=headers, data=payload)

    log.debug('Attempting to send message to Teams Room')

    if response.status_code != 200:
        log.warning('Send to WebEx Room Failed. Response Text:\r\n%s\r\n\r\n'
                    'Status Code: %d', response.text, response.status_code)

def send_webhook_msg(merge_dict, template):
    """
    Send HTTP POST to webhook URL
        Parameters:
            config (dict): Current configuration data
            template (str): JSON payload template. Optional jinja tags.
        Returns:
    """
    tmpl_json = json.dumps(template)
    payload = jinja(tmpl_json).render(merge_dict)

    url = merge_dict['webhook_url']
    headers = {'Content-Type': 'application/json'}
    response = requests.request('POST', url, headers=headers, data=payload)

    log.debug('Trying to send message to webhook: %s', url)

    if response.status_code not in range (200,299):
        log.warning('Send to webhook failed. Response text:\r\n%s'
                    '\r\n\r\nStatus Code: %d', response.text,
                    response.status_code)
