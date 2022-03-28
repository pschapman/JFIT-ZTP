"""
Notes:
    Python 3.6 or later
    Revise helps throughout
    Move webex/webhook jinja templates to separate file
"""

# Python native modules
import logging
from os import path
import json
from urllib.parse import quote

# External modules. Installed by freeztpInstaller.
import requests
from jinja2 import Template as jinja

# Private modules
from . import shared
from . import menu_text as menus
from . import help_text

# Begin logging inside module, parent initializes configuration
log = logging.getLogger(__name__)

def init_empty_cfg():
    """
    Create config variable with minimum required entries. All set None.
        Returns:
            config (dict): Baseline config dictionary
    """
    config = {'api_key': None,
              'form_id': None,
              'delimiter': ":",
              'exec_mode': "cli",
              'csv_path': None,
              'import_unknown': False,
              'null_answer': "Select From List",
              'bot_token': None,
              'room_id': None,
              'webhook_url': None,
              'data_map': {}}
    return config

def dynamic_selector_menu(items, header = "MENU", quit_opt = False):
    """
    Presents simple selector menu to user and returns list item position.
        Parameters:
            items (list): Set of text strings (presented to user)
            header (str): Menu heading
            quit_opt (bool): Enables / disables quit menu option.
        Returns:
            selection (int): Position value in original list 0..n
                or
            None: User quits (q) or empty list passed to function."""
    # Empty list presented, return None
    if not items:
        return None

    # Build menu, options 1..n for list positions 0..x
    menu_text = f'\t    {header}\r\n'
    i = 1
    for item in items:
        menu_text += f'\t{i}. {item}\r\n'
        i += 1

    # Add quit option if enabled
    if quit_opt:
        menu_text += '\tQ. Quit to Previous Menu\r\n'

    err_state = True
    while err_state:
        print(menu_text)
        ans = input('Select an item: ')

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

def check_api_key(api_key):
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
    response = requests.request('GET', url, headers=headers, data=payload)
    if response.status_code == 200:
        result = "Succeeded"

    return result

def api_key_menu(config):
    """
    API Key configuration menu. Key value must be hex, and 1..4 characters.
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_GET_API_KEY)
    err_state = True
    test_state = "Untested"
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_API_KEY).render(
            api_key = config['api_key'],
            test_result = test_state
        )
        print(menu)
        selection = input('Select Menu Item: ')

        if selection == '1':
            ans = input("Input API Key (Hex string): ").strip()
            fail = False
            if ' ' in ans:
                fail = True
                print('Answer contains illegal space character.')
            try:
                i = int(ans, 16) # pylint: disable=unused-variable
            except ValueError:
                fail = True
                print('Answer does not appear to be a hex string.')
            if len(ans) > 40:
                fail = True
                print('Answer is greater than 40 characters.')
            if not fail:
                config['api_key'] = ans

        elif selection == '2':
            test_state = check_api_key(config['api_key'])
        elif selection.lower() == 'h':
            print(help_text.INFO_GET_API_KEY)
        elif selection.lower() == 'q':
            err_state = False

    return config

def form_id_selector(config):
    """
    Presents dynamic list of available forms and requests selection
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_GET_FORM_ID)

    base_url = 'https://api.jotform.com/user/forms'
    api_filter = '?limit=1000&filter=' + quote('{"status":"ENABLED"}')
    url = (base_url + api_filter)
    headers = {'APIKEY': config['api_key']}
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload)
    form_set = {}
    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        for form in response.json()['content']:
            form_set.update({form['title']: form['id']})

    if len(form_set) > 0:
        key_set = list(form_set.keys())
        selection = dynamic_selector_menu(key_set, 'AVAILABLE FORMS')
        config['form_id'] = form_set[key_set[selection]]
    else:
        config['form_id'] = None

    return config

def get_csv_path():
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

def exec_mode_menu(config):
    """
    JFIT Execution Mode configuration menu.
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_GET_EXEC_MODE)
    err_state = True
    toggle_mode = config['exec_mode']
    toggle_unknown = config['import_unknown']
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_EXEC_MODE).render(
            exec_mode = toggle_mode.upper() ,
            csv_path = config['csv_path'],
            import_unknown = toggle_unknown
        )
        print(menu)
        selection = input('Select Menu Item: ')

        if selection == '1':
            toggle_mode = 'csv' if toggle_mode == 'cli' else 'cli'
        elif selection == '2':
            config['csv_path'] = get_csv_path()
        elif selection == '3':
            toggle_unknown = not toggle_unknown
        elif selection.lower() == 'h':
            print(help_text.INFO_GET_EXEC_MODE)
        elif selection.lower() == 'q':
            config['exec_mode'] = toggle_mode
            config['import_unknown'] = toggle_unknown
            err_state = False

    return config

def delimiter_question(config):
    """
    Simple question. Ask for new delimiter or accept current.
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_GET_DELIMITER)
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

