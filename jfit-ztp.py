"""
##                             JFIT-ZTP                              ##
##               JotForm Form Import Tool for freeZTP                ##

Author: Paul S. Chapman
Version: 0.9

Open Caveats / Bugs / Limitations:
1. Hacks on PyInputPlus __init__.py for Python 2.7 compatibility
 a. Line 134: Add "unicode" to class list str -> (str,unicode)
   i. if not isinstance(prompt, (str, unicode)):
 b. Line 156: Change input() to raw_input()
   i. userInput = raw_input()
 c. Data display in setup for "previous items" is framed in python structures
    and not textual.  Issue only occurs in Python 2. (PyInputPlus related)
2. "newline=" in file write not available until Python 3.3.  Added Try for
   backwards compatibility.  Required in Python 3 to resolve CRCRLF issue.
3. Script only adds to or alters existing data.  Duplicate JotForm submissions
   will not remove unneeded commands / external keystore fields.  Resolution
   appears to be non-trivial.  Possible strategy of marking some datamap
   variables as "unprotected" and subject to automatic deletion.  May require
   update to datamap schema.

To Do List:
1. Alter setup to show list of existing variables and allow individual update
   or delete.
2. Automate configuration of cron job
3. Add Logging
4. Determine what happens if 'mark as read' fails for process_data
"""
# Python native modules
from os import path
import sys
import subprocess
import json
import csv
if int(sys.version[:1]) == 3:
    from urllib.parse import quote
    # LOG INFO
else:
    from urllib import quote
    # LOG INFO

# External modules. Installed by freeztpInstaller.
import requests
# External modules. Separate install required.
try:
    import pyinputplus as pyip
except:
    print('Install module PyInputPlus. (e.g. pip install pyinputplus)')
    sys.exit()
# Private modules
import constants

def submission_to_cli(ans_set, data_map):
    # Generates ZTP CLI commands from JotForm Data
    # Inputs
    # ans_set = {'1': {'text': 'Question 1', 'answer': 'myhostname'}}
    # data_map = {'varname': {'qID': '1', 'index': 0}}
    # Outputs
    # cmd_set = ['ztp set idarray <name> <serial>', 'another ztp command']

    cmd_set = []
    device_id_set = []

    value = data_map['keystore_id']
    q_id = ans_set[value['qID']]
    ans_idx = value['index']
    keystore_id = get_answer_element(q_id, ans_idx)
    # LOG DEBUG

    for key, value in data_map.items():
        if 'keystore_id' in key:
            continue
        elif 'idarray' in key:
            q_id = ans_set[value['qID']]
            ans_idx = value['index']
            device_id = get_answer_element(q_id, ans_idx)
            if device_id:
                device_id_set.append(device_id)
                # LOG DEBUG
        elif 'association' in key:
            q_id = ans_set[value['qID']]
            ans_idx = value['index']
            var_data = get_answer_element(q_id, ans_idx)
            if var_data:
                cmd_set.append('ztp set association id ' + keystore_id
                               + ' template ' + var_data)
                # LOG DEBUG
        else:
            q_id = ans_set[value['qID']]
            ans_idx = value['index']
            var_data = get_answer_element(q_id, ans_idx)
            var_name = key
            if var_data:
                cmd_set.append('ztp set keystore ' + keystore_id + ' '
                                  + var_name + ' ' + var_data)
                # LOG DEBUG
    # LOG INFO
    cmd_set.append('ztp set idarray ' + keystore_id + ' '
                   + ' '.join(device_id_set))
    return cmd_set

