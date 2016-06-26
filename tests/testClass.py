

def props(cls):
    keys = [i for i in cls.__dict__.keys() if i[:1] != '_' and not hasattr(cls.__dict__[i],"__call__")]
    props = []
    for k in keys:
        props.append((k, cls.__dict__[k]))
    return props

    
class Entity():
    def printBonjour(self):
        print "Bonjour"
        
    def printClassAttr(self):
        for attr in props(self.__class__):
            print "Attribute: %s = %s\n" % (attr[0],attr[1])
        

class subEntity(Entity):
    first = ""
    last = ""
    
    def __init__(self, first, last):
        self.setFirst(first)
        self.setLast(last)
    
    def setFirst(self, first):
        subEntity.first = first
        print "First = %s" % first
        
    def setLast(self, last):
        subEntity.last = last
        print "Last = %s" % last