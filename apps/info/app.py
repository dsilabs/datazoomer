
from zoom import App, system
    
app = App()
system.app.menu = [
    ('index','Overview','index'),
    ('system-log','System Log','system-log'),
    ('errors','Errors','errors'),
    ('top-users','Top Users','top-users'),
    ('addresses','Addresses','addresses'),
    ('tables','Tables','tables'),
    ('environment','Environment','environment'),
    ('python','Python','python')]
    
    