def submission_to_csv(ans_set, data_map, headers, csv_data):
    # Update external keystore fields / rows from JotForm Data
    # Inputs
    # ans_set = {'1': {'text': 'Question 1', 'answer': 'myhostname'}}
    # data_map = {'varname': {'qID': '1', 'index': 0}}
    # headers = ['keystore_id', 'var_1', 'var_x']
    # csv_data = {'MYHOSTNAME': {'keystore_id': 'myhostname', 'var': 'value'}}
    # Outputs
    # headers <altered list if any headers missing>
    # csv_data <altered entries, same as above format>
    # True/False indicating whether changes were made (ztp restart)

    # Create empty change list
    csv_update = {}

    value = data_map['keystore_id']
    q_id = ans_set[value['qID']]
    ans_idx = value['index']
    keystore_id = get_answer_element(q_id, ans_idx)
    # LOG DEBUG

    for key, value in data_map.items():
        if 'keystore_id' in key:
            continue
        else:
            q_id = ans_set[value['qID']]
            ans_idx = value['index']
            var_data = get_answer_element(q_id, ans_idx)
            var_name = key
            if var_data:
                csv_update.update({var_name: var_data})
            # LOG DEBUG
    # LOG INFO
    # Create partial entry if Import Unknown is enabled
    if keystore_id.upper() not in csv_data and import_unknown:
        csv_data.update({keystore_id.upper(): {'keystore_id': keystore_id}})
        # LOG WARNING
    elif keystore_id.upper() not in csv_data and not import_unknown:
        print('Unknown keystore ID, "' + keystore_id + '", and Unknown '
              'Import is disabled.  Skipping item.')
        # Import Unknown disabled. Return unchanged data to calling code.
        return headers, csv_data, False
    
    # Apply change list to CSV Data
    headers, csv_data = update_csv_data(csv_data, headers,
                                        keystore_id, csv_update)
    
    return headers, csv_data, True

def update_csv_data(csv_data, headers, keystore_id, csv_update):
    # Update external keystore fields / rows from JotForm Data
    # Inputs
    # csv_data = {'MYHOSTNAME': {'keystore_id': 'myhostname', 'var': 'value'}}
    # headers = ['keystore_id', 'var_1', 'var_x']
    # keystore_id = 'myhostname'
    # csv_update = {'var_1': 'newdata', 'var_n': 'newdata'}
    # Outputs
    # headers <altered list if any headers missing>
    # csv_data <altered entries, same as above format>

    data = csv_data[keystore_id.upper()]

    for key, value in csv_update.items():
        # On rare chance that source file is empty, create first header.
        # Only occurs if Import Unknown is enabled.
        if not headers:
            headers = ['keystore_id']
            # LOG WARNING
        # Check CSV headers for variable. Add if needed.
        if key not in headers:
            headers.append(key)
            # LOG DEBUG
        
        data.update({key: value})
        csv_data.update({keystore_id.upper(): data})
        # LOG DEBUG
    
    return headers, csv_data

def get_answer_element(answer_dict, ans_idx):
    # Extract answer string or partial answer string if delimiter present
    # Inputs
    # ans_dict = {'text': 'Question 2', 'answer': 'myserial : mymodel'}
    # ans_idx = 1
    # Outputs (watch delimiter)
    # 'mymodel'

    full_answer = answer_dict['answer']
    split_answer = full_answer.split(delimiter)
    # print('Full Answer Text: ' + full_answer)
    if delimiter not in full_answer:
        # LOG WARNING - Delimiter mismatch JotForm/Current Config
        return None
    elif ans_idx + 1 > len(split_answer):
        # LOG WARNING - Answer missing elements
        return None
    if full_answer != null_answer:
        answer_element = full_answer.split(delimiter)[int(ans_idx)]
        return answer_element.strip()
        # LOG DEBUG
    else:
        return None
        # LOG DEBUG

def read_config(config_file):
    # Update external keystore fields / rows from JotForm Data
    # Inputs
    # config_file = '/path/to/jfit-ztp-folder/datamap.json'
    # Outputs
    # config = {'api_key': '<key>', '<vars>': '<values>', 'data_map': {<map>}}

    config = None
    if path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
        # LOG DEBUG
    else:
        pass
        # LOG DEBUG

    if config:
        return config
    else:
        return None

def read_ext_keystore(ext_keystore_file):
    # Update external keystore fields / rows from JotForm Data
    # Inputs
    # ext_keystore_file = '/path/to/ztp-folder/keystore.csv'
    # Outputs
    # headers = ['keystore_id', 'var_1', 'var_x']
    # csv_data = {'MYHOSTNAME': {'keystore_id': 'myhostname', 'var': 'value'}}

    if path.exists(ext_keystore_file):
        csv_path = open(ext_keystore_file, 'r')
        reader = csv.DictReader(csv_path)
        headers = reader.fieldnames
        csv_data = {}
        # Create dictionary wrapper keyed on keystore_id.
        for row in reader:
            csv_data[row['keystore_id'].upper()] = row
            # LOG DEBUG
        
        csv_path.close()
        return headers, csv_data
    
    else:
        return None, None

