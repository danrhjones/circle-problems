#!/usr/bin/env python3

########################################################################
# Cancel on_hold circleci workflows for the current project
########################################################################
import json
import logging
import operator
import os
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

assert os.getenv('circle_token')
assert os.getenv('CIRCLE_WORKFLOW_ID')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


class PipelineError(Exception):
    pass


class Cancel:
    @classmethod
    def get_workflows(self):
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
            'Circle thinks there are no pipelines which is impossible'

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
                    if workflow['id'] == os.getenv('CIRCLE_WORKFLOW_ID'):
                        workflows.append(workflow)

        workflows.sort(key=operator.itemgetter('created_at'))

        assert 0 < len(workflows), \
            'CircleCI thinks there are no workflows which is impossible'

        for workflow in workflows:
            assert workflow.get('id'), \
                '‘{}’ has no ‘id’ key which is impossible'.format(workflow)

        return json.loads(json.dumps(workflows))

workflow_ids = []
for i in Cancel.get_workflows():
    workflow_ids.append(i['id'])

start = workflow_ids.index(os.getenv('CIRCLE_WORKFLOW_ID'))
del workflow_ids[start:len(workflow_ids)]
print(workflow_ids)
if not workflow_ids:
    print("nothing to cancel")
else:
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
                print("cancelled {}".format(workflow_id))

        except (HTTPError, URLError) as error:
            logging.error('Data not retrieved because %s\nURL: %s', error, req)
            raise
