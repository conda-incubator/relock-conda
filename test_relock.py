from relock import _split_package_list

import pytest


@pytest.mark.parametrize("input,output", [
    ("", []),
    ("conda", ["conda"]),
    ("conda,python", ["conda", "python"]),
    ("conda, python\nblah,blah", ["conda", "python", "blah", "blah"]),
])
def test_split_package_list(input, output):
    assert _split_package_list(input) == output
