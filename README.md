# relock-conda
GitHub action to relock conda environments using conda-lock

## Usage

```yaml
name: relock conda
on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    name: test
    steps:
      - name: run
        uses: beckermr/relock-conda@main
        with:
          # A GitHub personal access token is required
          github-token: ${{ secrets.GITHUB_PAT }}

          # files to relock w/ conda-lock
          # environment-file: environment.yml  # default
          # lock-file: conda-lock.yml  # default

          # optional list of packages whose changes are ignore when relocking
          # ignored-packages: "numpy,scipy"

          # whether to relock on an update to any package in the environment, not just those in the environment file
          # relock-all-packages: false  # default

          # automerge the PR - you need to have GitHub automerge enabled to use this
          # automerge: false  # default
```

See the [action.yml](action.yml) for details on possible inputs and options.
