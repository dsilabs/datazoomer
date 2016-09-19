
Introduction
====

Views are what determines how a your app appears to the world.

After reading this guide, you will know:

* what a View is
* what a Helper is
* how to create custom helpers

-- section break --

[TOC]

-- section break --

What are Views?
====
In DataZoomer, web requests are handled by [[Controllers]] and [[Views]].
Typically, Controllers are concerned with any requests that alter the state of
the app and the view is concerned with how the app looks.

Views produce content which is typically included in an HTML page response.
They assemble this content from a variety of sources including objects or files
and they supply this content to the browser in a variety of forms including
HTML, css, javascript and others.

Content is supplied either as HTML in a text string or if the content is made
up of several parts such as HTML, CSS and JavaScript, it can be supplied using
a <code>component</code> which works with a wide variety of content types.


    """
        view-example.py
    """
    from zoom import page
    from zoom.component import component
    from zoom.mvc import View
    
    class MyView(View):
    
        def index(self):
            """produce the index page for the app"""
            content = component(
                '<a class="hello-link" href="view-example/hello">Say Hello!</a>',
                css='.hello-link {{ color: red; }}',
            )
            return page(content, title='Hello')
    
        def hello(self):
            return page('hello world!', title='Hello')
    
    view = MyView()


View methods correspond to the URL passed in so with 'index' being the default, so in this example, if the app is called 'guides' and the section of the app we're working was called 'view-example', then the url <a href="/guides/view-example">/guides/view-example</a> would call the index method of the view.



Helpers
====
When working with HTML it is often convenient to be able to insert bits of HTML
from other places such as objects or the system itself.  

To make this process easier and avoid duplicating commonly used code DataZoomer
provides a wide variety of helpers that provide content for dates, numbers,
user information, etc..  It's also easy to add helpers to your application as
it evolves so you can make your code even more <a href="https://en.wikipedia.org/wiki/Don%27t_repeat_yourself">DRY</a>.

