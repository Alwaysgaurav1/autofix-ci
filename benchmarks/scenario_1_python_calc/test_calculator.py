from calculator import add, multiply


def test_add_positive_numbers():
    assert add(2, 3) == 5


def test_add_zero():
    assert add(0, 0) == 0


def test_multiply():
    assert multiply(3, 4) == 12
