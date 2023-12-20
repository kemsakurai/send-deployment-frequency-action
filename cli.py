import pprint

import click
import os
import requests


@click.group()
def cli():
    pass


@cli.command("send_issue_info")
@click.argument('issue_id')
@click.argument('web_hook_token')
@click.option('--label', '-l', default='bug')
def send_issue_info(issue_id: str, label: str, web_hook_token: str):
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
    labels = set(label.split(','))
    node_labels = set(map(lambda el: el['name'], response['labels']['nodes']))
    if not labels.isdisjoint(node_labels):
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
        payload['pullrequestCausedBug'] = body
        payload['failureDatetime'] = body
        payload['failureCompletionDatetime'] = body
        import json
        json_str = json.dumps(payload, sort_keys=True, indent=2)
        f = open('payload.json', 'w')
        f.write(json_str)
        f.close()

    else:
        print('Since the label to be sent by webhook is not included, the sending process will be skipped.')


if __name__ == '__main__':
    cli()
