# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Format and send mail using python"""

from smtplib import SMTP
from email import Encoders
from re import match, compile
from htmllib import HTMLParser
from cStringIO import StringIO
from mimetypes import guess_type
from email.Message import Message
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEImage import MIMEImage
from email.MIMEAudio import MIMEAudio
from email.MIMEMultipart import MIMEMultipart
from types import TupleType, ListType, StringType
from formatter import AbstractFormatter, DumbWriter
from email.Utils import COMMASPACE, formatdate, formataddr, quote
from fill import fill
from system import system
from tools import unisafe

class EmailEncryptionFail(Exception): pass
class SenderKeyMissing(Exception): pass
class RecipientKeyMissing(Exception): pass

VALID_EMAIL_RE = compile("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$")

email_body = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<BODY>
<table width="100%">
 <tr>
  <td align="left">
  <img src="{{logo_url}}" alt="banner logo"> 
  </td>
 </tr>
 <tr>
  <td align="left">
  <font face="helvetica,arial,freesans,clean,sans-serif" size="2">{{message}}</font>
  </td>
 </tr>
</table>
</BODY>
</HTML>
"""

class Message(object):
    def __init__(self):
        x=1

#Attachment


def format_email(body):
    logo_url = system.config.get('mail','logo',system.uri + '/images/email_logo.png')
    return fill('{{','}}',email_body,dict(logo_url=logo_url,message=body).get)
#    class Filler(object):
#        def __init__(self):
#            self.MESSAGE = body
#    result = fill(email_body.replace('<#ROOT>',system.root_url),Filler())
#    return result

def validate_email(email_address):
    """A regular expression check against a supplied email address to see
        if it appears valid.
    """
    return VALID_EMAIL_RE.match(email_address) != None

def display_email_address(email):
    """Return a formatted email address (eg: "User Name <username@somewhere.net>"),
       from a tuple (Display name, email address) or a list of tuples.  If the
       parameter is a string, it is returned.
    """
    if type(email)==TupleType: return formataddr(email)
    elif type(email)==ListType: return ';'.join(display_email_address(to) for to in email)
    return email

def email_address(email):
    """Return the email address from a (Display name, email address) tuple or list of
       tuples.
    """
    if type(email)==TupleType: return email[1]
    elif type(email)==ListType: return ';'.join(email_address(to) for to in email)
    return email

def get_plain_from_html(html):
    textout = StringIO()
    formtext = AbstractFormatter(DumbWriter(textout))
    parser = HTMLParser(formtext)
    parser.feed(html)
    parser.close()
    return textout.getvalue()

def SendPlainTextMail(fromaddr,toaddr,subject,body,attachments=[]):
    """Send a plain text email
    """
    SendMail(fromaddr,toaddr,subject,body,'plain',attachments)

def SendHTMLMail(fromaddr,toaddr,subject,body,attachments=[]):
    """Send an HTML email
    """
    SendMail(fromaddr,toaddr,subject,body,'html',attachments)

def SendMail(fromaddr,toaddr,subject,body,mailtype='plain',attachments=[]):
    """Send mail message.
       -fromaddr can be a string or tuple
       -toaddr can be a string, tuple or list
       -mailtype is of 'plain' or 'html'
    """
    smtp_host = system.config.get('mail','smtp_host')
    smtp_port = system.config.get('mail','smtp_port')
    smtp_user = system.config.get('mail','smtp_user')
    smtp_passwd = system.config.get('mail','smtp_passwd')
    gnupg_home = system.config.get('mail','gnupg_home','')
    from_addr = system.config.get('mail','from_addr')
    logo_url = system.config.get('mail','logo',system.uri + '/images/email_logo.png')

    toaddr = (type(toaddr) <> ListType and [toaddr] or toaddr)
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = display_email_address(fromaddr)
    message['To'] = display_email_address(toaddr)
    message.preamble = 'This message is in MIME format.  You will not see this in a MIME-aware mail reader.\n'
    message.epilogue = '' # To guarantee the message ends with a newline

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msg_alternative = MIMEMultipart('alternative')
    message.attach(msg_alternative)

    if isinstance(body,unicode):
        body = body.encode('utf8')
        
    # simple encoding test, we will leave as ascii if possible (readable)
    _char = 'us-ascii'
    try: body.decode('ascii')
    except: _char = 'utf8'

    # attach a plain text version of the html email
    if mailtype=='html':
        msg_alternative.attach(MIMEText(get_plain_from_html(body),'plain',_char))
        body = format_email(body)
    body = MIMEText(body,mailtype,_char)
    msg_alternative.attach( body )

    for attachment in attachments:
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = guess_type(attachment.filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text' or (ctype==None and attachment.filename[-4:].lower()=='.ini'):
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
            Encoders.encode_base64(msg)
        # Set the filename parameter
        msg.add_header('Content-Disposition', 'attachment', filename=attachment.filename)
        message.attach(msg)

    server  = SMTP(smtp_host,smtp_port)
    if smtp_user and smtp_passwd:
        server.login(smtp_user,smtp_passwd)
    server.sendmail(email_address(fromaddr), [email_address(to) for to in toaddr], message.as_string())
    server.quit()

class Attachment(object):
    def __init__(self,filename,filelike_object,mime_type=None):
        """Attachment object contains the information necessary to email an attachment.
            filelike_object just needs a read method.
        """
        self.filename = filename
        self.data = filelike_object
        self.mimetype = mime_type
        self.read = filelike_object.read


def send_as(fromaddr,recipients,subject,message,attachments=[]):
    if type(recipients) == StringType:
        if ';' in recipients:
            recipients = zip(recipients.split(';'),recipients.split(';'))
        else:
            recipients = (recipients,recipients)
    if type(recipients) != type([]):
        recipients = [recipients]
    return SendMail(fromaddr,recipients,subject,message,'html',attachments=attachments)

def send(recipients,subject,message,attachments=[]):
    site_name = system.config.get('site','name','DataZoomer')
    from_addr = system.config.get('mail','from_addr')
    return send_as((site_name,from_addr),recipients,subject,message,attachments)

def send_secure_as(sender, recipient, subject, message):
    import gnupg
    gnupg_home = system.config.get('mail','gnupg_home','')
    gpg = gnupg.GPG(gnupghome=gnupg_home)

    find_key = lambda x: [a for a in gpg.list_keys() if x in a['uids'][0]]

    if not find_key(recipient):
        raise RecipientKeyMissing(recipient)

    emessage = gpg.encrypt(message, recipient)
    if emessage:
        SendPlainTextMail(sender, recipient, subject, str(emessage))
    else:
        raise EmailEncryptionFail

def send_secure(recipient, subject, message):
    from_addr = system.config.get('mail','from_addr')
    send_secure_as(from_addr, recipient, subject, message)

if __name__ == '__main__':

    site_name = system.config.get('site','name','DataZoomer')
    site_owner = system.config.get('site','owner_name','Dynamic Solutions Inc.')
    owner_email = system.config.get('site','owner_email','noreply@dynamic-solutions.com')

    message = '<big><strong>Hi %s</strong></big><br><br>This is a test email from mail.py' % site_owner
    fromaddr = (site_name,from_addr)
    to = [('Testuser',owner_email),]
    send('info@dynamic-solutions.com','Testing send',message)
    
    

