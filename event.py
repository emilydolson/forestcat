class Event():
    def __init__(self, prevState, newState, vector, time):
        self.prevState = prevState
        self.newState = newState
        self.vector = vector
        self.time = time
        
    def __str__(self):
        return str(self.prevState) + " -> " + str(self.newState) + ": " + str(self.time)

    def getTime(self):
        return self.time

    def getVector(self):
        return self.vector

class Error():
    def __init__(self, sensor, time, value, flag=None):
        self.sensor = sensor
        self.time = time
        self.value = value
        self.flag = flag
        
    def __str__(self):
        if self.flag != None:
            return "Potential error at " + str(self.time) + "in sensor" + str(self.sensor) + ": " + str(self.value) + " - Flagged because of " + self.flag
        else:
            return "Potential error at " + str(self.time) + "in sensor" + str(self.sensor) + ": " + str(self.value)

    def getTime(self):
        return self.time

    def getSensor(self):
        return self.sensor

    def __cmp__(self, other):
        if self.time < other.getTime():
            return -1
        elif self.time == other.getTime():
            return 0
        else:
            return 1

