from datetime import datetime, date

import click
import os
import requests
from dateutil import parser


@click.group()
def cli():
    pass


@cli.command("send_issue_info")
@click.argument('issue_id')
@click.argument('web_hook_token')
@click.option('--pullrquest_identification_string', '-p', default='**■ 不具合混入pull requests URL** >')
@click.option('--failure_date_identification_string', '-fd', default='**■ 障害発生日時** >')
@click.option('--failure_resolution_date_identification_string', '-frd', default='**■ 障害解消日時** >')
def send_issue_info(issue_id: str, web_hook_token: str, pullrquest_identification_string: str,
                    failure_date_identification_string: str, failure_resolution_date_identification_string: str):
    url = "https://api.github.com/graphql"
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': 'Bearer ' + token}
    query = """
        query ($id: ID!) {
            node(id: $id) {
              ... on Issue {
                id
                repository {
                  name
                }
                title
                author {
                  login
                }
                body
                url
                state
                labels(orderBy: { direction:ASC, field: NAME }, first: 10) {
                    nodes {
                        name
                    }
                }
                createdAt
                updatedAt
                closedAt
              }
            }
        }"""
    variables = {
        "id": issue_id
    }
    data = {'query': query,
            'variables': variables}
    response = requests.post(url, headers=headers, json=data).json()['data']['node']
    node_labels = set(map(lambda el: el['name'], response['labels']['nodes']))
    payload = {}
    payload['web_hook_token'] = web_hook_token
    payload['author'] = response['author']['login']
    body = response['body']
    payload['body'] = body
    payload['closedAt'] = response['closedAt']
    payload['createdAt'] = response['createdAt']
    payload['id'] = response['id']
    payload['labels'] = ','.join(node_labels)
    payload['repository'] = response['repository']['name']
    payload['state'] = response['state']
    payload['title'] = response['title']
    payload['updatedAt'] = response['updatedAt']
    payload['url'] = response['url']
    # 原因 pullrequest URL
    pullrequest_caused_bug = _get_defected_pull_requests_url(body, pullrquest_identification_string)
    payload['pullrequestCausedBug'] = pullrequest_caused_bug
    failure_info = _get_failure_info(body, failure_date_identification_string,
                                     failure_resolution_date_identification_string)
    payload['failureDatetime'] = failure_info.get("failure_datetime")
    payload['failureCompletionDatetime'] = failure_info.get("failure_completion_datetime")
    payload['time_to_restore_service'] = failure_info.get("time_to_restore_service")
    import json
    json_str = json.dumps(payload, sort_keys=True, indent=2, default=_json_serial)
    f = open('payload.json', 'w')
    f.write(json_str)
    f.close()


def _get_failure_info(description, failure_date_identification_string, failure_resolution_date_identification_string):
    failure_datetime = None
    failure_completion_datetime = None
    time_to_restore_service = None

    for line in description.splitlines():
        if failure_date_identification_string in line:
            failure_datetime = parser.parse(line.split(failure_date_identification_string)[1].strip())

        elif failure_resolution_date_identification_string in line:
            failure_completion_datetime = \
                parser.parse(line.split(failure_resolution_date_identification_string)[1].strip())

    if failure_datetime is not None and failure_completion_datetime is not None:
        time_to_restore_service = (failure_completion_datetime - failure_datetime).total_seconds()

    return {
        'failure_datetime': failure_datetime,
        'failure_completion_datetime': failure_completion_datetime,
        'time_to_restore_service': time_to_restore_service
    }


# date, datetimeの変換関数
def _json_serial(obj):
    # 日付型の場合には、文字列に変換します
    if isinstance(obj, (datetime, date)):
        return obj.isoformat(timespec='milliseconds').replace('.000', 'Z')
    # 上記以外はサポート対象外.
    raise TypeError("Type %s not serializable" % type(obj))


def _get_defected_pull_requests_url(description, pullrquest_identification_string):
    for line in description.splitlines():
        if pullrquest_identification_string in line:
            return line.split(pullrquest_identification_string)[1].strip()
    return ''


if __name__ == '__main__':
    cli()
