
import model, dzresponse

class View:
    def __call__(self,request):
        response = dzresponse.Response()
        response.headers['Content-type'] = 'image/png'
        response.content = model.current_user().photo #or open('no_photo.png','rb').read()
        return response
        
view = View()        
