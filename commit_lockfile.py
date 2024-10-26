import os
import subprocess

import click
import github


def _get_repo_owner_and_name():
    res = subprocess.run(
        ["git", "remote", "get-url", "--push", "origin"],
        shell=True,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError("Could not get repo name")
    parts = res.stdout.strip().split("/")
    return parts[-2], parts[-1][: -len(".git")]


def _get_current_branch():
    res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        shell=True,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError("Could not get current branch")
    return res.stdout.strip()


@click.command()
@click.option("--lock-file", required=True, type=click.Path())
def main(
    lock_file,
):
    repo_owner, repo_name = _get_repo_owner_and_name()
    branch = _get_current_branch()
    gh = github.Github(auth=github.Auth.Token(os.eviron["GH_TOKEN"]))
    repo = gh.get_repo(f"{repo_owner}/{repo_name}")

    contents = repo.get_contents(lock_file, ref=branch)
    with open(lock_file, "r") as f:
        new_lockfile_content = f.read()

    res = repo.update_file(
        contents.path,
        "relock w/ conda-lock",
        new_lockfile_content,
        contents.sha,
        branch=branch,
    )
    print(
        f"Updated {lock_file} in {repo_owner}/{repo_name} on branch {branch} w/ commit {res['commit'].sha}",
        flush=True,
    )


if __name__ == "__main__":
    main()
