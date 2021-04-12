# JotForm Form Import Tool for freeZTP (JFIT-ZTP)
## Introduction
JFIT-ZTP is simply a data extraction tool.  It maps answer data from JotForm to functional configuration for freeZTP.

**What is JotForm?** JotForm is a flexible form generation platform.  They offer both free and paid subscription services.  Subscription level will determine  monthly submission, storage, and API call limits among other features.  Please visit [jotform.com](https://www.jotform.com) for more details.

**What is freeZTP?** freeZTP (or just ZTP) is an open-source project which automates deployment of Cisco switches and routers. Cisco has included a unique first-boot behavior in IOS / IOS-XE for Zero Touch Provisioning.  See [packetsar/freeztp](https://github.com/PackeTsar/freeztp) on GitHub for more details.

**Additional Reading** If the README didn't put you to sleep, then try the ["Practical Guide"](documentation/practical_stack_guide.md) posted in documentation.

## Background
freeZTP has been instrumental for time savings in large scale deployments of Cisco switches (500 to 1500 units).  Several issues related to planning and logistics have been seen in these projects.  

**Staging -** From the perspective of a VAR or consulting company, staging is a time consuming task which adds cost to the project. Staging assumes that the IDF design and site details are known.  Once a device has been staged for a specific site that device can only be used there (short of wiping the config).

**Logisitics -** From the perspective of the warehouse team, finding a single serial number to deploy to a remote site could be extremely time consuming.  Allowing the warehouse to simply match model when preparing a site shipment is extremely efficient.

**Proposed Solution -**  Simply send the correct number of each device model to a site.  Have the field team install equipment according to documented plans and use ZTP to deploy the appropriate configuration.  This is where JFIT-ZTP comes in.  The field team will create the serial-to-hostname mapping by entering the data in JotForm from their smartphones.  JFIT-ZTP will pick up the new entries from JotForm and apply the configuration to ZTP automatically. (NOTE: DOA failure rates are typically 0.1%, so the field team should be supplied with spares to ensure completion on the first visit.)

## Mechanism
JFIT-ZTP allows for CLI style or external keystore (CSV) style configuration of ZTP. In CLI style, Jotform data is mapped to CLI commands (see image below).  In CSV style, Jotform data is mapped to fields in the external keystore.  After updates are made to ZTP, the ZTP service is automatically restarted by JFIT-ZTP. Per the freeZTP documentation, idarray and keystore data is passed to the Jinja2 template engine for use in configuration templates.

After updates to ZTP are executed the JotForm submissions are marked "read".  This limits the returned data for each execution of JFIT-ZTP and speeds up processing.

**NOTE:** In CSV style, IDArray and KeyStore data is mapped into the external keystore. Association (template) mapping can use the ZTP default, a static field in the CSV, or dynamic data from JotForm.
![Data Flow](documentation/dataflow.png)

## Compatibility
- Platforms: Ubuntu 20.04LTS
- Python: 2.7 (caveats) & 3.9


## Installation
This procedure assumes that you have already installed freeZTP and it is running as expected.
1. Log in with same account that ZTP is running under
2. Elevate your permissions
   1. `sudo su`
3. Install PyInputPlus (Used for setup wizard only.)
   1. `pip install pyinputplus`
4. Edit PyInputPlus module (Only if running python 2.7 (default for current ZTP version))
    1.  Use Nano or vi to edit `/usr/local/lib/python2.7/dist-packages/pyinputplus/__init__.py`
    2.  Go to line 134
    3.  Change `(prompt, str)` to `(prompt, (str, unicode))`
    4.  Go to line 156
    5.  Change `input()` to `raw_input()`
5. Directly copy files to ZTP server or clone GitHub repo (shown)
   1. `git clone https://github.com/pschapman/jfit-ztp`
6. Change working directory to jfit-ztp
   1. `cd jfit-ztp`
7. Run JFIT-ZTP setup
   1. `python jfit-ztp.py -s` or `python jfit-ztp.py --setup`
8. Carefully read prompts and answer accurately
   1. Provide your API Key
   2. Select Form that is used for this project from list
   3. Input delimiter for compound answers
   4. Select CSV or CLI execution mode from list
   5. Input JotForm Default Answer
   6. As prompted, create a sample submission for your form
   7. Select sample submission from list
   8. Select whether Association (template) data will come from Jotform
   9. Select answer in submission that contains the keystore ID (hostname)
   10. Select whether ZTP will be building stacks
   11. Select answer for each stack member that contains the device ID (idarray)
   12. Select whether additional Custom Variables should be mapped
9. Configure JFIT-ZTP to run as a cron job
    1.  `crontab -e`
    2.  Add: `* * * * * cd /<path>/jfit-ztp&&python jfit-ztp.py`
    3.  Save update and exit
    4.  Restart cron service: `systemctl restart cron`
    5.  **NOTE:** Once per minute is recommended for active implementation.
    6.  **WARNING:** JotForm limits API calls per day, so verify you will not exceed your limit before configuring your cron job.

## Open Issues for v0.9.3 Beta
- Python 2.7 imports JSON data fields as unicode strings.  This causes a vaidation issue on the "prompt" in PyInputPlus.  Current workaround is to hack PyInputPlus, adding unicode as a valid class for the prompt field.
- Native input() function in Python 2.7 expects an expression or function, and not a user input string. raw_input() in 2.7 is equivalent to input() in 3.x.  PyInputPlus uses the 3.x style.  Current workaround is to hack PyInputPlus, changing input() to raw_input().
- Possible issue in get_form_id().  If only 1 form in list PyInputPlus may error out.

## Future features
- Running setup additional times will update all fields, but will not remove mappings that no longer apply.  Setup logic likely needs a rewrite to fix.  **Workaround** by deleting datamap.json and run setup from the beginning.

## Change Log
- 0.9 Beta - Initial release
- 0.9.2 Beta
  - Realized error in trying to manually parse CLI arguments.  Switched to ArgParse native module.  Setup now uses -s / --setup arguments.
  - File and console logging added.  File logging is 'Info' by default (changable in code).  Console logging is disabled by default and can be enabled with -v and -d options, meaning verbose (Info) and debug respectively.
  - Fixed logic error regarding delimiters in get_answer_element.
  - Updated install instructions in readme.
- 0.9.3 Beta
  - Altered update logic to automatically clear fields that have the Null Answer in the JotForm submission.  For CLI style, JFIT-ZTP now issues `ztp clear` commands as needed.  For CSV style, JFIT-ZTP will clear any data from the appropriate field.
  - Added simple WebEx Teams notification feature.  Add your Bot Token and room during setup. Mardown file with sample added to Git Repo.