"""Menu Text for Setup"""
M_MAIN = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    Jotform Form ID: {{ form_id }}
    freeZTP Keystore Type: {{ keystore_type }}
    Answer Delimiter: "{{ delimiter }}"
    Null Answer: "{{ null_answer }}"

         MAIN MENU
         ---------
    1. Set JotForm API Key
    2. Set freeZTP Keystore Type (CSV / CLI)
    3. Set Delmiter (Compound Answers)
    4. Set Null Answer
    5. Configure Cisco WebEx Teams Notifications
    6. Configure Generic WebHook Notifications (ex. MS PowerAutomate)
    7. Configure Jotform Answer Mappings
    S. Save
    Q. Save and Quit
    A. Abandon Changes and Quit
'''
M_JOTFORM = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    API Key Test Result: {{ test_result }}
    Jotform Form ID: {{ form_id }}

         JOTFORM CONNECTION CONFIGURATION MENU
         -------------------------------------
    1. Set JotForm API Key
    2. Test Jotform Key and Connection
    3. Select Jotform Form ID
    H. Display Help
    Q. Quit to Main Menu
'''
M_KEYSTORE_TYPE = '''
       CURRENT SETTINGS
    freeZTP Keystore Type: {{ keystore_type }}
    External Keystore Path: {{ csv_path }}
    Import Unknown: {{ import_unknown }}

         ZTP KEYSTORE CONFIGURATION MENU
    1. Toggle freeZTP Keystore Type (CLI / CSV)
    2. Set External Keystore Path
    3. Toggle Import Unknown
    H. Display Help
    Q. Quit to Main Menu
'''
M_WEBEX = '''
       CURRENT SETTINGS
    WebEx Teams Bot Token: {{ bot_token }}
    Bot Token Test Result: {{ test_result }}
    WebEx Teams Room ID: {{ room_id }}

       WEBEX TEAMS NOTIFICATIONS CONFIGURATION MENU
    1. Set WebEx Teams Bot Token
    2. Test Bot Token
    3. Select Teams Room
    4. Send Test Message to Room
    X. Clear Teams Configuration
    H. Display Help
    Q. Quit to Main Menu
'''
M_WEBHOOK = '''
       CURRENT SETTINGS
    Webhook URL: {{ webhook_url }}

       GENERIC WEBHOOK CONFIGURATION MENU
    1. Set Webhook URL
    2. Print Test Rendered Message Payload to Screen
    3. Send Test Message to Webhook
    X. Clear Webhook Configuration
    H. Display Help
    Q. Quit to Main Menu
'''
