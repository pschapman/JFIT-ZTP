#!/usr/bin/env python3
"""
User interactive application setup. Creates JotForm to ZTP variable mappings
to be used by the main script process.
"""

# Python native modules
import logging
from os import path
import json
from urllib.parse import quote

# External modules
import requests
from jinja2 import Template as jinja

# Private modules
from . import shared
from . import menu_text as menus
from . import help_text
from . import template_text as tmpl

# Begin logging inside module, parent initializes configuration
log = logging.getLogger(__name__)

def setup(config_file, mode): # pylint: disable=unused-argument
    """
    Initial setup wizard
    """
    config = shared.file_read_config(config_file)
    if not config:
        config = initialize_config()

    menu_main(config_file, config, mode, bc_path='')

def initialize_config():
    """
    Create config variable with minimum required entries. All set None.
        Returns:
            config (dict): Baseline config dictionary
    """
    config = {'api_key': None,
              'form_id': None,
              'delimiter': ":",
              'keystore_type': "cli",
              'csv_path': None,
              'import_unknown': False,
              'null_answer': "Select From List",
              'bot_token': None,
              'room_id': None,
              'webhook_url': None,
              'max_stack_size': 1,
              'data_map': {}}
    return config

def menu_main(config_file, config, mode, bc_path):
    """
    Main Control Menu. All setup controlled from here.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    # Menu path breadcrumbs
    bc_path += '\r\nMAIN'
    err_state = True
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_MAIN).render(
            api_key = config['api_key'],
            form_id = config['form_id'],
            keystore_type = config['keystore_type'].upper(),
            delimiter = config['delimiter'],
            null_answer = config['null_answer']
        )
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            config = menu_jotform_main(config, bc_path)
        elif selection == '2':
            config = menu_keystore_main(config, bc_path)
        elif selection == '3':
            config = menu_datamap_main(config, mode, bc_path)
        elif selection == '4':
            config = prompt_delimiter(config)
        elif selection == '5':
            config = prompt_null_answer(config)
        elif selection == '6':
            config = menu_webex_main(config, bc_path)
        elif selection == '7':
            config = menu_webhook_main(config, bc_path)
        elif selection.lower() == 's':
            file_save_config(config_file, config)
        elif selection.lower() == 'q':
            file_save_config(config_file, config)
            err_state = False
        elif selection.lower() == 'a':
            ans = input('Quit without saving? (y/N)')
            if ans.lower() == 'y':
                err_state = False

def menu_jotform_main(config, bc_path):
    """
    Jotform connection configuration menu. Key value must be hex, and 1..40
    characters.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_JOTFORM_MENU)
    bc_path += '/JOTFORM CNXN'
    err_state = True
    test_state = "Untested"
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_JOTFORM).render(
            api_key = config['api_key'],
            form_id = config['form_id'],
            test_result = test_state
        )
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            ans = input("Input API Key (Hex string): ").strip()
            # No input checks intentional. Test facility will reveal issues.
            config['api_key'] = ans
        elif selection == '2':
            test_state = test_jotform_api_key(config['api_key'])
        elif selection == '3':
            config = select_form_id(config)
        elif selection.lower() == 'h':
            print(help_text.HELP_JOTFORM_MENU)
        elif selection.lower() == 'q':
            err_state = False

    return config

