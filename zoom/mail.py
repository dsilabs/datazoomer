"""
    format and send mail

    note: requires Python 2.5 or newer
"""

# pylint: disable=multiple-statements
# pylint: disable=too-many-arguments

import re
from smtplib import SMTP
from htmllib import HTMLParser
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


__all__ = (
    'send',
    'send_as',
    'send_secure',
    'send_secure_as',
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


VALID_EMAIL_RE = re.compile(
    "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\."
    "([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$"
)

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


def format_email(body):
    """wrap email body in a mail template"""
    logo_url = system.config.get(
        'mail',
        'logo',
        system.uri + '/images/email_logo.png'
    )
    return BODY_TPL.format(logo_url=logo_url, message=body)


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
    return VALID_EMAIL_RE.match(email_address) != None


def display_email_address(email):
    """Make a formatted address (eg: "User Name <username@somewhere.net>"),
       from a tuple (Display name, email address) or a list of tuples.
       If the parameter is a string, it is returned.
    """
    if type(email) == TupleType:
        return formataddr(email)
    elif type(email) == ListType:
        return ';'.join(display_email_address(to) for to in email)
    return email


def get_email_address(email):
    """Make an address from a (Display name, email address) tuple or
    list of tuples.

       >>> get_email_address(('Joe Smith', 'joe@smith.com'))
       'joe@smith.com'
       >>> get_email_address([('Joe Smith', 'joe@smith.com'), \\
       ... 'sally@smith.com'])
       'joe@smith.com;sally@smith.com'
       >>> get_email_address('joe@smith.com')
       'joe@smith.com'
       >>> get_email_address('joe@smith.com')
       'joe@smith.com'
    """
    if type(email) == TupleType:
        return email[1]
    elif type(email) == ListType:
        return ';'.join(get_email_address(to) for to in email)
    return email


def get_plain_from_html(html):
    """extract plain text from html

    >>> test_html = "<div><h1>Hey<h1><p>This is some text</p></div>"
    >>> get_plain_from_html(test_html)
    '\\nHey\\n\\nThis is some text'

    """
    textout = StringIO()
    formtext = AbstractFormatter(DumbWriter(textout))
    parser = HTMLParser(formtext)
    parser.feed(html)
    parser.close()
    return textout.getvalue()


def post(
    fromaddr,
    toaddr,
    subject,
    body,
    mailtype='plain',
    attachments=None,
):
    """post an email for delivery

       - fromaddr can be a string or tuple
       - toaddr can be a string, tuple or list
       - mailtype is of 'plain' or 'html'
    """
    # pylint: disable=too-many-locals

    get = system.config.get
    smtp_host = get('mail', 'smtp_host')
    smtp_port = get('mail', 'smtp_port')
    smtp_user = get('mail', 'smtp_user')
    smtp_passwd = get('mail', 'smtp_passwd')

    toaddr = (type(toaddr) != ListType and [toaddr] or toaddr)

    email = MIMEMultipart()
    email['Subject'] = subject
    email['From'] = display_email_address(fromaddr)
    email['To'] = display_email_address(toaddr)
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
        body.decode('ascii')
    except:
        _char = 'utf8'

    # attach a plain text version of the html email
    if mailtype == 'html':
        msg_alternative.attach(
            MIMEText(get_plain_from_html(body), 'plain', _char)
        )
        body = format_email(body)
    body = MIMEText(body, mailtype, _char)
    msg_alternative.attach(body)

    for attachment in attachments or []:
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = guess_type(attachment.filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
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

    server = SMTP(smtp_host, smtp_port)
    if smtp_user and smtp_passwd:
        server.login(smtp_user, smtp_passwd)
    server.sendmail(
        get_email_address(fromaddr),
        [get_email_address(to) for to in toaddr],
        email.as_string()
    )
    server.quit()


class Attachment(object):
    """Contains the information necessary to email an attachment.

    note: filelike_object just needs a read method.

    """
    # pylint: disable=too-few-public-methods
    def __init__(self, filename, filelike_object=None, mime_type=None):
        self.filename = filename
        self.data = self.file = filelike_object
        self.mimetype = mime_type

    @property
    def read(self):
        """reads the attachment content"""
        if not self.file:
            self.data = self.file = open(self.filename)
        return self.file.read


def send_as(fromaddr, recipients, subject, body, attachments=None):
    """send an email as a specific sender"""
    if type(recipients) == StringType:
        if ';' in recipients:
            recipients = zip(recipients.split(';'), recipients.split(';'))
        else:
            recipients = (recipients, recipients)
    if type(recipients) != type([]):
        recipients = [recipients]
    return post(fromaddr, recipients, subject, body, 'html', attachments)


def send(recipients, subject, body, attachments=None):
    """send an email"""
    site_name = system.config.get('site', 'name', 'DataZoomer')
    from_addr = system.config.get('mail', 'from_addr')
    return send_as(
        (site_name, from_addr),
        recipients,
        subject,
        body,
        attachments
    )


def send_secure_as(sender, recipient, subject, body):
    """send a secure email as a specific sender"""
    import gnupg # importing here because in reality gnupg is rarely required

    gnupg_home = system.config.get('mail', 'gnupg_home', '')
    gpg = gnupg.GPG(gnupghome=gnupg_home)

    find_key = lambda x: [a for a in gpg.list_keys() if x in a['uids'][0]]

    if not find_key(recipient):
        raise RecipientKeyMissing(recipient)

    ebody = gpg.encrypt(body, recipient)
    if ebody:
        post(sender, recipient, subject, 'plain', str(ebody))
    else:
        raise EmailEncryptionFail


def send_secure(recipient, subject, body):
    """send a secure email"""
    from_addr = system.config.get('mail', 'from_addr')
    send_secure_as(from_addr, recipient, subject, body)


if __name__ == '__main__':
    #
    #running this script will send a test email to the site owner as
    #specified in the config file"""
    #
    # pylint: disable=invalid-name

    recipient_name = system.config.get(
        'site',
        'owner_name',
        'Recipient'
    )
    recipient_address = system.config.get(
        'site',
        'owner_email',
    )
    body = """
    <big><strong>Hi %s</strong></big>
    <br><br>This is a test email from DataZoomer.
    """ % recipient_name
    send(
        (recipient_name, recipient_address),
        'Testing send with attachment',
        body,
    )

