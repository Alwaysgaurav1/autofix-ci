def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    # BUG: Off-by-one error added by regression
    return a + b + 1


def multiply(a: int, b: int) -> int:
    """Return the product of two integers."""
    return a * b
