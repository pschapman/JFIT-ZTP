""" blah """

# Python native modules
import logging

# Private modules
from . import shared

# Begin logging inside module, parent initializes configuration
log = logging.getLogger(__name__)

def process_data(config_file):
    """
    Operational data processing
    """
    settings = shared.read_config(config_file)
    if not settings:
        # Error logged in read_config
        sys.exit()

    # global null_answer, delimiter, import_unknown, bot_token, room_id
    null_answer = settings['null_answer']
    delimiter = settings['delimiter']
    bot_token = settings['bot_token']
    room_id = settings['room_id']
    exec_mode = settings['exec_mode']      # cli or csv
    import_unknown = settings['import_unknown']
    csv_path = settings['csv_path']
    data_map = settings['data_map']
    api_key = settings['api_key']
    form_id = settings['form_id']
    azure_url = settings['azure_url']
    restart_ztp = False
    submission_ids = []
    cmd_set = []

    response = get_new_submissions(api_key, form_id)

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

        if exec_mode == 'csv':
            headers, csv_data = read_ext_keystore(csv_path)
            if csv_data is None:
                # Error logged in read_ext_keystore
                sys.exit()

        mkdn_form = ('#### JotForm Data Added to freeZTP\r\n'
                    '{{ keystore_id }} ([{{ submission_id }}]'
                    '(https://jotform.com/edit/{{ submission_id }})) '
                    '\r\n\r\n---')

        html_form = ('<p><strong>JotForm Data Added to freeZTP</strong></p>'
                    '<p>{{ keystore_id }} (<a href="https://jotform.com/edit'
                    '/{{ submission_id }}">{{ submission_id }}</a>)</p>'
                    '<span style="display: none">')
        msgblob = {}
        msgblob['src-id'] = pyfile + '.' + hostfqdn
        msgblob['type'] = 'status'

        # Loop through all entries
        for submission in response.json()['content']:
            # Build submission list.  Process all before marking as read.
            # LOG DEBUG - Current Submission ID
            submission_ids.append(submission['id'])
            ans_set = submission['answers']
            # Prepare ZTP updates based on keystore method: cli or csv.
            if exec_mode == 'cli':
                more_cmds, keystore_id = submission_to_cli(ans_set, data_map)
                restart_ztp = True
                cmd_set.extend(more_cmds)
            else:
                headers, csv_data, change_flag, keystore_id = (
                    submission_to_csv(ans_set, data_map, headers,csv_data)
                )
                restart_ztp = True if change_flag else restart_ztp

            if bot_token and keystore_id:
                markdown = jinja(mkdn_form).render(
                    submission_id=submission['id'], keystore_id=keystore_id
                    )
                send_webex_msg(markdown)

            if azure_url and keystore_id:
                msgblob['message'] = jinja(html_form).render(
                    submission_id=submission['id'], keystore_id=keystore_id
                    )
                payload = json.dumps(msgblob)
                send_powerautomate_msg(azure_url, payload)

        # Post processing tasks (e.g. restart ZTP)
        log.info('All submissions processed.')
        log.debug('Submission Set: %s', ' '.join(submission_ids))

        if restart_ztp:
            if exec_mode == 'csv' and csv_data:
                # Test harness to write to alternate external keystore file
                # if test_mode:
                #     csv_path = csv_path[:-4] + '2.csv'
                write_ext_keystore(csv_path, headers, csv_data)
            elif exec_mode == 'csv' and not csv_data:
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
                response = mark_submissions_read(api_key, submission_ids)
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
