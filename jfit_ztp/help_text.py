"""Help Text for Setup Wizard"""
HELP_JOTFORM_MENU = '''
 ============================JOTFORM API KEY=============================
  Provide your JotForm API key.  Key must have "Full Access" permissions.
  Script only looks for new submissions. Submissions marked "read" when
  data processing and ZTP updates have completed.
 ========================================================================
'''
HELP_FORM_ID_SELECTOR = '''
 ==========================SELECT JOTFORM FORM===========================
  Please select your Form from this list of "enabled" forms.
 ========================================================================
'''
FAIL_FORM_ID_SELECTOR = '''
 ====================== CRITICAL FAILURE ================================
                     NO ENABLED FORMS FOUND!
  1) Verify desired form is accepting new submissions.
  2) Re-run "Test JotForm Key and Connection". Update as needed.
 ====================== CRITICAL FAILURE ================================
'''
HELP_KEYSTORE_CONFIG_MENU = """
 =======================ZTP KEYSTORE UPDATE CONFIG=======================
  Keystore Types
    CLI
        All keystore and idarray information will be stored in freeZTP's
        embedded config file. (Default Setting)
    CSV
        All keystore and idarray information is stored in an external
        keystore file. Association data (template), if not using the
        default, MUST also be stored in the external keystore.

  Import Unknown (ONLY APPLIES TO CSV MODE)
    Default is FALSE.
    Enabling this feature will generate rows in the external keystore for
    non-present items. THIS MAY IMPACT JUST-IN-TIME DEPLOYMENT OPERATIONS.

    EXAMPLE: Keystore with pre-populated management IP. New rows would
    have no value for the management IP.  Deployment may fail.
 ========================================================================
"""
HELP_DELIMITER_QUESTION = '''
 ===============================DELIMITER================================
  JFIT-ZTP will recognize and parse compound answers.  For simplicity
  only 1 (one) single character delimiter is allowed. (NOT space or tab)

  Example compound answer "ab12345 : FOC1111ZXY2 : c9300-48p", where:
    Colon (:) is the delimiter
    ab12345 is an asset tag (Custom Variable)
    FOC1111ZXY2 is a serial number (ID Array)
    c9300-48p is a valid "provision" command value (Custom Variable)

  NOTE: Leading and terminal spaces will be stripped automatically.
 ========================================================================
'''
HELP_NULL_ANSWER_QUESTION = '''
 ==============================NULL ANSWER===============================
  JFIT-ZTP will recognize answers which should be considered equivalent
  to "blank" (null answer). Specify the answer string which should be
  ignored. For simplicity, only one Null Answer is allowed.

  Explanation:
    Most JotForm form elements allow for a default answer in case the
    user skips the question.  For the purposes of ZTP, dropdown lists and
    the Dynamic Dropdown Widget often present the most efficient way to
    get both consistent and accurate answers from data entry personnel.
    When device deployment is widely varied (e.g. switch stacks from 1 to
    8 members), it is expected that some questions should be unanswered.
    Manual data entry should be avoided for obvious reasons.

  Keystore Behavior
    CLI Mode
        Commands will not be generated for items with the Null Answer.
    CSV Mode
        Field will be left blank for items with the Null Answer.

  Example Null Answer: "Please Select Option"
 ========================================================================
'''
HELP_ROOM_ID_SELECTOR = '''
 ==============================SELECT ROOM===============================
  Please select your Room from this list.
 ========================================================================
'''
FAIL_ROOM_ID_SELECTOR = '''
 ====================== CRITICAL FAILURE ================================
                     NO ROOMS FOUND!
  Verify Bot has been added to the room / space.
 ====================== CRITICAL FAILURE ================================
'''
HELP_WEBEX_MENU = '''
 ========================WEBEX TEAMS NOTIFICATION========================
  JFIT-ZTP is capable of sending update notifications through Cisco WebEx
  Teams.  A Bot Token and target room are required for setup.

  Mechanism
    Notifications are sent via WebEx Teams Bot.  This is a user createable
    construct which can be attached to a Teams Room like a user.

  Message Format
    Notifications are formatted in Markdown. A sample is included in the
    Git Repo (new_submision.md). Message templates are found in
    template_text.py with addition comments / instructions.
 ========================================================================
'''
WARN_WEBEX_MENU = '''
 ========================== WARNING =====================================
  Bot Token or Room ID empty. Leaving now will remove configuration.
 ========================================================================
'''
HELP_WEBHOOK_URL_MENU = '''
 ==========================WEBHOOK NOTIFICATION==========================
  JFIT-ZTP is capable of sending update notifications via Webhooks. A URL
  is required for setup.

  Mechanism
    Notifications are sent to a HTTPS listener which is then responsible
    for processing the message and final delivery.
    Only HTTP POST and a header with "'Content-Type': 'application/json'"
    is used. JFIT-ZTP has no authentication mechanism.

  Default Configuration
    JFIT-ZTP includes pre-built formatting (http) for notifications to
    Microsoft Power Automate (MSPA) via Azure.

  Message Format
    JSON is mandatory. Choice of fields is open. "message" is the minimum
    recommended field. Included default format includes HTTP formatted
    message and metadata items for processing by MSPA. Message templates
    are found in template_text.py with addition comments / instructions.
 ========================================================================
'''


