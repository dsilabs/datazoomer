"""
    zoom.forms

    A collection ready to use general purpose forms.
"""

import zoom
from zoom.fields import Form, Hidden, Button, MarkdownText


def delete_form(name):
    """produce a delete form"""
    return Form(
        MarkdownText('Are you sure you want to delete **%s**?' % name),
        Hidden(name='CONFIRM', value='NO'),
        Button(
            'Yes, I''m sure.  Please delete.',
            name='DELETE_BUTTON',
            cancel='/'+'/'.join(zoom.route[:-1])
        )
    ).edit()
