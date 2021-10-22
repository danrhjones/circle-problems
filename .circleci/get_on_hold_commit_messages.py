#!/usr/bin/env python3

########################################################################
# Retrieve on_hold workflows for the current project, branch, and
# workflow name and get the associated git commit hashes
# Use those hashes to compile a list of the PR titles
########################################################################

import json
import logging
import os
import urllib.request
from urllib.error import HTTPError, URLError
from get_workflows import get_workflows

commits = []

for i in json.loads(json.dumps(get_workflows())):
    commits.append(i['pipeline']['vcs']['revision'])

commitMessages = ""

for commit in commits:

    req = urllib.request.Request(
        url='https://api.github.com/search/issues?q={}'
            .format(commit),
        method='GET',
        headers={'Authorization': 'token {}'.format(os.getenv('github_token'))},
        )
    try:
        with urllib.request.urlopen(req) as response:
            response_raw_body = response.read()
            pythonObj = json.loads(response_raw_body)

    except (HTTPError, URLError) as error:
        logging.error('Data not retrieved because %s\nURL: %s', error, req)
        raise

    for i in pythonObj['items']:
        commitMessages += (i['title'])
        commitMessages += "; "

print(commitMessages)
