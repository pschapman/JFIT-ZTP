"""Notification Templates"""
##################@@## WEBEX TEAMS NOTIFICATIONS ###########################
# (MANDATORY) This variable is consumed by setup.py
# Shows all tags available for merge.
WEBEX_SETUP_MSG = '''#### JFIT Setup
Hi, your WebEx Teams Bot integration is working!! Here are fields you can pass:
JotForm API Key: {{ api_key }}
JotForm Form ID: {{ form_id }}
Compound Answer Delimiter: {{ delimiter }}
freeZTP Keystore Type: {{ keystore_type }}
freeZTP External Keystore: {{ csv_path }}
Import Unknown Flag: {{ import_unknown }}
Default (null) Answer: {{ null_answer }}
WebEx Bot Token: {{ bot_token }}
WebEx Room ID:{{ room_id }}
Webhook URL: {{ webhook_url }}
Data Map: {{ data_map }}
Host FQDN: {{ host_fqdn }}
Keystore ID (Device Name): {{ keystore_id }}
Jotform Submission ID: {{ submission_id }}

---'''

# (MANDATORY) This variable is consumed by worker.py
WEBEX_WORKER_MSG = '''#### JotForm Data Added to freeZTP
{{ keystore_id }} ([{{ submission_id }}](https://jotform.com/edit/{{ submission_id }}))

---'''

####################### WEBHOOK NOTIFICATIONS ##############################
# (Optional) This variable is consumed locally in this file only.
# Setup message separated from payload to provide clarity.
# Shows all tags available for merge.
# Formatted message for Microsoft Power Automate (MSPA) webook via Azure.
# This message format is used for the "Post a message as the Flow bot to a
# channel (preview)" action. This action uses HTTP as the message format.
# As an alternate for MSPA, the "Post a message (V3) (preview)" action
# uses individual data points.  In this case expand the payload dictionary
# to provide individual items instead of formatted text.
WEBHOOK_SETUP_MSG = '''
<p><strong>JFIT Setup</strong></p>
<p>Hi, your Webhook URL is working!! Here are fields you can pass:</p>
<p>JotForm API Key: {{ api_key }}</p>
<p>JotForm Form ID: {{ form_id }}</p>
<p>Compound Answer Delimiter: {{ delimiter }}</p>
<p>freeZTP Keystore Type: {{ keystore_type }}</p>
<p>freeZTP External Keystore: {{ csv_path }}</p>
<p>Import Unknown Flag: {{ import_unknown }}</p>
<p>Default (null) Answer: {{ null_answer }}</p>
<p>WebEx Bot Token: {{ bot_token }}</p>
<p>WebEx Room ID:{{ room_id }}</p>
<p>Webhook URL: {{ webhook_url }}</p>
<p>Data Map: {{ data_map }}</p>
<p>Host FQDN: {{ host_fqdn }}</p>
<p>Keystore ID (Device Name): {{ keystore_id }}</p>
<p>Jotform Submission ID: {{ submission_id }}</p>
<span style="display: none">
'''
# (MANDATORY) This variable is consumed by setup.py
# Payload is a dictionary that will be converted to JSON by calling code.
# Sample fields and intended usage:
#   src-id (str): System distinguisher. 1 Webhook for many script instances.
#       May direct notifications to different destinations.
#   type (str): Message distinguisher. Vary possible actions by level.
#   message (str): Formatted based on target capability (HTML Sample)
WEBHOOK_SETUP_DICT = {
    'src-id': 'jfit-ztp.{{ host_fqdn }}',
    'type': 'status',
    'message': WEBHOOK_SETUP_MSG
}

# (Optional) This variable is consumed locally in this file only.
WEBHOOK_WORKER_MSG = '''
<p><strong>JotForm Data Added to freeZTP</strong></p>
<p>{{ keystore_id }} (<a href="https://jotform.com/edit/{{ submission_id }}">
{{ submission_id }}</a>)</p>
<span style="display: none">
'''

# (MANDATORY) This variable is consumed by worker.py
WEBHOOK_WORKER_DICT = {
    'src-id': 'jfit-ztp.{{ host_fqdn }}',
    'type': 'status',
    'message': WEBHOOK_WORKER_MSG
}
