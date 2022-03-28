"""Menu Text for Setup"""
M_MAIN = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    Jotform Form ID: {{ form_id }}
    JFIT Mode: {{ exec_mode }} / Import Unknown: {{ import_unknown }}
    Answer Delimiter: "{{ delimiter }}"
    Null Answer: "{{ null_answer }}"

       MAIN MENU
    1. Set JotForm API Key
    2. Select JotForm Form ID
    3. Set Execution Mode (CSV / CLI)
    4. Set Delmiter (Compound Answers)
    5. Set Null Answer
    6. Configure Cisco WebEx Teams Notifications
    7. Configure Generic WebHook Notification (ex. MS PowerAutomate)
    8. Configure Jotform Answer Mappings
    H. Display Help
    S. Save
    Q. Save and Quit
    A. Abandon Changes and Quit
'''
M_API_KEY = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    API Key Test Result: {{ test_result }}

       JOTFORM API KEY CONFIGURATION MENU
    1. Set JotForm API Key
    2. Test Jotform Connection
    H. Display Help
    Q. Quit to Main Menu
'''
M_EXEC_MODE = '''
       CURRENT SETTINGS
    JFIT Execution Mode: {{ exec_mode }}
    External Keystore Path: {{ csv_path }}
    Import Unknown: {{ import_unknown }}

       JFIT EXECUTION MODE CONFIGURATION MENU
    1. Toggle JFIT Execution Mode (CLI / CSV)
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
    2. Send Test Message to Webhook
    X. Clear Webhook Configuration
    H. Display Help
    Q. Quit to Main Menu
'''
