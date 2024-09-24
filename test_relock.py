from relock import _split_package_list
from commit_file import _get_branch

import pytest


@pytest.mark.parametrize(
    "input,output",
    [
        ("", []),
        ("\n,\n\n", []),
        (",", []),
        ("\n", []),
        ("conda", ["conda"]),
        ("conda, python", ["conda", "python"]),
        (
            "\nconda, python\nblah,blah\n,\nfoo bar\n",
            ["conda", "python", "blah", "blah", "foo", "bar"],
        ),
    ],
)
def test_split_package_list(input, output):
    assert _split_package_list(input) == output


@pytest.mark.parametrize(
    "ref,branch",
    [("refs/heads/main", "main"), ("refs/pull/123/merge", "pull/123/head")],
)
def test_get_branch(ref, branch):
    assert _get_branch(ref) == branch