def write_ext_keystore(ext_keystore_file, headers, csv_data):
    # Update external keystore fields / rows from JotForm Data
    # Inputs
    # ext_keystore_file = '/path/to/ztp-folder/keystore.csv'
    # headers = ['keystore_id', 'var_1', 'var_x']
    # csv_data = {'MYHOSTNAME': {'keystore_id': 'myhostname', 'var': 'value'}}

    try:
        csv_path = open(ext_keystore_file, 'w', newline='')
    except:
        csv_path = open(ext_keystore_file, 'w')
    writer = csv.DictWriter(csv_path, fieldnames=headers)
    writer.writeheader()
    # Strip off dictionary wrapper and write data
    for value in csv_data.values():
        writer.writerow(value)
        # LOG DEBUG
    
    csv_path.close()

def get_new_submissions(api_key, form_id):
    # Query JotForm for new Submissions
    # Inputs
    # api_key = '<hex string>'
    # form_id = '<numeric string>'
    # Output
    # <Requests Response Object with all properties>

    base_url = 'https://api.jotform.com/form/'
    api_filter = '?filter=' + quote('{"status":"ACTIVE","new":"1"}')
    url = (base_url + form_id + '/submissions' + api_filter)
    headers = {'APIKEY': api_key}
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload)
    # Error checking in main().
    return response

def mark_submissions_read(api_key, submission_ids):
    # Query JotForm for new Submissions
    # Inputs
    # api_key = '<hex string>'
    # submission_ids = ['<numeric string>', '<numeric string>']
    # Output
    # <Requests Response Object with all properties> or None

    err_set = None
    base_url = 'https://api.jotform.com/submission/'
    headers = {'APIKEY': api_key}
    payload = {'submission[new]': '0'}
    for item in submission_ids:
        url = (base_url + item)
        response = requests.request('POST', url, headers=headers, data=payload)
        if response.status_code != 200:
            err_set = err_set + '\r\n' + response.text
    
    # Error checking in main().
    if err_set:
        return response
    else:
        return None

def exec_cmds(cmd_set):
    # Send freeZTP commands to system CLI
    # Inputs
    # cmd_set = ['ztp set idarray <name> <serial>', 'another ztp command']
    # Output
    # True / False indicating success / failure

    for command in cmd_set:
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
    
    # Last command restarts ZTP. Verify status.
    if '(running)' in output:
        return True
    else:
        return False

def check_api_key(api_key):
    # Send test query to JotForm. Calling code determines pass/fail actions.
    # Inputs
    # api_key = '<hex string>'
    # Output
    # True / None indicating success / failure

    url = 'https://api.jotform.com/user/usage'
    headers = {'APIKEY': api_key}
    payload = None
    try:
        int(api_key, 16)
    except:
        print('Answer not Hex value.')
        return None
    response = requests.request('GET', url, headers=headers, data=payload)
    if response.status_code == 200:
        return True
    else:
        print('Could not log in with provided key.')
        return None

def query_available_forms(api_key):
    # Request list of "enabled" forms available to API Key
    # Inputs
    # api_key = '<hex string>'
    # Output
    # None or
    # form_set = {'My Form Title': '<num str>', 'My Form Title2': '<num str>'}

    base_url = 'https://api.jotform.com/user/forms'
    api_filter = '?limit=1000&filter=' + quote('{"status":"ENABLED"}')
    url = (base_url + api_filter)
    headers = {'APIKEY': api_key}
    payload = None
    response = requests.request('GET', url, headers=headers, data=payload)
    form_set = {}
    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        for form in response.json()['content']:
            # form_name = form['title'].encode('ascii')
            # form_set.update({form_name.strip(): form['id']})
            form_set.update({form['title']: form['id']})
    
    if len(form_set) > 0:
        return form_set
    else:
        return None

def get_csv_path():
    # Ask user for external keystore path. Validate existance. Retry as needed.
    # Output
    # csv_path = '/path/to/ztp-folder/keystore.csv'

    validated = False
    prompt = 'Enter explicit path to keystore file. (ex. /etc/my.csv) > '
    while not validated:
        csv_path = pyip.inputStr(prompt=prompt)
        if path.exists(csv_path):
            validated = True
        else:
            print('Cannot find file: "' + csv_path + '"')
            result = pyip.inputYesNo('Create empty file? (y/N) > ', blank=True)
            if result == 'yes':
                open(csv_path, 'x')
                validated = True
    return csv_path

