

import zoom


class DirectionsForm(zoom.mvc.DynamicView):

    pass


class AppointmentForm(zoom.mvc.DynamicView):

    pass


fields = zoom.Fields(
    zoom.TextField('Name', placeholder='Your name'),
    zoom.TextField('Email', value='myemail@test.co'),
    zoom.TextField('Phone'),
    zoom.MemoField('Notes', value='notes go here'),
)


class MyView(zoom.mvc.View):

    def index(self):
        title = 'Forms'
        content = zoom.component(
            DirectionsForm(name='Joe'),
            AppointmentForm(fields=fields),
        )

        return zoom.page(str(content), title=title)


class MyController(zoom.mvc.Controller):

    def request_button(self, *args, **kwargs):
        message = (
            'Your Appointment is Booked!<br><br>'
            'Here''s what we received:<br><br>'
        )
        data = zoom.html.ul('{}: {}'.format(*i) for i in kwargs.items())
        content = message + data
        return zoom.page(content, title='Booked!')


view = MyView()
controller = MyController()
