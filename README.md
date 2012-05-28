## Work Summarizer


### What it does

1. It creates  daily summary of things you have done by creating a summary of commits, messages left on tickets and so on.
2. It sends a daily email of this to everyone on your team.

### Supported Tools

1. Assembla
2. (Todo) Github

### Usage

Add your authentication details in `auth.py`  
Add list of email recipients in `recipients.py`  
`python summarize.py` will create the summary and email it.  
`python summarize.py noemail` will print the summary to stdout.  

### Requirements
See requirements.txt

Assembla API via: https://github.com/agiliq/assembla
Github API via: https://github.com/ask/python-github2
