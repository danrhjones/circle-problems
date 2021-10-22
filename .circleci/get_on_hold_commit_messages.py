#!/usr/bin/env python3

########################################################################
# Retrieve the git commit messages for a list of circleci workflows
########################################################################

import json
import logging
import os
import urllib.request
from urllib.error import HTTPError, URLError
from get_workflows import get_workflows

commits = []

for workflow in get_workflows():
    commits.append(workflow['pipeline']['vcs']['revision'])

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
