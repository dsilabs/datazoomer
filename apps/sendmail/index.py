

from zoom import *
from zoom.mail import send, send_secure, RecipientKeyMissing, Attachment

mail_form = Form([
    TextField('Recipient',size=60,maxlength=60),
    TextField('Subject'),
    MemoField('Message'),
    FileField('Attachment'),
    CheckboxField('Encrypt'),
    ButtonField('Send'),
    ])

class MyView(View):

    def index(self):
        return page(content='Send mail as the system' + mail_form.edit(), title='Send Mail')

class MyController(Controller):

    def send_button(self, **input):

        if mail_form.validate(input):

            if 'ENCRYPT' in input:

                try:
                    send_secure( input['RECIPIENT'], input['SUBJECT'], input['MESSAGE'] )
                    message('encrypted message sent')
                    return home()

                except RecipientKeyMissing, e:
                    error('Missing pulic key for %s'%e.message)

            else:
                if 'ATTACHMENT' in input and hasattr(input['ATTACHMENT'], 'filename'):
                    send(
                        input['RECIPIENT'],
                        input['SUBJECT'],
                        input['MESSAGE'],
                        [Attachment(
                            input['ATTACHMENT'].filename,
                            input['ATTACHMENT'].file,
                        )],
                    )
                    message('message sent with attachment')
                else:
                    send(input['RECIPIENT'], input['SUBJECT'], input['MESSAGE'])
                    message('message sent')
                return home()

view = MyView()
controller = MyController()


