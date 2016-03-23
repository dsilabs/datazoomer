
from zoom import *
from zoom.flags import *

flag_form = Form(
    TextField('Label', required),
    TextField('URL', required, size=60, maxlength=240, hint='max 240 chars'),
    PulldownField('Icon', required, default='star', options=['mail','star','heart']),
    Hidden(name='OWNER', value=user.username),
    Buttons(['Save'],cancel='cancel'),
    )


