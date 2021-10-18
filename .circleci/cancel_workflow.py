#!/usr/bin/env python3

########################################################################
# Cancel on_hold circleci workflows for the current project
########################################################################
import json
import logging
import os
import urllib.request
from urllib.error import HTTPError, URLError

from get_on_hold_commit_messages import Workflow

assert os.getenv('circle_token')
assert os.getenv('CIRCLE_WORKFLOW_ID')

workflow_ids = []
for i in Workflow.get_workflows():
    workflow_ids.append(i['id'])

start = workflow_ids.index(os.getenv('CIRCLE_WORKFLOW_ID'))
del workflow_ids[start:len(workflow_ids)]
print(workflow_ids)
for workflow_id in workflow_ids:
    req = urllib.request.Request(
        url='https://circleci.com/api/v2/workflow/{}/cancel'.format(workflow_id),
        method='POST',
        headers={'Circle-Token': os.getenv('circle_token')}
    )
    try:
        with urllib.request.urlopen(req) as response:
            print("this working?")
            response_raw_body = response.read()
            parsed_response = json.loads(response_raw_body)
            if parsed_response.get('message') == "Accepted.":
                print("cancelled {}".format(workflow_id))
            else:
                print("nothing to cancel")

    except (HTTPError, URLError) as error:
        logging.error('Data not retrieved because %s\nURL: %s', error, req)
        raise
