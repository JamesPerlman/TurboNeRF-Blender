
class NotificationCenter:

    def __init__(self):
        self.observers = {}
    
    @classmethod
    def default(cls):
        if not hasattr(cls, "_default"):
            cls._default = cls()
        
        return cls._default

    def add_observer(self, name, observer):
        if name not in self.observers:
            self.observers[name] = []
        
        self.observers[name].append(observer)
    
    def remove_observer(self, name, observer):
        if name not in self.observers:
            return
        
        self.observers[name].remove(observer)
    
    def notify(self, name, *args, **kwargs):
        if name not in self.observers:
            return
        
        for observer in self.observers[name]:
            observer(*args, **kwargs)
