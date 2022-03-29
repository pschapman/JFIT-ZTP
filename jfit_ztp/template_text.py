"""Notification Templates"""
WEBEX_TEST = '''#### JFIT Setup
Hi, your WebEx Teams Bot integration is working!!
{{ api_key }}
{{ form_id }}
{{ delimiter }}
{{ keystore_type }}
{{ csv_path }}
{{ import_unknown }}
{{ null_answer }}
{{ bot_token }}
{{ room_id }}
{{ webhook_url }}
{{ data_map }}

---'''

# WEBEX_MSG = '''#### JotForm Data Added to freeZTP
# {{ keystore_id }} ([{{ submission_id }}](https://jotform.com/edit/{{ submission_id }}))

# ---'''

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
# Payload is a dictionary that will be converted to JSON by calling code.
# Sample fields and intended usage:
#   src-id (str): System distinguisher. 1 Webhook for many script instances.
#       May direct notifications to different destinations.
#   type (str): Message distinguisher. Vary possible actions by level.
#   message (str): Formatted based on target capability (HTML Sample)
WEBHOOK_SETUP_PAYLOAD = {
    'src-id': '{{ host_fqdn }}',
    'type': 'status',
    'message': WEBHOOK_SETUP_MSG
}

# WEBHOOK_WORKER_PAYLOAD = ('<p><strong>JotForm Data Added to freeZTP</strong></p>'
#             '<p>{{ keystore_id }} (<a href="https://jotform.com/edit'
#             '/{{ submission_id }}">{{ submission_id }}</a>)</p>'
#             '<span style="display: none">')