def null_answer_question(config):
    """
    Simple question. Ask for new null answer or accept current.
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_GET_NULL_ANSWER)
    null_ans = config['null_answer']
    prompt = f'Input null answer string ([enter] for {null_ans}): '
    ans = input(prompt).strip()
    config['null_answer'] = ans

    return config

def check_bot_token(bot_token):
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
    response = requests.request('GET', url, headers=headers, data=payload)
    if response.status_code == 200:
        result = "Succeeded"
    else:
        print(f'Room Query Failure. Status Code: {response.status_code}\r\n'
              + '\r\nResponse Text:\r\n\r\n{response.text}')

    return result

def room_id_selector(config):
    """
    Presents dynamic list of available rooms and requests selection
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_GET_FORM_ID)
    bot_token = config['bot_token']
    url = 'https://webexapis.com/v1/rooms'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bot_token}'
        }
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload)
    room_set = {}
    if response.status_code == 200:
        for room in response.json()['items']:
            room_set.update({room['title']: room['id']})
    else:
        print('Room Query Failure. Status Code: ' + str(response.status_code)
              + '\r\nResponse Text:\r\n\r\n' + response.text)

    if len(room_set) > 0:
        key_set = list(room_set.keys())
        selection = dynamic_selector_menu(key_set, 'AVAILABLE ROOMS')
        config['room_id'] = room_set[key_set[selection]]
    else:
        config['room_id'] = None

    return config

