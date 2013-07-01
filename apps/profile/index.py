
from zoom.response import PNGResponse
from model import *

password_snippet = '<a class="action" href="/profile/change-password">Change Password</a>'

class ProfileController(Controller):
    
    def update_profile_button(self,**values):
        user = current_user()
        user.update(values)
        errors = user.validate()
        if errors:
            error(*errors)
        else:
            user.put()            
            message('Profile updated')

    def change_password_button(self):

        if password_fields.validate(data):
            user = current_user()

            if not user.authentic(data['OLD_PASSWORD']):
                warning('incorrect password')

            elif data['NEW_PASSWORD'] <> data['CONFIRM']:
                warning('passwords do not match')

            else:
                user.set_password(data['NEW_PASSWORD'])
                message('password changed')
                return to_page()

    def upload_button(self,*a,**k):
        input = webvars.__dict__
        if not 'uploaded_photo' in input:
            message('File missing')
        else:
            name = input.get('uploaded_photo').filename
            data = input.get('uploaded_photo').value
            user = current_user()
            if user.update_photo(name,data):
                return redirect_to('/profile')
            else:
                warning('unknown image type')

class ProfileView(View):

    def avatar(self):
        photo = current_user().photo or open('no_photo.png','rb').read() 
        return PNGResponse(photo)

    def change_photo(self):
        return Page('change_photo',dict(photo=self.photo()).get)

    def photo(self):
        #return 'photo goes here'
        css = '"border: 1px solid #bbbbbb; padding: 3px; background-color: width:100px; height:100px; #white; width=100px;"'
        return "<img style=%s src='%s'>" % (css,url_for('avatar'))

    def index(self):
        user = current_user()
        main_form.update(**user.__dict__)
        filler = { 
            'fields': main_form.edit(),
            'photo':self.photo(),
            'password_option': system.authentication == 'windows' and ' ' or password_snippet,
             }
        return Page('index',filler.get)

    def change_password(self):
        if system.authentication == 'windows':
            return redirect_to(url_for('/profile'))
        filler = { 'password_fields': password_fields.edit() }
        return Page('change_password',filler.get)

    
filler = {
    'fields':main_form.edit(),
    'photo':''
    }.get

view = ProfileView()    
controller = ProfileController()




