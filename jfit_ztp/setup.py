""" blah """

# Python native modules
import logging
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
              'import_unknown': None,
              'null_answer': "Select From List",
              'bot_token': None,
              'room_id': None,
              'azure_url': None,
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
    menu_text = '\t    ' + header + '\r\n'
    i = 1
    for item in items:
        menu_text += '\t' + str(i) + '. ' + item + '\r\n'
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
            print('\r\n' + ans + ' is not a valid selection. Try again.\r\n')

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
            test_state = check_api_key(config)
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

    key_set = list(form_set.keys())
    selection = dynamic_selector_menu(key_set, 'AVAILABLE FORMS')
    config['form_id'] = form_set[key_set[selection]]

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
    user_prompt = 'Input single character delimiter ([enter] for ' + str(delim)
    while err_state:
        ans = input(user_prompt + ': ').strip()
        if not ans:
            err_state = False
        elif len(ans) == 1:
            config['delimeter'] = ans
            err_state = False
        else:
            print('Delimeter length not 1. Space not permitted. Try again.')

    return config

def setup(config_file):
    """
    Initial setup wizard
    """
    cfg = shared.read_config(config_file)
    if not cfg:
        cfg = init_empty_cfg()
    # global delimiter, null_answer, bot_token, room_id

    # Settings not part of key map
    # api_key = get_api_key(cfg)
    form_id = get_form_id(api_key, cfg)
    delimiter = get_delimiter(cfg)
    exec_mode, csv_path, import_unknown = get_exec_mode(cfg)
    null_answer = get_null_answer(cfg)

    # Enable WebEx Teams notifications
    print(prompts.INFO_WEBEX_TEAMS_INTEGRATION)
    prompt = 'Enable notifications to WebEx Teams? (y/N) > '
    response = pyip.inputYesNo(prompt=prompt, blank=True)
    if response == 'yes':
        bot_token = get_bot_token(cfg)
        room_id = get_room_id(bot_token, cfg)
    else:
        bot_token = None
        room_id = None

    # Enable MS Teams notifications via Power Automate
    print(prompts.INFO_POWER_AUTOMATE_INTEGRATION)
    prompt = 'Enable notifications to Microsoft Power Automate? (y/N) > '
    response = pyip.inputYesNo(prompt=prompt, blank=True)
    if response == 'yes':
        azure_url = get_powerautomate_url(cfg)
    else:
        azure_url = None

    # Get sample data set for key map Q&A
    sample_data = get_sample_submission(api_key, form_id)
    ans_set = sample_data['answers']
    ans_menu = dict_to_q_menu(ans_set)

    # Get old data map settings to offer reusable config
    data_map = cfg['data_map'] if cfg else {}

    # Begin key map Q&A
    print(prompts.INFO_KEYSTORE_ID)
    ztp_var = 'keystore_id'
    old_vals = get_old_vals(data_map, [ztp_var], ans_set)
    if old_vals:
        ans_ords = old_vals[0]
    else:
        prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
        ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
    data_map.update({ztp_var: ans_ords})

    print(prompts.INFO_ASSOCIATION)
    ztp_var = 'association'
    prompt = 'Will this JotForm provide a template association? (y/N) > '
    response = pyip.inputYesNo(prompt=prompt, blank=True)
    if response == 'yes':
        old_vals = get_old_vals(data_map, [ztp_var], ans_set)
        if old_vals:
            ans_ords = old_vals[0]
        else:
            prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
            ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
        data_map.update({ztp_var: ans_ords})

    print(prompts.INFO_SWITCH_STACKS)
    prompt = 'Will this ZTP instance provision switch stacks? (Y/n) > '
    response = pyip.inputYesNo(prompt=prompt, blank=True)
    stack_max = 1
    if response == 'yes' or not response:
        prompt = 'What is the maximum stack size? (default is 8) > '
        stack_max = pyip.inputNum(prompt=prompt, min=1, max=9, blank=True)
        stack_max = 8 if not stack_max else stack_max
    for index in range(stack_max):
        ztp_var = 'idarray' + '_' + str(index + 1)
        old_vals = get_old_vals(data_map, [ztp_var], ans_set)
        if old_vals:
            ans_ords = old_vals[0]
        else:
            prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
            ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
        data_map.update({ztp_var: ans_ords})

    print(prompts.INFO_CUSTOM_VARIABLES)
    prompt = 'Map a Custom Variable? (y/N) > '
    done = None
    while not done:
        response = pyip.inputYesNo(prompt=prompt, blank=True)
        if response == 'no' or not response:
            done = True
        else:
            prompt = 'Specify variable name. > '
            regex = [(r'\ ', 'Spaces not allowed.')]
            ztp_var = pyip.inputStr(prompt=prompt, blockRegexes=regex)
            old_vals = get_old_vals(data_map, [ztp_var], ans_set)
            if old_vals:
                ans_ords = old_vals[0]
            else:
                prompt = 'Which answer contains the value for ' + ztp_var + '? > \r\n'
                ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
            data_map.update({ztp_var: ans_ords})
        prompt = 'Map another Custom Variable? (y/N) > '

    # Post Q&A - Generate / save JSON file then mark sample submission "read"
    new_config = {'api_key': api_key,
                  'form_id': form_id,
                  'delimiter': delimiter,
                  'exec_mode': exec_mode,
                  'csv_path': csv_path,
                  'import_unknown': import_unknown,
                  'null_answer': null_answer,
                  'bot_token': bot_token,
                  'room_id': room_id,
                  'azure_url': azure_url,
                  'data_map': data_map}

    print('Config File Contents:\r\n' + json.dumps(new_config, indent=4))
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, indent=4)
    f.close()
    print('Configuration saved to disk.')

    if bot_token:
        mkdn_form = ('#### JFIT Setup Complete\r\n'
                    'Hi, your WebEx Teams Bot integration is working!!\r\n'
                    '\r\n---')
        markdown = jinja(mkdn_form).render(config=new_config)
        send_webex_msg(markdown)

    if azure_url:
        msgblob = {}
        msgblob['src-id'] = pyfile + '.' + hostfqdn
        msgblob['type'] = 'status'
        html_form = ('<p><strong>JFIT Setup Complete</strong></p>'
                    '<p>Hi, your MS Power Automate integration is working!!'
                    '</p><span style="display: none">')
        msgblob['message'] = jinja(html_form).render(config=new_config)
        payload = json.dumps(msgblob)
        send_powerautomate_msg(azure_url, payload)

    if not test_mode:
        # Marking sample entry as read
        response = mark_submissions_read(api_key, [sample_data['id']])
        if response:
            print('WARNING - FAILED TO MARK SAMPLE SUBMISSION AS READ.\r\n'
                'Verify your API Key permissions before going into'
                ' production.\r\n Your configuration has been saved.')
            print(response.status_code)
            print(json.dumps(response.json(), indent=4))
        else:
            print('Sample submission marked as read.')
    print('SETUP COMPLETE!')

def main_menu(config): # pylint: disable=too-many-branches
    """Main Menu"""
    err_state = True
    while err_state:
        # Update dynamic menu parts
        menu = jinja(menus.M_MAIN).render(
            api_key = config['api_key'],
            form_id = config['form_id'],
            exec_mode = config['exec_mode'],
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
            print()
        elif selection == '4':
            config = delimiter_question(config)
        elif selection == '5':
            print()
        elif selection == '6':
            print()
        elif selection == '7':
            print()
        elif selection == '8':
            print()
        elif selection.lower() == 'h':
            print()
        elif selection.lower() == 's':
            print()
        elif selection.lower() == 'q':
            print()
            err_state = False
        elif selection.lower() == 'a':
            print()
            err_state = False
