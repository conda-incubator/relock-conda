from relock import _split_package_list

import pytest


@pytest.mark.parametrize("input,output", [
    ("", []),
    ("\n,\n\n", []),
    (",", []),
    ("\n", []),
    ("conda", ["conda"]),
    ("conda,python", ["conda", "python"]),
    ("\nconda, python\nblah,blah\n,\n\n", ["conda", "python", "blah", "blah"]),
])
def test_split_package_list(input, output):
    assert _split_package_list(input) == output
