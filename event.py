class Event():
    def __init__(self, prevState, newState, vector, time, reason="None"):
        self.prevState = prevState
        self.newState = newState
        self.vector = vector
        self.time = time
        self.reason = reason

    def __str__(self):
        return str(self.prevState) + ", " + str(self.newState) + ", " + str(self.vector + ", " + str(self.time) + ", " + self.reason + "\n"

    def getTime(self):
        return self.time

    def getReason(self):
        return self.reason

    def getVector(self):
        return self.vector

    def equalTo(self, e):
        return self.time == e.getTime() and self.vector == e.getVector()

    def __cmp__(self, other):
        if self.time < other.getTime():
            return -1
        elif self.time == other.getTime():
            return 0
        else:
            return 1

    def __hash__(self):
        return hash(self.time)

class Error():
    def __init__(self, sensor, time, value, replaced = None, flag=None):
        self.sensor = sensor
        self.time = time
        self.value = value
        self.flag = flag
        self.replaced = replaced
        
    def __str__(self):
        if self.flag != None:
            return "Potential error at " + str(self.time) + "in sensor" + str(self.sensor) + ": " + str(self.value) + " - Flagged because of " + self.flag
        else:
            return "Potential error at " + str(self.time) + "in sensor" + str(self.sensor) + ": " + str(self.value)

    def getTime(self):
        return self.time

    def getValue(self):
        return self.value

    def getSensor(self):
        return self.sensor

    def equalTo(self, e):
        return self.time == e.getTime() and self.value == e.getValue()

    def __cmp__(self, other):
        if self.time < other.getTime():
            return -1
        elif self.time == other.getTime():
            return 0
        else:
            return 1

    def __hash__(self):
        return hash((self.time, self.sensor))