def get_import_unknown():
    # Ask user how to deal with unknown keystore ids
    # Output
    # True / False

    print(constants.INFO_IMPORT_UNKNOWN)
    prompt = 'Enable Unknown ID Import? (y/N) > '
    import_unknown = pyip.inputYesNo(prompt=prompt, blank=True)
    if import_unknown == 'yes':
        return True
    else:
        return False

def get_sample_submission(api_key, form_id):
    # Instruct user to submit jotform. Wait for submission. Use data to map
    # answers to freeZTP usable data.
    # Inputs
    # api_key = '<hex string>'
    # form_id = '<num string>'
    # Output
    # submission = {'id': '<num str>, '<vars>': '<vals>', 'answers': {<dict>}}

    print(constants.INFO_SAMPLE_SUBMISSION)
    prompt = 'Hit <enter> after Form is submitted... > '
    pyip.inputStr(prompt=prompt, blank=True)

    response = get_new_submissions(api_key, form_id)
    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        count = response.json()['resultSet']['count']
        submission_ids = []
        for submission in response.json()['content']:
            # submission_ids.append(submission['id'].encode('ascii'))
            submission_ids.append(submission['id'])
        
        if count == 1:
            prompt = 'Select item or hit <enter>. > \r\n'
        else:
            prompt = 'Select item from list. > \r\n'
        sample_submission_id = None
        while not sample_submission_id:
            sample_submission_id = pyip.inputMenu(submission_ids,
                                                  prompt=prompt,
                                                  numbered=True,
                                                  blank=True)
            if count == 1 and not sample_submission_id:
                sample_submission_id = submission_ids[0]

        for submission in response.json()['content']:
            if sample_submission_id == submission['id']:
                return submission
    else:
        print('Failed to get sample submission.')
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))
        sys.exit()

def dict_to_q_menu(ans_set):
    # Create Q&A list for use in PyInputPlus menus.
    # Inputs
    # ans_set = {'1': {'text': 'Question 1', 'answer': 'myhostname'}}
    # Output
    # ans_menu = ['Question: Q1 / Answer: A1 / Control:000x']

    ans_menu = []
    ctrl = 1
    for index in range(len(ans_set)):
        # q_text = ans_set[str(index + 1)]['text'].encode('ascii')
        q_text = ans_set[str(index + 1)]['text']
        try:
            # q_answer = ans_set[str(index + 1)]['answer'].encode('ascii')
            q_answer = ans_set[str(index + 1)]['answer']
        except:
            q_answer = 'None'
        
        # PyIP returns answer text, not answer #.  Control string used for item
        # identification in get_ordinals.
        ans_menu.append('Question: ' + q_text + ' / Answer: ' + q_answer
                           + ' / Control:' + ('0000' + str(ctrl))[-4:])
        ctrl += 1
    return ans_menu

def get_api_key(settings):
    # Ask user for JotForm API Key. settings passed to offer option to use
    # existing configuration.
    # Inputs
    # settings = {'api_key': '<key>', '<vars>': '<vals>', 'data_map': {<map>}}
    # Output
    # api_key = '<hex string>'

    print(constants.INFO_GET_API_KEY)

    old_vals = get_old_vals(settings, ['api_key'])
    if old_vals:
        return old_vals[0]

    validated = False
    prompt = 'What is your API key? > '
    while not validated:
        api_key = pyip.inputStr(
            prompt=prompt,
            blockRegexes=[
                ('.{41,}', 'Answer too long.'),
                (r'\ ', 'Spaces not allowed.')
                ]
            )
        result = check_api_key(api_key)
        if result == True:
            validated = True
    return api_key

def get_form_id(api_key, settings):
    # Ask user for JotForm Form ID. settings passed to offer option to use
    # existing configuration.
    # Inputs
    # settings = {'api_key': '<key>', '<vars>': '<vals>', 'data_map': {<map>}}
    # Output
    # form_id = '<num str>'

    print(constants.INFO_GET_FORM_ID)

    old_vals = get_old_vals(settings, ['form_id'])
    if old_vals:
        return old_vals[0]

    data = query_available_forms(api_key)
    if not data:
        print(constants.FAIL_NO_FORMS_FOUND)
        sys.exit()

    prompt = 'Which Form is being used for this deployment? > \r\n'
    form_name = pyip.inputMenu(list(data.keys()), prompt=prompt, numbered=True)
    return data[form_name]

