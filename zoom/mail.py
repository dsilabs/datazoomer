"""
    format and send mail

    note: requires Python 2.5 or newer
"""

# pylint: disable=multiple-statements
# pylint: disable=too-many-arguments

import os
import re
import json
from smtplib import SMTP
from cStringIO import StringIO
from mimetypes import guess_type
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from types import TupleType, ListType, StringType
from formatter import AbstractFormatter, DumbWriter

from zoom.system import system
from zoom.store import Record, EntityStore


__all__ = (
    'send',
    'send_as',
    'send_secure',
    'send_secure_as',
    'deliver',
    'Attachment',
)


class EmailEncryptionFail(Exception):
    """gpg failure"""
    pass

class SenderKeyMissing(Exception):
    """gpg sender key mssing"""
    pass

class RecipientKeyMissing(Exception):
    """gpg recipient key mssing"""
    pass

class AttachmentDataException(Exception):
    """raised when asked to deliver data in background process"""
    pass

class SystemMail(Record):
    """system message"""
    pass


BODY_TPL = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<BODY>
<table width="100%">
 <tr>
  <td align="left">
  <img src="{logo_url}" alt="banner logo"> 
  </td>
 </tr>
 <tr>
  <td align="left">
  <font face="helvetica,arial,freesans,clean,sans-serif" size="2">{message}</font>
  </td>
 </tr>