# INFO_SAMPLE_SUBMISSION = '''
#  ===========================SAMPLE SUBMISSION============================
#   Setup needs a sample JotForm submission to map answers to freeZTP
#   configuration commands / external keystore entries.\r\n
#   *** PLEASE CREATE AND SUBMIT A FORM NOW ***
#   *** FILL OUT ALL ANSWERS - LEAVE NO DEFAULT ***\r\n
#   The submission ID will show in the url on the "Thank You" page.
#   Ex: https://submit.jotform.com/submit/<15 digit #>\r\n
#   Hit <enter> when ready to view list of forms.
#  ========================================================================
# '''
# INFO_KEYSTORE_ID = '''
#  ==============================KEYSTORE ID===============================
#   Select the answer to map to the Keystore ID
#   The Keystore ID in freeZTP is the common index value between ID Array
#   data, keystore values, and template associations. When using JotForm
#   with freeZTP the Keystore ID is likely to correspond with the hostname.
#  ========================================================================
# '''
# INFO_ASSOCIATION = '''
#  =============================ASSOCIATION ID=============================
#   (OPTIONAL) Will JotForm provide the Association ID Value?
#   The Association ID in freeZTP is mapping of a configuration template to
#   a specific Keystore ID. If no association is specified, freeZTP will
#   use its default value. RECOMMENDATIONS:
#   - CLI Mode: Use freeZTP default value for single template cases. Use
#     JotForm answer mapping when using freeZTP to image multiple platforms
#     (e.g. routers & switches) and/or multiple roles (e.g. core & edge).
#   - CSV Mode: Create "association" column in the external keystore and
#     enter the appropriate field value when pre-loading other data.
#  ========================================================================
# '''
# INFO_SWITCH_STACKS = '''
#  ============================SWITCH STACKING=============================
#   (OPTIONAL) Will this ZTP instance build switch stacks?
#   freeZTP was built as a general purpose imaging system. For switch
#   stacks, multiple IDs (serial numbers) can be assigned to the Keystore
#   ID (idarray). This allows for proper device ID regardless of boot
#   order. If "no" is selected, setup will prompt for one (1) serial number
#   mapping. If "yes" is selected, setup will ask for a maximum stack size,
#   then prompt to map each position.\r\n
#   NOTE: If building mixed-model stacks it is recommended that you include
#   the model information with each serial using the delimiter.'
#   FUN FACTS:
#   1. ID array data is shared with the Jinja2 engine as idarray_x in the
#      order they show up. This can be used for automatic stack re-ordering
#      with EEM scripts.  See sample on the freeZTP GitHub site.
#   2. If building mixed-model stacks, adding model information as a Custom
#      Variable can allow for pre-population of port configurations before
#      member switches join the stack. (switch <#> provision <model>
#      Simplest setup places serial and model in same answer and separated
#      by the delimiter (e.g. <serial> : <model>)
#  ========================================================================
# '''
# INFO_CUSTOM_VARIABLES = '''
#  ============================CUSTOM VARIABLES============================
#   (OPTIONAL) Define Custom Variables
#   Custom variables are mapped from JotForm to freeZTP commands / external
#   keystore fields in the exact same way as other mappings. The difference
#   is that custom variable names are your choice.
#   RESTRICTION: BLANK SPACES ARE NOT ALLOWED IN CUSTOM VARIABLE NAMES\r\n
#   Examples:
#   - model1, model2, modelx: Possible use for mixed-model stacks
#   - snmp_loc: Insert device meta-data in snmp location
#  ========================================================================
# '''
# INFO_x = '''
#  '========================================================================
#  '========================================================================
# )
# FAIL_x = '''
#  '====================== CRITICAL FAILURE ================================
#  '====================== CRITICAL FAILURE ================================
# )