def get_delimiter(settings):
    # Ask user for delimiter value. settings passed to offer option to use
    # existing configuration.
    # Inputs
    # settings = {'api_key': '<key>', '<vars>': '<vals>', 'data_map': {<map>}}
    # Output
    # delimiter = '<single character>'

    print(constants.INFO_GET_DELIMITER)

    old_vals = get_old_vals(settings, ['delimiter'])
    if old_vals:
        return old_vals[0]

    validated = False
    prompt = 'What is the delimiter? (enter for default [:]) > '
    while not validated:
        delimiter = pyip.inputStr(prompt=prompt, blank=True)
        delimiter = ':' if not delimiter else delimiter
        if len(delimiter) > 1:
            print('Delimiter more than 1 character.')
        else:
            validated = True
    return delimiter

def get_exec_mode(settings):
    # Ask user for Configuration Mode. settings passed to offer option to use
    # existing configuration.
    # Inputs
    # settings = {'api_key': '<key>', '<vars>': '<vals>', 'data_map': {<map>}}
    # Output
    # exec_mode = '<csv or cli>'

    print(constants.INFO_GET_EXEC_MODE)

    old_vals = get_old_vals(settings, ['exec_mode',
         'csv_path', 'import_unknown'])
    if old_vals:
        exec_mode = old_vals[0]
        csv_path = old_vals[1]
        import_unknown = old_vals[2]
        return exec_mode, csv_path, import_unknown
    
    prompt = 'Select script mode. (enter for default [csv]) \r\n'
    exec_mode = pyip.inputMenu(['CLI', 'CSV'], prompt=prompt,
                               blank=True, numbered=True)
    exec_mode = exec_mode.lower() if exec_mode else 'csv'
    if exec_mode == 'csv':
        csv_path = get_csv_path()
        import_unknown = get_import_unknown()
        return exec_mode, csv_path, import_unknown
    else:
        return exec_mode, None, False

def get_null_answer(settings):
    # Ask user for Null Answer. settings passed to offer option to use
    # existing configuration.
    # Inputs
    # settings = {'api_key': '<key>', '<vars>': '<vals>', 'data_map': {<map>}}
    # Output
    # null_answer = '<string>'

    print(constants.INFO_GET_NULL_ANSWER)

    old_vals = get_old_vals(settings, ['null_answer'])
    if old_vals:
        return old_vals[0]

    prompt = 'Specify Null Answer. (enter for default [Select From List]) > '
    null_answer = pyip.inputStr(prompt=prompt, blank=True)
    if not null_answer:
        null_answer = 'Select From List'
    return null_answer

def get_ordinals(ans_set, ans_menu, var_name, prompt):
    # Parse selected answer and ask user to choose sub-answer, if present.
    # Result is ordinal values for 1) which item in the JotForm answer set
    # contains the answer, then 2) which sub-item (if delimiter in string) is
    # the actual value to use.
    # Inputs
    # ans_set = {'1': {'text': 'Question 1', 'answer': 'myhostname'}}
    # ans_menu = ['Question: Q1 / Answer: A1 / Control:000x']
    # var_name = 'keystore_id'
    # prompt = 'Answer with keystore ID?'
    # Output
    # map_dict = {'qID': '1', 'index': 0}

    spaced_delimiter = ' ' + delimiter + ' '
    response = None
    prompt = '\r\n\r\n' + prompt
    response = pyip.inputMenu(ans_menu, prompt=prompt, numbered=True, )
    prompt = '\r\nSelection does not have an answer field.' + prompt
    # Prevent user from choosing a question with no answer (e.g. page title).
    while r' / Answer: None /' in response:
        response = pyip.inputMenu(ans_menu, prompt=prompt, numbered=True, )

    # Read right 4 characters from response (0-prefixed string). Cast as Int
    # to strip leading zeros. Recast as string for dict lookups in ans_set.
    q_id = str(int(response[-4:]))
    # answer_text = ans_set[str(q_id)]['answer'].encode('ascii')
    answer_text = ans_set[str(q_id)]['answer']
    if spaced_delimiter in answer_text:
        compound = answer_text.split(spaced_delimiter)
        prompt = ('Compound answer detected (delimiter in string).\r\n'
                 'Select item that contains ' +  var_name + '. > \r\n')
        response = pyip.inputMenu(compound, prompt=prompt, numbered=True)
        for index, item in enumerate(compound):
            if item == response:
                ans_idx = index
    elif answer_text == null_answer:
        prompt = ('Null Answer found.  Will this answer contain multiple'
                 ' elements separated by the delimiter (' + delimiter + ')?'
                 ' (y/N) > ')
        response = pyip.inputYesNo(prompt=prompt, blank=True)
        if response == 'no' or not response:
            ans_idx = 0
        else:
            prompt = ('Provide numeric ID of element. (First item on left'
                      ' is 1) > ')
            response = pyip.inputNum(prompt=prompt, min=1)
            ans_idx = response - 1
    else:
        ans_idx = 0
    return {'qID': q_id, 'index': ans_idx}

