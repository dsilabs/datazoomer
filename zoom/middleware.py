"""
    middlware layers

    provies a set of functions that can be placed between the http server and
    the application layer.  these functions can provide various helper services
    such as content serving, caching, error trapping, security, etc..
"""

# pylint: disable=broad-except
# We sometimes catch anything that hasn't already been handled and provide a
# useful respose to the browser.  That's not usually advised but in this
# case it's what we want.

import os
import sys
import traceback
import json
from StringIO import StringIO

from .response import (
    PNGResponse, JPGResponse, CSSResponse, JavascriptResponse
)


SAMPLE_FORM = """<br><br>
<form action="" id="dz_form" name="dz_form" method="POST" enctype="multipart/form-data">
    first name<input name="first_name" value="" type="text">
    last name<input name="last_name" value="" type="text">
    picture<input name="photo" value="" type="file">
    <input style="" name="send_button" value="send" class="button" type="submit" id="send_button">
</form>
""".replace('/n', '<br>')


def debug(request):
    """fake app for development purposes"""

    def format_section(title, content):
        """format a section for debugging output"""
        return '<pre>\n====== %s ======\n%s\n</pre>' % (title, repr(content))

    def formatr(title, content):
        """format a section for debugging output in raw form"""
        return '<pre>\n====== %s ======\n%s\n</pre>' % (title, content)

    content = ''

    try:
        status = '200 OK'

        if request.module == 'wsgi':
            title = 'Hello from WSGI!'
        else:
            title = 'Hello from CGI!'

        content += title + '<br>\n'

        content += formatr('printed output', '{printed_output}')

        content += formatr('request', request)
        content += formatr('form', SAMPLE_FORM)
        content += formatr('paths', json.dumps(dict(
            path=[sys.path],
            directory=os.path.abspath('.'),
            pathname=__file__,
                ), indent=2))
        content += formatr('environment',
                           json.dumps(os.environ.items(), indent=2))

        print 'testing printed output'

        data = request.data
        if 'photo' in data and data['photo'].filename:
            content += format_section('filename', data['photo'].filename)
            content += format_section('filedata', data['photo'].value)

        headers = [('Content-type', 'text/html'),
                   ('Content-Length', str(len(content)))]

    except Exception:
        status = '200 OK'
        content = traceback.format_exc()
        headers = [('Content-type', 'text/plain'),
                   ('Content-Length', str(len(content)))]

    return status, headers, content


def app(request):
    """Call the main Application"""
    from zoom.startup import run_as_app
    response = run_as_app(request)
    doc = response.render_doc()
    headers = response.headers.items() + [('Content-length', '%s' % len(doc))]
    status = response.status
    return status, headers, doc


def capture_stdout(request, handler, *rest):
    """Capture printed output for debugging purposes"""
    real_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        status, headers, content = handler(request, *rest)
    finally:
        printed_output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = real_stdout
        content = content.replace('{printed_output}', printed_output)
    return status, headers, content


def serve_response(filename):
    """Serve up various respones with their correct response type"""
    known_types = dict(
            png=PNGResponse,
            jpg=JPGResponse,
            gif=PNGResponse,
            ico=PNGResponse,
            css=CSSResponse,
            js=JavascriptResponse,
            )
    if os.path.exists(filename):
        func = filename.lower()
        for file_type in known_types:
            if func.endswith('.' + file_type):
                data = open(filename).read()
                response = known_types[file_type](data)
                return response.render_wsgi()
        return '200 OK', [], 'unknown file type'
    else:
        return '200 OK', [], 'file not found: {}'.format(filename)


def serve_static(request, handler, *rest):
    """Serve a static file"""
    if request.path.startswith('/static/'):
        root_dir = request.instance
        filename = os.path.join(root_dir, 'www', request.path[1:])
        return serve_response(filename)
    else:
        return handler(request, *rest)


def serve_themes(request, handler, *rest):
    """Serve a theme file"""
    if request.path.startswith('/themes/'):
        root_dir = request.instance
        filename = os.path.join(root_dir, request.path[1:])
        return serve_response(filename)
    else:
        return handler(request, *rest)


def serve_images(request, handler, *rest):
    """Serve an image file"""
    if request.path.startswith('/images/'):
        filename = os.path.join(request.root, 'content', request.path[1:])
        return serve_response(filename)
    else:
        return handler(request, *rest)


def serve_favicon(request, handler, *rest):
    """Serve a favicon file"""
    if request.path == '/favicon.ico':
        root_dir = request.root
        filename = os.path.join(root_dir, 'static', 'images', request.path[1:])
        return serve_response(filename)
    else:
        return handler(request, *rest)


def serve_html(request, handler, *rest):
    """Direct a request for an HTML page to the content app"""
    if request.path.endswith('.html'):
        request.path = '/content' + request.path[:-5]
        request.route = request.path.split('/')[1:]
        return handler(request, *rest)
    else:
        return handler(request, *rest)


def trap_errors(request, handler, *rest):
    """Trap exceptions and raise a server error"""
    try:
        return handler(request, *rest)
    except Exception:
        status = '500 Internal Server Error'
        content = traceback.format_exc()
        headers = [('Content-type', 'text/plain'),
                   ('Content-Length', str(len(content)))]
        return status, headers, content


def _handle(request, handler, *rest):
    """invoke the next handler"""
    return handler(request, *rest)


def handle(request, handlers=None):
    """handle a request"""
    default_handlers = (
        trap_errors,
        serve_favicon,
        serve_static,
        serve_themes,
        serve_images,
        serve_html,
        #capture_stdout,
        #trap_errors,
        app,
    )
    return _handle(request, *(handlers or default_handlers))


DEBUGGING_HANDLERS = (
    trap_errors,
    serve_favicon,
    serve_static,
    serve_themes,
    serve_images,
    debug,
)
