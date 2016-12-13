"""
    zoom.vis.utils

    utilities specific to the vis library
"""


def merge_options(old, updates):
    """Merges two sets of options

    >>> from pprint import pprint
    >>> options1 = {
    ...     'setting_one': 10,
    ...     'setting_two': 20,
    ...     'setting_three': {
    ...         'setting_four': 'test',
    ...         'setting_five': [1, 2, 3],
    ...     },
    ...     'setting_six': 30,
    ... }
    >>> options2 = {
    ...     'setting_one': 30,
    ...     'setting_three': {
    ...         'setting_five': [1,2],
    ...     },
    ... }
    >>> pprint(merge_options(options1, options2))
    {'setting_one': 30,
     'setting_six': 30,
     'setting_three': {'setting_five': [1, 2], 'setting_four': 'test'},
     'setting_two': 20}

    >>> pprint(merge_options(options1, None))
    {'setting_one': 10,
     'setting_six': 30,
     'setting_three': {'setting_five': [1, 2, 3], 'setting_four': 'test'},
     'setting_two': 20}


    """
    if updates is None:
        return old

    elif hasattr(old, 'keys') and hasattr(updates, 'keys'):
        new = {}
        for k in old:
            new[k] = old[k]
        for k in updates:
            if k in new:
                new[k] = merge_options(new[k], updates[k])
            else:
                new[k] = updates[k]
        return new

    else:
        return updates