</table>
</BODY>
</HTML>
"""

def get_mail_store():
    """returns the mail store"""
    return EntityStore(system.db, SystemMail)


def format_as_html(text):
    """wrap email text in a mail template"""
    logo_url = system.config.get(
        'mail',
        'logo',
        system.uri + '/images/email_logo.png'
    )
    return BODY_TPL.format(logo_url=logo_url, message=text)


def validate_email(email_address):
    """A regular expression check against a supplied email address to see
        if it appears valid.

        >>> validate_email('a')
        False
        >>> validate_email('a@b.c')
        False
        >>> validate_email('a@b.co')
        True
    """
    VALID_EMAIL_RE = re.compile(
        "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\."
        "([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$"
    )
    return VALID_EMAIL_RE.match(email_address) != None


def display_email_address(email):
    """Make a formatted address (eg: "User Name <username@somewhere.net>"),
       from a tuple (Display name, email address) or a list of tuples.
       If the parameter is a string, it is returned.

       >>> recipients = [('Joe','joe@smith.com'),'sally@smith.com']
       >>> display_email_address(recipients)
       'Joe <joe@smith.com>;sally@smith.com'

       >>> recipients = [['Joe','joe@smith.com'],'sally@smith.com']
       >>> display_email_address(recipients)
       'Joe <joe@smith.com>;sally@smith.com'

       >>> recipients = (('Joe','joe@smith.com'),'sally@smith.com')
       >>> display_email_address(recipients)
       'Joe <joe@smith.com>;sally@smith.com'
    """
    if type(email) in [ListType, TupleType]:
        result = []
        for item in email:
            if type(item) in [ListType, TupleType] and len(item) == 2:
                result.append(formataddr(item))
            else:
                result.append(item)
        return ';'.join(result)
    return email


def get_plain_from_html(html):
    """extract plain text from html

    >>> test_html = "<div><h1>Hey<h1><p>This is some text</p></div>"
    >>> get_plain_from_html(test_html)
    '\\nHey\\n\\nThis is some text'

    """
    from htmllib import HTMLParser # import here to avoid high startup cost

    textout = StringIO()
    formtext = AbstractFormatter(DumbWriter(textout))
    parser = HTMLParser(formtext)
    parser.feed(html)
    parser.close()
    return textout.getvalue()


def post(sender, recipients, subject, body, attachments=None, style='plain'):
    """post an email message for delivery"""

    dumps = json.dumps
    mail = SystemMail(
        sender=dumps(sender),
        recipients=dumps(recipients),
        subject=subject,
        body=body,
        attachments=dumps([a.as_tuple() for a in attachments or []]),
        style=style,
        status='waiting',
    )
    get_mail_store().put(mail)


def compose(sender, recipients, subject, body, attachments, style):
    """compose an email message"""

    email = MIMEMultipart()
    email['Subject'] = subject
    email['From'] = formataddr(sender)
    email['To'] = display_email_address(recipients)
    email.preamble = (
        'This message is in MIME format. '
        'You will not see this in a MIME-aware mail reader.\n'
    )
    email.epilogue = '' # To guarantee the message ends with a newline

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they
    # want to display.
    msg_alternative = MIMEMultipart('alternative')
    email.attach(msg_alternative)

    if isinstance(body, unicode):
        body = body.encode('utf8')

    # simple encoding test, we will leave as ascii if possible (readable)
    _char = 'us-ascii'
    try:
        body.encode('ascii')
    except UnicodeDecodeError:
        _char = 'utf8'

    # attach a plain text version of the html email
    if style == 'html':
        msg_alternative.attach(
            MIMEText(get_plain_from_html(body), 'plain', _char)
        )
        body = format_as_html(body)
    body = MIMEText(body, style, _char)
    msg_alternative.attach(body)

    for attachment in attachments or []:
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.

        ctype, encoding = guess_type(attachment.filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed),
            # so use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)

        if maintype == 'text' or (
            ctype == None and
            attachment.filename[-4:].lower() == '.ini'
        ):
            # Note: we should handle calculating the charset
            msg = MIMEText(attachment.read(), _subtype=subtype)
        elif maintype == 'image':
            msg = MIMEImage(attachment.read(), _subtype=subtype)
        elif maintype == 'audio':
            msg = MIMEAudio(attachment.read(), _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(attachment.read())
            # Encode the payload using Base64
            encoders.encode_base64(msg)

        # Set the filename parameter
        msg.add_header(
            'Content-Disposition',
            'attachment',
            filename=attachment.filename
        )
        email.attach(msg)

    return email.as_string()


def connect():
    """connect to the mail server"""
    get = system.config.get
    smtp_host = get('mail', 'smtp_host')
    smtp_port = get('mail', 'smtp_port')
    smtp_user = get('mail', 'smtp_user')
    smtp_passwd = get('mail', 'smtp_passwd')

    server = SMTP(smtp_host, smtp_port)
    if smtp_user and smtp_passwd:
        server.login(smtp_user, smtp_passwd)

    return server

def disconnect(server):
    """disconnect from the mail server"""
    server.quit()


def expedite(sender, recipients, subject, body, attachments=None,
             style='plain'):
    """deliver this email now"""
    email = compose(
        sender,
        recipients,
        subject,
        body,
        attachments or [],
        style,
    )

    try:
        sender_address = sender[1]
    except IndexError:
        sender_address = sender

    server = connect()
    try:
        server.sendmail(
            sender_address,
            [r[1] for r in recipients],
            email
        )
    finally:
        disconnect(server)


def deliver():
    """deliver mail"""
    # spylint: disable=too-many-locals

    count = 0
    server = connect()
    try:
        mail_store = get_mail_store()
        mails = mail_store.find(status='waiting')
        for mail in mails:

            sender = json.loads(mail.sender)
            recipients = json.loads(mail.recipients)
            attachments = [
                Attachment(name, data, mimetype)
                for name, data, mimetype
                in json.loads(mail.attachments) or []
            ]

            email = compose(
                sender,
                recipients,
                mail.subject,
                mail.body,
                attachments,
                mail.style,
            )

            try:
                sender_address = sender[1]
            except IndexError:
                sender_address = sender

            try:
                server.sendmail(
                    sender_address,
                    [r[1] for r in recipients],
                    email
                )
                mail.status = 'sent'
                count += 1
            except Exception:
                mail.status = 'error'
                raise
            finally:
                mail_store.put(mail)
    finally:
        disconnect(server)

    return count


class Attachment(object):
    """Email attachment

    provide either a pathname, or a filename and a pathname, or if sending
    directly a filename and a file-like object.

    """
    # pylint: disable=too-few-public-methods
    def __init__(self, pathname, data=None, mime_type=None):
        self.pathname = pathname
        self.data = data
        self.mimetype = mime_type
        self.filename = os.path.split(pathname)[1]

    def as_tuple(self):
        """partilars required for delivery"""
        if hasattr(self.data, 'read'):
            msg = 'Unable to deliver data directly, use physical file instead'
            raise AttachmentDataException(msg)
        return self.pathname, self.data, self.mimetype

    @property
    def read(self):
        """provides a reader for the data

        if the data is not open, it will be because the user provided only a
        pathanme so we open the file at the pathname and return it"""
        if not self.data:
            self.data = open(self.pathname)
        elif type(self.data) in [str, unicode]:
            self.data = open(self.data)
        return self.data.read


def send_as(sender, recipients, subject, message, attachments=None):
    """send an email as a specific sender"""

    if type(recipients) == StringType:
        if ';' in recipients:
            recipients = zip(recipients.split(';'), recipients.split(';'))
        else:
            recipients = (recipients, recipients)

    if type(recipients) != ListType:
        recipients = [recipients]

    if system.mail_delivery != 'background':
        expedite(sender, recipients, subject, message, attachments, 'html')
    else:
        post(sender, recipients, subject, message, attachments, 'html')


def send(recipients, subject, message, attachments=None):
    """send an email"""
    site_name = system.config.get('site', 'name', 'DataZoomer')
    from_addr = system.config.get('mail', 'from_addr')
    sender = (site_name, from_addr)
    send_as(sender, recipients, subject, message, attachments)


def send_secure_as(sender, recipient, subject, message):
    """send a secure email as a specific sender"""
    import gnupg # importing here because in reality gnupg is rarely required

    gnupg_home = system.config.get('mail', 'gnupg_home', '')
    gpg = gnupg.GPG(gnupghome=gnupg_home)

    find_key = lambda x: [a for a in gpg.list_keys() if x in a['uids'][0]]

    if not find_key(recipient):
        raise RecipientKeyMissing(recipient)

    emessage = gpg.encrypt(message, recipient)
    if emessage:
        post(sender, recipient, subject, str(emessage), None, 'plain')
    else:
        raise EmailEncryptionFail


def send_secure(recipient, subject, message):
    """send a secure email"""
    from_addr = system.config.get('mail', 'from_addr')
    send_secure_as(from_addr, recipient, subject, message)



if __name__ == '__main__':
    #
    #running this script will send a test email to the site owner as
    #specified in the config file"""
    #
    # pylint: disable=invalid-name
    from StringIO import StringIO
    text_blob = StringIO('this is some text')

    recipient_name = system.config.get(
        'site',
        'owner_name',
        'Recipient'
    )
    recipient_address = system.config.get(
        'site',
        'owner_email',
    )
    tpl = """
        <big><strong>Hi %s</strong></big>
        <br><br>This is a test email from DataZoomer.
    """
    send(
        (recipient_name, recipient_address),
        'Testing send without attachments',
        tpl % recipient_name,
    )

    send(
        (recipient_name, recipient_address),
        'Testing send with an attachment',
        tpl % recipient_name,
        [Attachment('myfile.txt', text_blob)]
    )
