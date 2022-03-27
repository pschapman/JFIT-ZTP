""" blah """

# Python native modules
import logging

# Private modules
from . import shared

# Begin logging inside module, parent initializes configuration
log = logging.getLogger(__name__)

def setup(config_file):
    """
    Initial setup wizard
    """
    settings = shared.read_config(config_file)
    # global delimiter, null_answer, bot_token, room_id

    # Settings not part of key map
    api_key = get_api_key(settings)
    form_id = get_form_id(api_key, settings)
    delimiter = get_delimiter(settings)
    exec_mode, csv_path, import_unknown = get_exec_mode(settings)
    null_answer = get_null_answer(settings)

    # Enable WebEx Teams notifications
    print(prompts.INFO_WEBEX_TEAMS_INTEGRATION)
    prompt = 'Enable notifications to WebEx Teams? (y/N) > '
    response = pyip.inputYesNo(prompt=prompt, blank=True)
    if response == 'yes':
        bot_token = get_bot_token(settings)
        room_id = get_room_id(bot_token, settings)
    else:
        bot_token = None
        room_id = None

    # Enable MS Teams notifications via Power Automate
    print(prompts.INFO_POWER_AUTOMATE_INTEGRATION)
    prompt = 'Enable notifications to Microsoft Power Automate? (y/N) > '
    response = pyip.inputYesNo(prompt=prompt, blank=True)
    if response == 'yes':
        azure_url = get_powerautomate_url(settings)
    else:
        azure_url = None

    # Get sample data set for key map Q&A
    sample_data = get_sample_submission(api_key, form_id)
    ans_set = sample_data['answers']
    ans_menu = dict_to_q_menu(ans_set)

    # Get old data map settings to offer reusable config
    data_map = settings['data_map'] if settings else {}

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
