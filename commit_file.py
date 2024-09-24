import os

import click
import github


def _get_branch(ref):
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/") :]
    elif ref.startswith("refs/pull/"):
        return "pull/" + ref[len("refs/pull/") : -len("/merge")] + "/head"
    else:
        return ref


@click.command()
@click.option("--repo", required=True, type=str)
@click.option("--ref", required=True, type=str)
@click.option("--filename", required=True, type=str)
@click.option("--commit-message", required=True, type=str)
def main(repo, ref, filename, commit_message):
    branch = _get_branch(ref)
    with open(filename, "r") as f:
        data = f.read()

    gh_token = os.environ["GH_TOKEN"]
    gh = github.Github(auth=github.Auth.Token(gh_token))
    repo = gh.get_repo(repo)
    try:
        contents = repo.get_contents(filename, ref=ref)
    except github.UnknownObjectException:
        contents = None

    if contents is None:
        repo.create_file(
            filename,
            commit_message,
            data,
            branch=branch,
        )
    else:
        repo.update_file(
            contents.path,
            commit_message,
            data,
            contents.sha,
        )


if __name__ == "__main__":
    main()
