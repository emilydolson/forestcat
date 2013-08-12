def findNormVals(name):
    name = name.lower().split("_")
    if len(name) == 3 and name[2] == "avg":
        if name[0] == "ec":
            return (0, 8)
        if name[0] == "perm":
            return(1, 81)
        if name[0] == "vwc":
            return (.05, .5)
        if name[0] == "tsoil":
            return (-10, 70)

    elif len(name) == 3:
        if name[1] == "air" and name[2] == "temperature":
            return (-40, 60)
        if name[0] == "cr1000" and name[1] == "panel" and name[2] == "temp":
            return (-40, 60)

    elif len(name) >= 2 and name[0] == "weir" and name[1] == "lvl":
        return (0, 2)

    elif len(name) == 1:
        if name[0] == "cond" or name[0] == "ct":
            return (.005, 7)
        if name[0] == "precipitation":
            return (0, 1)

    elif len(name) == 2:
        if name[0] == "temp" and name[1] == "c":
            return (0, 50)
        if name[0] == "relative" and name[1] == "humidity":
            return (0, 100)
        if name[0] == "bucket" and name[1] == "depth":
            return (0, 16)
    
    return None

class rtSensorStream:
    def __init__(self, name):
        self.name = name
        self.range = findNormVals(name)
        self.currVal = None

    def store(self, val):
        self.currVal = (val-self.range[0])/(self.range[1]-self.range[0])

    def getOrigVal(self):
        return self.currVal*(self.range[1]-self.range[0]) + self.range[0]

    
        
        