def webex_menu(config):
    """
    WebEx Teams Notifications configuration menu.
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_WEBEX_TEAMS_INTEGRATION)
    err_state = True
    test_state = "Untested"
    markdown = ('#### JFIT Setup \r\nHi, your WebEx Teams Bot integration is'
                ' working!!\r\n\r\n---')
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_WEBEX).render(
            bot_token = config['bot_token'],
            test_result = test_state,
            room_id = config['room_id']
        )
        print(menu)
        selection = input('Select Menu Item: ')

        if selection == '1':
            ans = input("Input API Key: ").strip()
            fail = False
            if ' ' in ans:
                fail = True
                print('Answer contains illegal space character.')
            if len(ans) > 110:
                fail = True
                print('Answer is greater than 110 characters.')
            if not fail:
                config['bot_token'] = ans

        elif selection == '2':
            test_state = check_bot_token(config['bot_token'])
        elif selection == '3':
            config = room_id_selector(config)
        elif selection == '4':
            shared.send_webex_msg(config['bot_token'], config['room_id'], markdown)
        elif selection.lower() == 'x':
            config['bot_token'] = None
            config['room_id'] = None
        elif selection.lower() == 'h':
            print(help_text.INFO_WEBEX_TEAMS_INTEGRATION)
        elif selection.lower() == 'q':
            err_state = False

    return config

def webhook_url_menu(config):
    """
    Webhook Notifications configuration menu.
        Parameters:
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            config (dict): Updated configuration data
    """
    print(help_text.INFO_POWER_AUTOMATE_INTEGRATION)
    err_state = True
    msgblob = {
        'src-id': f'jfit_ztp.{shared.hostfqdn}',
        'type': 'status',
        'message': ('<p><strong>JFIT Setup</strong></p>'
                    '<p>Hi, your Webhook URL is working!!</p>'
                    '<span style="display: none">')
    }
    payload = json.dumps(msgblob)

    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_WEBHOOK).render(
            webhook_url = config['webhook_url']
        )
        print(menu)
        selection = input('Select Menu Item: ')

        if selection == '1':
            ans = input("Input Webhook URL ([enter] for None): ").strip()
            fail = False
            if ' ' in ans:
                fail = True
                print('Answer contains illegal space character.')
            if len(ans) > 300:
                fail = True
                print('Answer is greater than 300 characters.')
            if not ans:
                ans = None
            elif ('https://').lower() not in ans:
                fail = True
                print('Answer does not contain "https://".')
            if not fail:
                config['webhook_url'] = ans

        elif selection == '2':
            shared.send_webhook_msg(config['webhook_url'], payload)
        elif selection.lower() == 'x':
            config['webhook_url'] = None
        elif selection.lower() == 'h':
            print(help_text.INFO_POWER_AUTOMATE_INTEGRATION)
        elif selection.lower() == 'q':
            err_state = False

    return config

def save_config(config_file, config):
    """
    Write or overwrite configuration file with new data.
        Parameters:
            config_file (str): Relative or absolute path
            config (dict): Current configuration data
                ex. {'api_key': '<key>', '<vars>': '<vals>'}
        Returns:
            None
    """
    with open(config_file, 'w', encoding='utf-8') as json_file:
        json.dump(config, json_file, indent=4)
    print('Configuration saved to disk.')

def setup(config_file, test_mode): # pylint: disable=unused-argument
    """
    Initial setup wizard
    """
    cfg = shared.read_config(config_file)
    if not cfg:
        cfg = init_empty_cfg()

    main_menu(config_file, cfg)

    # # Get sample data set for key map Q&A
    # sample_data = get_sample_submission(api_key, form_id)
    # ans_set = sample_data['answers']
    # ans_menu = dict_to_q_menu(ans_set)

    # # Get old data map settings to offer reusable config
    # data_map = cfg['data_map'] if cfg else {}

    # Begin key map Q&A
    # print(prompts.INFO_KEYSTORE_ID)
    # ztp_var = 'keystore_id'
    # old_vals = get_old_vals(data_map, [ztp_var], ans_set)
    # if old_vals:
    #     ans_ords = old_vals[0]
    # else:
    #     prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
    #     ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
    # data_map.update({ztp_var: ans_ords})

    # print(prompts.INFO_ASSOCIATION)
    # ztp_var = 'association'
    # prompt = 'Will this JotForm provide a template association? (y/N) > '
    # response = pyip.inputYesNo(prompt=prompt, blank=True)
    # if response == 'yes':
    #     old_vals = get_old_vals(data_map, [ztp_var], ans_set)
    #     if old_vals:
    #         ans_ords = old_vals[0]
    #     else:
    #         prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
    #         ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
    #     data_map.update({ztp_var: ans_ords})

    # print(prompts.INFO_SWITCH_STACKS)
    # prompt = 'Will this ZTP instance provision switch stacks? (Y/n) > '
    # response = pyip.inputYesNo(prompt=prompt, blank=True)
    # stack_max = 1
    # if response == 'yes' or not response:
    #     prompt = 'What is the maximum stack size? (default is 8) > '
    #     stack_max = pyip.inputNum(prompt=prompt, min=1, max=9, blank=True)
    #     stack_max = 8 if not stack_max else stack_max
    # for index in range(stack_max):
    #     ztp_var = 'idarray' + '_' + str(index + 1)
    #     old_vals = get_old_vals(data_map, [ztp_var], ans_set)
    #     if old_vals:
    #         ans_ords = old_vals[0]
    #     else:
    #         prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
    #         ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
    #     data_map.update({ztp_var: ans_ords})

    # print(prompts.INFO_CUSTOM_VARIABLES)
    # prompt = 'Map a Custom Variable? (y/N) > '
    # done = None
    # while not done:
    #     response = pyip.inputYesNo(prompt=prompt, blank=True)
    #     if response == 'no' or not response:
    #         done = True
    #     else:
    #         prompt = 'Specify variable name. > '
    #         regex = [(r'\ ', 'Spaces not allowed.')]
    #         ztp_var = pyip.inputStr(prompt=prompt, blockRegexes=regex)
    #         old_vals = get_old_vals(data_map, [ztp_var], ans_set)
    #         if old_vals:
    #             ans_ords = old_vals[0]
    #         else:
    #             prompt = 'Which answer contains the value for ' + ztp_var + '? > \r\n'
    #             ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
    #         data_map.update({ztp_var: ans_ords})
    #     prompt = 'Map another Custom Variable? (y/N) > '

    # # print('Config File Contents:\r\n' + json.dumps(new_config, indent=4))

    # if not test_mode:
    #     # Marking sample entry as read
    #     response = mark_submissions_read(api_key, [sample_data['id']])
    #     if response:
    #         print('WARNING - FAILED TO MARK SAMPLE SUBMISSION AS READ.\r\n'
    #             'Verify your API Key permissions before going into'
    #             ' production.\r\n Your configuration has been saved.')
    #         print(response.status_code)
    #         print(json.dumps(response.json(), indent=4))
    #     else:
    #         print('Sample submission marked as read.')
    # print('SETUP COMPLETE!')

def main_menu(config_file, config): # pylint: disable=too-many-branches
    """Main Menu"""
    err_state = True
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_MAIN).render(
            api_key = config['api_key'],
            form_id = config['form_id'],
            exec_mode = config['exec_mode'].upper(),
            import_unknown = config['import_unknown'],
            delimiter = config['delimiter'],
            null_answer = config['null_answer']
        )
        print(menu)
        selection = input('Select Menu Item: ')

        if selection == '1':
            config = api_key_menu(config)
        elif selection == '2':
            config = form_id_selector(config)
        elif selection == '3':
            config = exec_mode_menu(config)
        elif selection == '4':
            config = delimiter_question(config)
        elif selection == '5':
            config = null_answer_question(config)
        elif selection == '6':
            config = webex_menu(config)
        elif selection == '7':
            config = webhook_url_menu(config)
        elif selection == '8':
            print()
        elif selection.lower() == 'h':
            print()
        elif selection.lower() == 's':
            save_config(config_file, config)
        elif selection.lower() == 'q':
            save_config(config_file, config)
            err_state = False
        elif selection.lower() == 'a':
            ans = input('Quit without saving? (y/N)')
            if ans.lower() == 'y':
                err_state = False
