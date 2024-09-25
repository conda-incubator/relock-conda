# relock-conda
[![tests](https://github.com/conda-incubator/relock-conda/actions/workflows/tests.yml/badge.svg)](https://github.com/conda-incubator/relock-conda/actions/workflows/tests.yml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/conda-incubator/relock-conda/main.svg)](https://results.pre-commit.ci/latest/github/conda-incubator/relock-conda/main)

GitHub action to relock conda environments using conda-lock

This action runs [conda-lock](https://github.com/conda/conda-lock) to relock a conda environment. Some features include

- responding to comments on PRs to relock the environment (comment with `/relock-conda` to trigger)
- running on a schedule to relock the environment
- customization of which package version updates trigger a relock

## Usage

```yaml
name: relock conda
on:
  workflow_dispatch:
  issue_comment:

jobs:
  test:
    runs-on: ubuntu-latest
    name: test
    steps:
      - name: checkout
        uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332

      - name: run
        uses: conda-incubator/relock-conda@main
        with:
          # A GitHub personal access token is required
          github-token: ${{ secrets.GITHUB_PAT }}

          # files to relock w/ conda-lock
          environment-file: environment.yml  # default
          lock-file: conda-lock.yml  # default

          # optional list of packages whose changes are ignore when relocking
          ignored-packages: ""  # default
          # ignored-packages: "numpy,scipy"

          # use only these packages to determine if a relock is needed
          include-only-packages: ""  # default
          # include-only-packages: "numpy,scipy"

          # whether to relock on an update to any package in the environment,
          # not just those in the environment file
          relock-all-packages: false  # default

          # action to take if we relock
          # one of 'pr' (make a PR) or 'file' (leave new lock file in CWD)
          # or 'commit' (commit new lock file to the repo)
          # if triggered by a comment, this input is ignored and the action
          # will always commit the new lock file
          action: 'pr'  # default

          # these options apply only if we are making PRs
          # automerge the PR - you need to have GitHub automerge enabled
          automerge: false  # default

          # use this setting to fix issues with the base branch not
          # being inferred correctly
          # See https://github.com/peter-evans/create-pull-request/blob/main/docs/concepts-guidelines.md#events-which-checkout-a-commit
          base-branch: ""  # default
          # base-branch: blah

          # the head branch for PRs
          head-branch: relock-conda  # default

          # whether to skip relocking if a PR already exists
          skip-if-pr-exists: false  # default

          # whether to open the PR as a draft
          draft: false  # default
```

See the [action.yml](action.yml) for details on possible inputs and options.
