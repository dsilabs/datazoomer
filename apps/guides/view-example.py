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
            css='.hello-link { color: red; }',
        )
        return page(content, title='Hello')

    def hello(self):
        return page('hello world!', title='Hello')

view = MyView()
