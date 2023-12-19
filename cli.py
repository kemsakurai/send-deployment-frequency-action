import click
import os
import requests


@click.group()
def cli():
    pass


@cli.command("send_issue_info")
@click.argument('issue_id')
@click.option('--label', '-l', default='bug')
@click.argument('web_hook_url')
@click.argument('web_hook_token')
def send_issue_info(issue_id: str, label: str, web_hook_url, web_hook_token):
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
    response = requests.post(url, headers=headers, json=data).json()
    labels = label.split(',')
    node_labels = map(lambda el: el['name'], response['labels']['nodes'])
    if not set(labels.isdisjoint(node_labels)):
        payload = {}
    else:
        print('Since the label to be sent by webhook is not included, the sending process will be skipped.')


if __name__ == '__main__':
    cli()