def get_answer(ans_set, var_name, var_dict):
    # Abbreviated version of submission_to_[csv/cli] for setup.  Extracts
    # answer to show to user in setup menu.
    # Inputs
    # ans_set = {'1': {'answer': 'Answer'}}
    # var_name = 'keystore_id'
    # var_dict = {'keystore_id': {'qID': '1', 'index': 0}}
    # Output
    # None or <text, see below>

    q_id = var_dict[var_name]['qID']
    ans_idx = var_dict[var_name]['index']
    ans_dict = ans_set[q_id]
    var_data = get_answer_element(ans_dict, ans_idx)

    if var_data:
        text = ('Q #: ' + q_id + ' / Answer Index: ' + str(ans_idx + 1)
                + '\r\nSample Answer: ' + var_data)
    else:
        text = None
    return text

def get_old_vals(var_dict, var_list, ans_set=None):
    # Extracts 1 or more settings from old settings file. Composes question
    # showing old values and/or data from sample submission.
    # Inputs
    # var_dict = {'keystore_id': {'qID': '1', 'index': 0}}
    # var_dict = {'delimiter': ':'}
    # var_list = ['exec_mode', 'csv_path', 'import_unknown']
    # var_list = ['delimiter']
    # ans_set = *** Optional Answers dictionary from Jotform ***
    # Output
    # var_list_data = ['val1', valx']

    review_info = {}
    var_list_data = []
    populated = True
    # Loop through list
    for item in var_list:
        # None may be passed instead of dictionary
        if var_dict:
            # ans_set only passed for ordinal-based vars, get sub-answers
            if ans_set and item in var_dict:
                text = get_answer(ans_set, item, var_dict)
                if text:
                    review_info.update({item: text})
                    var_list_data.append(var_dict[item])
                else:
                    populated = False
            elif item in var_dict:
                review_info.update({item: var_dict[item]})
                var_list_data.append(var_dict[item])
            else:
                populated = False
        else:
            populated = False
    if not populated:
        return None
    # Old data found.  Ask user.  If yes, send back original data as list
    # in same order as var_list.
    print('Setting from previous setup found:')
    for key, value in review_info.items():
        print(key, ':', value)
    response = pyip.inputYesNo('Reuse this setting? (Y/n) > ', blank=True)
    if response == 'yes' or not response:
        return var_list_data
    else:
        return None

def setup():
    global delimiter, null_answer
    settings = read_config(config_file)

    api_key = get_api_key(settings)
    form_id = get_form_id(api_key, settings)
    delimiter = get_delimiter(settings)
    exec_mode, csv_path, import_unknown = get_exec_mode(settings)
    null_answer = get_null_answer(settings)

    sample_submission_data = get_sample_submission(api_key, form_id)
    ans_set = sample_submission_data['answers']
    ans_menu = dict_to_q_menu(ans_set)
    
    data_map = settings['data_map'] if settings else {}
    # print(data_map)

    print(constants.INFO_KEYSTORE_ID)
    ztp_var = 'keystore_id'
    old_vals = get_old_vals(data_map, [ztp_var], ans_set)
    if old_vals:
        ans_ords = old_vals[0]
    else:
        prompt = 'Choose item that has value for ' + ztp_var + '? > \r\n'
        ans_ords = get_ordinals(ans_set, ans_menu, ztp_var, prompt)
    data_map.update({ztp_var: ans_ords})

    print(constants.INFO_ASSOCIATION)
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
    
    print(data_map)
    print(constants.INFO_SWITCH_STACKS)
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

    print(constants.INFO_CUSTOM_VARIABLES)
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


    dummy = {'api_key': api_key,
             'form_id': form_id,
             'delimiter': delimiter,
             'exec_mode': exec_mode,
             'csv_path': csv_path,
             'import_unknown': import_unknown,
             'null_answer': null_answer,
             'data_map': data_map}

    print(json.dumps(dummy, indent=4))
    with open(config_file, 'w') as f:
        json.dump(dummy, f, indent=4)
    f.close()
    print('Configuration saved to disk.')

    # Marking sample entry as read
    response = mark_submissions_read(api_key, [sample_submission_data['id']])
    if response:
        print('WARNING - FAILED TO MARK SAMPLE SUBMISSION AS READ.\r\n'
              'Verify your API Key permissions before going into'
              ' production.\r\n Your configuration has been saved.')
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))
    else:
        print('Sample submission marked as read.\r\n SETUP COMPLETE!')

