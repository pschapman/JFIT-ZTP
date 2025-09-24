#!/usr/bin/env python3
"""
Setup menu text with Jinja2 tags
"""
M_MAIN = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    Jotform Form ID: {{ form_id }}
    freeZTP Keystore Type: {{ keystore_type }}
    Answer Delimiter: "{{ delimiter }}"
    Null Answer: "{{ null_answer }}"

           MAIN
           ----
    1. Set JotForm API Key
    2. Set freeZTP Keystore Type (CSV / CLI)
    3. Configure Jotform Answer Mappings
    S. Save
    Q. Save and Quit
    A. Abandon Changes and Quit
        ~~ OPTIONAL CONFIGURATION ~~
    4. Set Delmiter (Compound Answers)
    5. Set Null Answer
    6. Configure Cisco WebEx Teams Notifications
    7. Configure Generic WebHook Notifications (ex. MS PowerAutomate)
'''
M_JOTFORM = '''
       CURRENT SETTINGS
    Jotform API Key: {{ api_key }}
    API Key Test Result: {{ test_result }}
    Jotform Form ID: {{ form_id }}

         JOTFORM CONNECTION CONFIGURATION
         --------------------------------
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

         ZTP KEYSTORE CONFIGURATION
         --------------------------
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

         WEBEX TEAMS NOTIFICATIONS CONFIGURATION
         ---------------------------------------
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

         GENERIC WEBHOOK CONFIGURATION
         -----------------------------
    1. Set Webhook URL (No input = clear config)
    2. Print Test Message to Screen (Payload)
    3. Send Test Message to Webhook
    H. Display Help
    Q. Quit to Main Menu
'''
M_DATAMAP_MAIN = '''
       CURRENT SETTINGS
    Maximum Stack Size: {{ mss }}
    Sample Submission: {{ sample_state }}

         DATA MAP CONFIGURATION
         ----------------------
    1. Change Stack Size
    2. Update Sample Submission
    3. Set Keystore ID / ID Array Mappings (Mandatory)
    4. Set Custom Variable Mappings (Optional)
    X. Delete All Mappings
    H. Display Help
    Q. Quit to Main Menu
'''
M_DATAMAP_MANDATORY = '''
       CURRENT SETTINGS (Jotform Question | Answer ID | Sub-answer Index)
    keystore_id: {{ k_id.q_text }} | {{ k_id.a_id }} | {{ k_id.a_idx }}
    idarray_1: {{ id_arr1.q_text }} | {{ id_arr1.a_id }} | {{ id_arr1.a_idx }}
{% if mss >= 2 %}    idarray_2: {{ id_arr2.q_text }} | {{ id_arr2.a_id }} | {{ id_arr2.a_idx }}{% endif %}
{% if mss >= 3 %}    idarray_3: {{ id_arr3.q_text }} | {{ id_arr3.a_id }} | {{ id_arr3.a_idx }}{% endif %}
{% if mss >= 4 %}    idarray_4: {{ id_arr4.q_text }} | {{ id_arr4.a_id }} | {{ id_arr4.a_idx }}{% endif %}
{% if mss >= 5 %}    idarray_5: {{ id_arr5.q_text }} | {{ id_arr5.a_id }} | {{ id_arr5.a_idx }}{% endif %}
{% if mss >= 6 %}    idarray_6: {{ id_arr6.q_text }} | {{ id_arr6.a_id }} | {{ id_arr6.a_idx }}{% endif %}
{% if mss >= 7 %}    idarray_7: {{ id_arr7.q_text }} | {{ id_arr7.a_id }} | {{ id_arr7.a_idx }}{% endif %}
{% if mss >= 8 %}    idarray_8: {{ id_arr8.q_text }} | {{ id_arr8.a_id }} | {{ id_arr8.a_idx }}{% endif %}
.
         MANDATORY MAPPINGS
         ------------------
    1. Map keystore_id
    2. Map idarray_1
{% if mss >= 2 %}    3. Map idarray_2{% endif %}
{% if mss >= 3 %}    4. Map idarray_3{% endif %}
{% if mss >= 4 %}    5. Map idarray_4{% endif %}
{% if mss >= 5 %}    6. Map idarray_5{% endif %}
{% if mss >= 6 %}    7. Map idarray_6{% endif %}
{% if mss >= 7 %}    8. Map idarray_7{% endif %}
{% if mss >= 8 %}    9. Map idarray_8{% endif %}
    H. Display Help
    Q. Quit to Data Map Menu
'''
M_DATAMAP_CUSTOM = '''
       CURRENT SETTINGS (Jotform Question | Answer ID | Sub-answer Index)
{{ settings }}

         CUSTOM VARIABLE MAPPINGS
         ------------------------
    1. Add Custom Variable
    2. Remove Custom Variable
    T. Add Template Association Variable (special use cases)
    H. Display Help
    Q. Quit to Data Map Menu
'''
