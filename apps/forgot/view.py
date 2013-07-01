

class View:

    def __call__(self,*a,**k):
        if len(a) and hasattr(self,a[0]):
            """Collection View"""
            view_name = a[0]
            rest = a[1:]
            method = getattr(self,view_name)
            if callable(method):
                result = method(*rest,**k)
            else:
                result = method      
        elif len(a)==1:
            """Default item view"""
            result = self.show(a[0])
        elif len(a)>1 and hasattr(self,a[1]) and callable(getattr(self,a[1])):
            """Item view"""
            view_name = a[1]
            rest = a[2:]
            id = a[0]
            method = getattr(self,view_name)
            result = method(id,*rest,**k)
        elif len(a)==0:
            """Default collection view"""
            result = self.index(**k)
        else:
            """No view"""
            result = None            

        if result:
            return result

    def index(self):
        """GET a list of items"""
        pass

    def edit(self,id,**values):
        """GET a form to edit the item"""
        pass

    def show(self,id,**values):
        """GET a form to display the item"""
        pass

    def delete(self,id,confirm=1):
        """GET a form to confirm the deletion of the item"""
        pass

    def new(self,id):
        """GET a form to enter a new item"""
        pass