def menu_keystore_main(config, bc_path):
    """
    JFIT Execution Mode configuration menu.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_KEYSTORE_CONFIG_MENU)
    bc_path += '/KEYSTORE TYPE'
    err_state = True
    toggle_mode = config['keystore_type']
    toggle_unknown = config['import_unknown']
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_KEYSTORE_TYPE).render(
            keystore_type = toggle_mode.upper() ,
            csv_path = config['csv_path'],
            import_unknown = toggle_unknown
        )
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            toggle_mode = 'csv' if toggle_mode == 'cli' else 'cli'
        elif selection == '2':
            config['csv_path'] = prompt_csv_path()
        elif selection == '3':
            toggle_unknown = not toggle_unknown
        elif selection.lower() == 'h':
            print(help_text.HELP_KEYSTORE_CONFIG_MENU)
        elif selection.lower() == 'q':
            config['keystore_type'] = toggle_mode
            config['import_unknown'] = toggle_unknown
            err_state = False

    return config

def menu_datamap_main(config, mode, bc_path):
    """
    Webhook Notifications configuration menu.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_DATAMAP_MAIN_MENU)
    bc_path += '/DATAMAP MAIN'
    sample_file = 'datasample.json'
    sample, dwnld_state = file_read_sample(sample_file)
    err_state = True
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_DATAMAP_MAIN).render(
            mss = int(config['max_stack_size']),
            sample_state = dwnld_state
        )
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            config = prompt_stack_size(config)
        elif selection == '2':
            sample, dwnld_state = select_submission(config, sample_file)
            if mode:
                args = (config['api_key'], [sample['id']])
                _ = shared.mark_submissions_read(*args)
        elif selection == '3' and sample:
            config = menu_dm_basic_mappings(config, sample, bc_path)
        elif selection == '4' and sample:
            config = menu_dm_custom_mappings(config, sample, bc_path)
        elif selection.lower() == 'x':
            ans = input('Are you sure? (y/N): ')
            if ans.lower() == 'y':
                config['data_map'] = {}
        elif selection.lower() == 'h':
            print(help_text.HELP_DATAMAP_MAIN_MENU)
        elif selection.lower() == 'q':
            err_state = False

    return config

def menu_dm_basic_mappings(config, sample, bc_path):
    """
    Keystore ID and ID Array mapping menu.
        Parameters:
            config (dict): Current configuration data
            sample (dict): Jotform sample submission data
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.HELP_DATAMAP_MANDATORY_MENU)
    bc_path += '/BASIC MAPPINGS'
    mss = int(config['max_stack_size'])
    menu_opts, meta_list = build_select_data(sample)
    data_map = config['data_map']

    err_state = True
    while err_state:
        var = None
        # Update dynamic menu parts
        render_dict = build_menu_dm_basic(data_map, mss)
        menu = jinja(menus.M_DATAMAP_MANDATORY).render(render_dict)
        while '\n\n' in menu:
            menu = menu.replace('\n\n', '\n')
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            var = 'keystore_id'
        elif selection == '2':
            var = 'idarray_1'
        elif mss >= 2 and selection == '3':
            var = 'idarray_2'
        elif mss >= 3 and selection == '4':
            var = 'idarray_3'
        elif mss >= 4 and selection == '5':
            var = 'idarray_4'
        elif mss >= 5 and selection == '6':
            var = 'idarray_5'
        elif mss >= 6 and selection == '7':
            var = 'idarray_6'
        elif mss >= 7 and selection == '8':
            var = 'idarray_7'
        elif mss >= 8 and selection == '9':
            var = 'idarray_8'
        elif selection.lower() == 'h':
            print(help_text.HELP_DATAMAP_MANDATORY_MENU)
        elif selection.lower() == 'q':
            err_state = False
            config['data_map'] = data_map.copy()

        if var:
            args = (config, sample, menu_opts, meta_list, var)
            map_dict = select_q_a_combo(*args)
            data_map.update({var: map_dict})

    return config

def menu_dm_custom_mappings(config, sample, bc_path):
    """
    Custom variable mapping menu.
        Parameters:
            config (dict): Current configuration data
            sample (dict): Jotform sample submission data
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.HELP_DATAMAP_CUSTOM_MENU)
    bc_path += '/CUSTOM MAPPINGS'
    menu_opts, meta_list = build_select_data(sample)
    data_map = config['data_map']

    err_state = True
    while err_state:
        var = None
        # Update dynamic menu parts
        render_data, var_list = build_menu_dm_custom(data_map)
        menu = jinja(menus.M_DATAMAP_CUSTOM).render(settings=render_data)
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            var = input('Input Custom Variable Name (No spaces): ')
            if not var or ' ' in var:
                print('Incorrect data entry. Try again.')
                var = None
        elif selection == '2':
            ans = menu_generic_select(var_list, 'CUSTOM VARIABLES')
            if ans is not None:
                data_map.pop(var_list[ans], None)
        elif selection.lower() == 't':
            print(help_text.INFO_ASSOCIATION)
            var = 'association'
        elif selection.lower() == 'h':
            print(help_text.HELP_DATAMAP_CUSTOM_MENU)
        elif selection.lower() == 'q':
            err_state = False
            config['data_map'] = data_map.copy()

        if var:
            args = (config, sample, menu_opts, meta_list, var)
            map_dict = select_q_a_combo(*args)
            data_map.update({var: map_dict})

    return config

