
#
#   Routes in this application are not atypical.
#
#   /content - shows the index page
#   /content/index - shows the index page
#   /content/services - shows the services page
#   /content/services/index - shows the index page in the services section
#   /content/p - shows a list of pages
#   /content/p/services/edit - shows the services page in edit mode
#   /content/p/services/storage/archival/edit - shows the services/storage/archival page in edit mode
#   /content/p/services/delete - shows the services page in delete mode
#   /content/p/new - shows a new page form
#   /content/i - shows a list of images
#   /content/f - shows a list of files
#

from zoom import App, user

class MyApp(App):
    def authorized(self):
        return bool(user.is_manager)

app = MyApp()

