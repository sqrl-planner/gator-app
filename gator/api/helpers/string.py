"""String manipulation helpers."""


def chomp(x: str, suffix: str) -> str:
    """Remove the suffix from the end of the string.

    Args:
        x: The string to remove the suffix from.
        suffix: The suffix to remove.

    Returns:
        The string with the suffix removed.

    >>> chomp('ExampleSuffix', 'Suffix')
    'Example'
    >>> chomp('Nothing', 'Suffix')
    'Nothing'
    """
    if x.endswith(suffix):
        return x[:-len(suffix)]
    return x