def menu_webex_main(config, bc_path):
    """
    WebEx Teams Notifications configuration menu.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_WEBEX_MENU)
    bc_path += '/WEBEX INTEGRATION'
    err_state = True
    test_state = "Untested"
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_WEBEX).render(
            bot_token = config['bot_token'],
            test_result = test_state,
            room_id = config['room_id']
        )
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            ans = input("Input WebEx Teams Bot Token: ").strip()
            # No input checks intentional. Test facility will reveal issues.
            config['bot_token'] = ans
        elif selection == '2':
            test_state = test_webex_bot_token(config['bot_token'])
        elif selection == '3':
            config = select_room_id(config)
        elif selection == '4':
            merge_dict = shared.build_merge_data(config)
            shared.send_webex_msg(merge_dict, tmpl.WEBEX_SETUP_MSG)
        elif selection.lower() == 'x':
            config['bot_token'] = None
            config['room_id'] = None
        elif selection.lower() == 'h':
            print(help_text.HELP_WEBEX_MENU)
        elif selection.lower() == 'q':
            if config['bot_token'] and config['room_id']:
                err_state = False
            else:
                print(help_text.WARN_WEBEX_MENU)
                ans = input("Exit and clear config? (y/N)")
                if ans.lower() == 'y':
                    config['bot_token'] = None
                    config['room_id'] = None
                    err_state = False

    return config

def menu_webhook_main(config, bc_path):
    """
    Webhook Notifications configuration menu.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_WEBHOOK_URL_MENU)
    bc_path += '/WEBHOOK INTEGRATION'
    err_state = True
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_WEBHOOK).render(
            webhook_url = config['webhook_url']
        )
        print(menu)
        selection = input(f'{bc_path} > ')

        if selection == '1':
            ans = input("Input Webhook URL ([enter] for None): ").strip()
            # No input checks intentional. Test facility will reveal issues.
            config['webhook_url'] = ans
        elif selection == '2':
            merge_dict = shared.build_merge_data(config)
            # Render template in the same was as notification
            tmpl_json = json.dumps(tmpl.WEBHOOK_SETUP_DICT, indent=4)
            payload = jinja(tmpl_json).render(merge_dict)
            print(f'\r\n{payload}\r\n')
        elif selection == '3':
            merge_dict = shared.build_merge_data(config)
            shared.send_webhook_msg(config, tmpl.WEBHOOK_SETUP_DICT)
        elif selection.lower() == 'h':
            print(help_text.HELP_WEBHOOK_URL_MENU)
        elif selection.lower() == 'q':
            err_state = False

    return config

def prompt_delimiter(config):
    """
    Simple question. Ask for new delimiter or accept current.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_DELIMITER_QUESTION)
    err_state = True
    delim = config['delimiter']
    prompt = f'Input single character delimiter ([enter] for "{delim}"): '
    while err_state:
        ans = input(prompt).strip()
        if not ans:
            err_state = False
        elif len(ans) == 1:
            config['delimiter'] = ans
            err_state = False
        else:
            print('Delimeter length not 1. Space not permitted. Try again.')

    return config

def prompt_null_answer(config):
    """
    Simple question. Ask for new null answer or accept current.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_NULL_ANSWER_QUESTION)
    null_ans = config['null_answer']
    prompt = f'Input null answer string ([enter] for {null_ans}): '
    ans = input(prompt).strip()
    config['null_answer'] = ans

    return config