def process_data():
    settings = read_config(config_file)
    if not settings:
        print('Configuration file missing.  Please run setup.')
        # LOG ERROR
        sys.exit()
    
    global null_answer, delimiter, import_unknown
    null_answer = settings['null_answer']
    delimiter = settings['delimiter']
    exec_mode = settings['exec_mode']      # cli or csv
    import_unknown = settings['import_unknown']
    csv_path = settings['csv_path']
    data_map = settings['data_map']
    api_key = settings['api_key']
    form_id = settings['form_id']
    restart_ztp = False
    submission_ids = []
    cmd_set = []
    
    response = get_new_submissions(api_key, form_id)
    
    # Process data only if new entries exist
    if (response.status_code == 200
            and response.json()['resultSet']['count'] >= 1):
        response_count = response.json()['resultSet']['count']
        api_calls_left = response.json()['limit-left']

        # LOG INFO - 'New Submissions: ' + response_count
        # LOG INFO - 'Remaining API Calls: ' + str(api_calls_left)

        if api_calls_left < response_count:
            print('Insufficient remaining API calls to service current '
                  'submissions.  Stopping script without processing.')
            # LOG ERROR
            sys.exit()
        
        if exec_mode == 'csv':
            headers, csv_data = read_ext_keystore(csv_path)
            if csv_data == None:
                print('Referenced keystore is missing and execution mode is '
                      'CSV.  Create keystore file or re-run setup.')
                # LOG ERROR
                sys.exit()

        # Loop through all entries
        for submission in response.json()['content']:
            # Build submission list.  Process all before marking as read.
            # LOG DEBUG - Current Submission ID
            submission_ids.append(submission['id'])
            # print('Submission ID: ' + submission['id'])
            ans_set = submission['answers']
            # Prepare ZTP updates based on keystore method: cli or csv.
            if exec_mode == 'cli':
                more_cmds = submission_to_cli(ans_set, data_map)
                restart_ztp = True
                # LOG DEBUG
                cmd_set.extend(more_cmds)
            else:
                headers, csv_data, change_flag = (
                    submission_to_csv(ans_set, data_map, headers,csv_data)
                )
                restart_ztp = True if change_flag else restart_ztp
                # LOG DEBUG
        
        # Post processing tasks (e.g. restart ZTP)

        if restart_ztp:
            if exec_mode == 'csv' and csv_data:
                # if test_mode:
                #     csv_path = csv_path[:-4] + '2.csv'
                write_ext_keystore(csv_path, headers, csv_data)
            elif exec_mode == 'csv' and not csv_data:
                print('Referenced keystore empty (0 bytes) and Unknown '
                    'Import disabled. Stopping script without marking new '
                    'submissions as "read".')
                # LOG ERROR
                sys.exit()
            
            cmd_set.append('ztp service restart')
            # print('\r\n'.join(cmd_set))
            # LOG INFO - '\r\n'.join(cmd_set)
            if test_mode:
                print('\r\n'.join(cmd_set))
            else:
                exec_cmds(cmd_set)
                # LOG INFO - 'Submission Set: ' + ' '.join(submission_ids)
                response = mark_submissions_read(api_key, submission_ids)
                if response:
                    print(response)
                    # LOG DEBUG
                else:
                    # LOG DEBUG
                    pass
        else:
            print('No changes. ZTP not restarted!')
            # LOG INFO
    else:
        print('No new submissions!')
        # LOG INFO

def main():
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'setup':
            print('Hello')
            setup()
        else:
            process_data()
    else:
        process_data()

if __name__ == '__main__':
    global config_file, test_mode
    config_file = 'datamap.json'
    test_mode = False
    main()

