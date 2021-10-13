#!/usr/bin/env python3

########################################################################
# Retrieve on_hold workflows for the current project, branch, and
# workflow name and get the associated git commit hashes
# Use those hashes to compile a list of the PR titles
########################################################################

import json
import logging
import operator
import os
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from urllib.error import URLError

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

assert os.getenv('github_token')
assert os.getenv('circle_token')
assert os.getenv('CIRCLE_PROJECT_USERNAME')
assert os.getenv('CIRCLE_PROJECT_REPONAME')
assert os.getenv('CIRCLE_BRANCH')
assert os.getenv('CIRCLE_WORKFLOW_ID')


class PipelineError(Exception):
    pass


logger.info("Retrieving our own workflow information")

req = urllib.request.Request(
    url='https://circleci.com/api/v2/workflow/{}'.format(
        os.getenv('CIRCLE_WORKFLOW_ID')
    ),
    method='GET',
    headers={
        'Circle-Token': os.getenv('circle_token')
    }
)
try:
    with urllib.request.urlopen(req) as response:
        response_raw_body = response.read()
        parsed_response = json.loads(response_raw_body)
        assert parsed_response.get('name'), \
            '‘{}’ has no ‘name’ key which is impossible'.format(parsed_response)
        our_workflow = parsed_response
except (HTTPError, URLError) as error:
    logging.error('Data not retrieved because %s\nURL: %s', error, req)
    raise

project_pipelines_url = (
    "https://circleci.com/api/v2/project/github/{}/{}/pipeline?{}"
).format(
    os.getenv('CIRCLE_PROJECT_USERNAME'),
    os.getenv("CIRCLE_PROJECT_REPONAME"),
    urllib.parse.urlencode({
        'branch': os.getenv("CIRCLE_BRANCH"),
    })
)
req = urllib.request.Request(
    url=project_pipelines_url,
    method='GET',
    headers={
        'Circle-Token': os.getenv('circle_token')
    }
)
try:
    with urllib.request.urlopen(req) as response:
        response_raw_body = response.read()
        parsed_response = json.loads(response_raw_body)
except PipelineError:
    logger.exception("Exception while retrieving recent builds from CircleCI")
    raise

pipelines = parsed_response['items']

assert 0 < len(pipelines), \
    'Circle thinks there are no pipasdsafdsfelines which is impossible'

logger.info('Found %d pipelines', len(pipelines))

workflows = []
for pipeline in pipelines:
    pipeline_workflow_url = "https://circleci.com/api/v2/pipeline/{}/workflow" \
        .format(pipeline['id'])
    req = urllib.request.Request(
        url=pipeline_workflow_url,
        method='GET',
        headers={
            'Circle-Token': os.getenv('circle_token'),
            'Accept': 'application/json'
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            response_raw_body = response.read()
            parsed_response = json.loads(response_raw_body)
    except BaseException:
        logger.exception(
            "Exception while retrieving recent builds from CircleCI")
        raise

    for workflow in parsed_response['items']:
        assert workflow.get('name'), \
            '‘{}’ has no ‘name’ key which is impossible'.format(
                workflow
            )
        if workflow['name'] == our_workflow['name']:
            if workflow['status'] == 'on_hold':
                workflow['pipeline'] = pipeline
                workflows.append(workflow)

workflows.sort(key=operator.itemgetter('created_at'))

pythonObj = json.loads(json.dumps(workflows))
commits = []
for i in pythonObj:
    commits.append(i['pipeline']['vcs']['revision'])

assert 0 < len(workflows), \
    'CircleCI thinks there are no workflows which is impossible'

for workflow in workflows:
    assert workflow.get('id'), \
        '‘{}’ has no ‘id’ key which is impossible'.format(workflow)

commitMessages = []

for commit in commits:

    req = urllib.request.Request(
        url='https://api.github.com/search/issues?q={}'
            .format(commit),
        method='GET',
        headers={
            'Authorization': 'token {}'.format(os.getenv('github_token'))
            },
        )
    try:
        with urllib.request.urlopen(req) as response:
            response_raw_body = response.read()
            pythonObj = json.loads(response_raw_body)

    except (HTTPError, URLError) as error:
        logging.error('Data not retrieved because %s\nURL: %s', error, req)
        raise

    for i in pythonObj['items']:
        commitMessages.append(i['title'])

print(commitMessages)