def prompt_csv_path():
    """
    Ask user for external keystore path. Validate existance. Retry as needed.
        Returns:
            csv_path (str): Absolute or relative path (absolute preferred)
                ex. '/path/to/ztp-folder/keystore.csv'
    """
    validated = False
    prompt = 'Enter explicit path to keystore file. (ex. /etc/my.csv): '
    while not validated:
        csv_path = input(prompt).strip()
        csv_path = csv_path.replace('"', '')
        csv_path = csv_path.replace("'", "")
        if not csv_path:
            ans = input('No input. Go back to menu? (Y/n): ')
            if ans.lower() != "n":
                return None

        if path.exists(csv_path):
            validated = True
        else:
            print(f'Cannot find file: "{csv_path}"')
            ans = input('Create empty file? (y/N): ')
            if ans.lower() == 'y':
                with open(csv_path, 'x', encoding='utf-8') as file:
                    print(f'Created {file.name}')
                validated = True

    return csv_path

def prompt_stack_size(config):
    """
    Configure stack size parameter. Impacts # of available ID Array mappings.
        Parameters / Returns:
            config (dict): Current configuration data
    """
    print(help_text.HELP_STACK_SIZE_QUESTION)
    current = config['max_stack_size']
    err_state = True
    while err_state:
        ans = input(f'Input max stack size. ([enter] for {current}): ')
        if not ans:
            ans = current
        fail = False
        try:
            i = int(ans)
        except ValueError:
            print(f'Input {ans} is not an integer.')
            fail = True
        if i not in range(1,9):
            print(f'Input {ans} not in range of 1 to 8.')
            fail = True
        err_state = True if fail else False

    config['max_stack_size'] = ans
    return config

def select_form_id(config):
    """
    Presents dynamic list of available forms and requests selection
        Parameters / Returns:
            config (dict): Current configuration data
    """
    base_url = 'https://api.jotform.com/user/forms'
    api_filter = '?limit=1000&filter=' + quote('{"status":"ENABLED"}')
    url = base_url + api_filter
    headers = {'APIKEY': config['api_key']}
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload, timeout=10)
    form_set = {}
    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        for form in response.json()['content']:
            form_set.update({form['title']: form['id']})

    if len(form_set) > 0:
        print(help_text.HELP_FORM_ID_SELECTOR)
        key_set = list(form_set.keys())
        selection = menu_generic_select(key_set, 'AVAILABLE FORMS')
        config['form_id'] = form_set[key_set[selection]]
    else:
        print(help_text.FAIL_FORM_ID_SELECTOR)
        config['form_id'] = None

    return config

def select_submission(config, sample_file):
    """
    Obtain sample submission data. Save file and return data to calling code.
        Parameters:
            config (dict): Current configuration data
        Returns:
            sample (dict): JSON data read into python
                ex. {'id': '<num str>, '<vars>': '<vals>', 'answers': {<dict>}}
            dwnld_state (str): Values 'Present' or 'Absent'
    """
    print(help_text.HELP_SUBMISSION_SELECTOR)
    _ = input('Hit [enter] after Form is submitted...')

    sample = None
    dwnld_state = 'Absent'
    api_key = config['api_key']
    form_id = config['form_id']
    response = shared.get_new_submissions(api_key, form_id)

    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        log.debug('Full Jotform Response (JSON):\r\n%s',
                  json.dumps(response.json(), indent=4))

        submission_ids = []
        for submission in response.json()['content']:
            submission_ids.append(submission['id'])

        ans = menu_generic_select(submission_ids, 'UNREAD SUBMISSIONS')
        for submission in response.json()['content']:
            if submission_ids[ans] == submission['id']:
                sample = submission

        if sample:
            with open(sample_file, 'w', encoding='utf-8') as json_file:
                json.dump(sample, json_file, indent=4)
            dwnld_state = 'Present'

    else:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))
        print(help_text.FAIL_SUBMISSION_SELECTOR)

    return sample, dwnld_state

