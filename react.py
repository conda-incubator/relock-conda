import os

import click
import github


@click.command()
@click.option("--full-name", required=True, type=str)
@click.option("--pr-number", required=True, type=int)
@click.option("--comment-id", required=True, type=int)
def main(full_name, pr_number, comment_id):
    gh = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
    repo = gh.get_repo(full_name)
    pr_as_issue = repo.get_pull(pr_number).as_issue()
    comment = pr_as_issue.get_comment(comment_id)
    comment.create_reaction("rocket")


if __name__ == "__main__":
    main()
