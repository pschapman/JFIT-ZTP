"""Menu Text for Setup"""
M_MAIN = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    Jotform Form ID: {{ form_id }}
    JFIT Mode: {{ exec_mode }}
    Answer Delimiter: "{{ delimiter }}"
    Null Answer: "{{ null_answer }}"

       MAIN MENU
    1. Set JotForm API Key
    2. Select JotForm Form ID
    3. Set Execution Mode (CSV / CLI)
    4. Set Delmiter (Compound Answers)
    5. Set Null Answer
    6. Configure Cisco WebEx Teams Notifications
    7. Configure Generic WebHook Notification
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