def select_q_a_combo(config, sample, menu_opts, meta_list, var_name):
    """
    Generic process to map Keystore variables to JotForm Answers
        Parameters:
            var_name (str): keystore_id, idarray_x, <custom>
            menu_opts (list): Items for user selection
        Returns:
            map_dict (dict): Answer mapping and actual question
                ex. {q_text: 'My Question', a_id: 14, a_idx: 0}
    """
    print()
    delim = config['delimiter']
    answers = sample['answers']

    h_text = 'AVAILABLE JOTFORM ANSWERS'
    p_text = f'Select Item Containing "{var_name.upper()}": '
    sel = menu_generic_select(menu_opts, header=h_text,prompt=p_text)
    a_id = meta_list[sel]
    q_text = answers[a_id]['text']
    a_text = answers[a_id]['answer']
    if delim in a_text:
        items = a_text.replace(f' {delim} ', delim).split(delim)
        h_text = "DELIMITER SPLIT VALUES"
        p_text = f'Select value for "{var_name.upper()}": '
        a_idx = menu_generic_select(items, header=h_text, prompt=p_text)
    else:
        a_idx = 0

    map_dict = {'q_text': q_text, 'a_id': a_id, 'a_idx': a_idx}

    return map_dict

def select_room_id(config):
    """
    Presents dynamic list of available rooms and requests selection
        Parameters / Returns:
            config (dict): Current configuration data
    """
    bot_token = config['bot_token']
    url = 'https://webexapis.com/v1/rooms'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bot_token}'
        }
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload, timeout=10)
    room_set = {}
    if response.status_code == 200:
        for room in response.json()['items']:
            room_set.update({room['title']: room['id']})
    else:
        print('Room Query Failure. Status Code: ' + str(response.status_code)
              + '\r\nResponse Text:\r\n\r\n' + response.text)

    if len(room_set) > 0:
        print(help_text.HELP_ROOM_ID_SELECTOR)
        key_set = list(room_set.keys())
        selection = menu_generic_select(key_set, 'AVAILABLE ROOMS')
        config['room_id'] = room_set[key_set[selection]]
    else:
        print(help_text.FAIL_ROOM_ID_SELECTOR)
        config['room_id'] = None

    return config

def menu_generic_select(items, header="MENU", quit_opt=False, prompt=None):
    """
    Presents simple selector menu to user and returns list item position.
        Parameters:
            items (list): Set of text strings (presented to user)
            header (str): Menu heading
            quit_opt (bool): Optional. Enables / disables quit menu option.
            prompt (str): Optional. Alternate user prompt.
        Returns:
            selection (int): Position value in original list 0..n
                or
            None: User quits (q) or empty list passed to function."""
    # Empty list presented, return None
    if not items:
        return None

    q_text = prompt if prompt else "Select an item: "

    # Build menu, options 1..n for list positions 0..x
    menu_text = f'         {header}\r\n'
    i = 1
    for item in items:
        menu_text += f'    {i}. {item}\r\n'
        i += 1

    # Add quit option if enabled
    if quit_opt:
        menu_text += '    Q. Quit to Previous Menu\r\n'

    err_state = True
    while err_state:
        print(menu_text)
        ans = input(q_text)

        # User selected quit, return None
        if quit_opt and ans.lower() == 'q':
            return None

        # Check if user input in range of options
        try:
            selection = int(ans)
        except ValueError:
            err_state = True
        else:
            if selection in range(1, i):
                err_state = False
            else:
                err_state = True

        # User feedback for bad selection
        if err_state:
            print(f'\r\n{ans} is not a valid selection. Try again.\r\n')

    # Subtract 1 from selection to simplify calling code
    return selection - 1

def test_jotform_api_key(api_key):
    """
    Send test query to JotForm. Calling code determines pass/fail actions.
        Parameters:
            api_key (str): Hexidecimal string value
        Returns:
            result (str}: Succeeded or Failed
    """
    result = "Failed"
    url = 'https://api.jotform.com/user/usage'
    headers = {'APIKEY': api_key}
    payload = None
    try:
        int(api_key, 16)
    except ValueError:
        print('Answer not Hex value.')
        return None
    response = requests.request('GET', url, headers=headers, data=payload, timeout=10)
    if response.status_code == 200:
        result = "Succeeded"
    else:
        print(f'API Test Failure. Status Code: {response.status_code}\r\n'
              + '\r\nResponse Text:\r\n\r\n{response.text}')
        log.debug('Full Jotform Response (JSON):\r\n%s',
                  json.dumps(response.json(), indent=4))

    return result

def test_webex_bot_token(bot_token):
    """
    Send test query to WebEx Teams. Calling code determines pass/fail actions.
        Parameters:
            bot_token (str): String value
        Returns:
            result (str}: Succeeded or Failed
    """
    result = "Failed"
    url = 'https://webexapis.com/v1/rooms'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bot_token}'
        }
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload, timeout=10)
    if response.status_code == 200:
        result = "Succeeded"
    else:
        print(f'Room Query Failure. Status Code: {response.status_code}\r\n'
              + '\r\nResponse Text:\r\n\r\n{response.text}')

    return result

def file_save_config(config_file, config):
    """
    Write or overwrite configuration file with new data.
        Parameters:
            config_file (str): Relative or absolute path
            config (dict): Current configuration data
        Returns:
            None
    """
    with open(config_file, 'w', encoding='utf-8') as json_file:
        json.dump(config, json_file, indent=4)
    print('Configuration saved to disk.')

def file_read_sample(sample_file):
    """
    Read Jotform sample submission file, if present.
        Parameters:
            sample_file (str): Relative or absolute path.
        Returns:
            sample (dict): JSON data read into python
            dwnld_state (str): Values 'Present' or 'Absent'
    """
    sample = None
    dwnld_state = 'Absent'
    if path.exists(sample_file):
        dwnld_state = 'Present'
        with open(sample_file, encoding='utf-8') as cfg_file:
            sample = json.load(cfg_file)
        log.debug('Imported configuration from file, %s',  sample_file)
    else:
        log.info('Unable to import configuration.')

    return sample, dwnld_state

def build_select_data(sample):
    """
    Build list and dictionary for user selection
        Parameters:
            sample (dict): JotForm sample submission
        Returns:
            menu_opts (list): Set of string values (user options)
            meta_list (list): Jotform Q IDs in order of menu options
    """
    menu_opts = None
    meta_list = None
    if sample:
        answers = sample['answers']
        menu_opts = []
        meta_list = []

        for q_id_num, inner_dict in answers.items():
            q_text = inner_dict['text']
            try:
                a_text = inner_dict['answer']
            except KeyError:
                a_text = 'None'
                continue

            menu_opts.append(f'Q: {q_text} || A: {a_text}')
            meta_list.append(q_id_num)

    return menu_opts, meta_list

def build_menu_dm_basic(data_map, mss):
    """
    Generates customized dictionary data for Jinja2 dynamic menu.
        Parameters:
            data_map (dict): Answers portion of Jotform sample submission
            mss (int): Maximum Stack Size. Used for dynamic menu template.
        Returns:
            render_dict (dict): Display ready data for Jinja2 rendering
    """
    render_dict = {'mss': mss}
    if 'keystore_id' in data_map.keys():
        render_dict['k_id'] = data_map['keystore_id']
    else:
        render_dict['k_id'] = None

    for i in range(1,9):
        if f'idarray_{i}' in data_map.keys():
            render_dict[f'id_arr{i}'] = data_map[f'idarray_{i}']
        else:
            render_dict[f'id_arr{i}'] = None

    return render_dict

def build_menu_dm_custom(data_map):
    """
    Generates customized dictionary data for Jinja2 dynamic menu.
        Parameters:
            data_map (dict): Answers portion of Jotform sample submission
        Returns:
            render_data (list): Display ready data for Jinja2 rendering
            var_list (list): Selection names for deltion option
    """
    render_data = ''
    var_list = []
    for var_name, var_info in data_map.items():
        if 'idarray_' not in var_name and 'keystore_id' not in var_name:
            render_data += (f"    {var_name}: {var_info['q_text']} |"
                          + f" {var_info['a_id']} | {var_info['a_idx']}\r\n")
            var_list.append(var_name)

    return render_data, var_list
