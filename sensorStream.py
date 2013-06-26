from math import isnan, sqrt
from datetime import *
from event import *

class SensorStream():
    def __init__(self, data, times, label):
        self.stream = data
        self.times = times
        self.active = True
        time1 = times[0]
        time2 = times[1]
        self.freq = time2-time1
        self.label = label
        self.curr = 0
        self.minutesElapsed = times[0]
        self.normConst = max(data[:500])
        if isnan(self.normConst) or self.normConst == 0 or self.normConst < 0:
            self.normConst = 1

    def __str__(self):
        return self.label + ": " + ", ".join([str(i) for i in self.stream[:3]]) + "...   ..." + ", ".join([str(i) for i in self.stream[-3:]])

    def next(self, mins):
        self.minutesElapsed += timedelta(minutes=mins)
        while self.minutesElapsed > self.times[self.curr+1]:
            self.curr += 1
        return self.stream[self.curr]/self.normConst

    def isActive(self):
        return self.active

    def setActive(self):
        self.active = True

    def setInactive(self):
        self.active = False
    
    def getStream(self):
        return self.stream

    def getLabel(self):
        return self.label

    def getTime(self, i):
        return self.times[i]

    def getCurrTime(self):
        return self.times[self.curr]

    def scanForErrors(self):
        errors = []

        persistLengths = []
        persistEnds = []

        persistVal = -1
        persistLength = 0

        slopes = []

        for i in range(len(self.stream)):
            if isnan(self.stream[i]):
                errors.append(Error(self.label, self.times[i], self.stream[i], "Invalid Number"))
                persistVal = -1
                persistLength = 0
                continue
            
            if i > 0:
                slopes.append(self.stream[i] - self.stream[i-1])

            if self.stream[i] == persistVal:
                persistLength += 1
            else:
                persistLengths.append(persistLength)
                persistEnds.append(i)
                persistVal = float(self.stream[i])
                persistLength = 0

        meanLen = sum(persistLengths)/float(len(persistLengths))
        sdLen = sqrt(sum([(i - meanLen)**2 for i in persistLengths])/float(len(persistLengths)))
        for i in range(len(persistLengths)):
            if abs((persistLengths[i]-meanLen)/(sdLen+.00001)) > 3:
                val = self.stream[persistLengths[i]-1]
                for j in range(persistEnds[i]-1, 0, -1):
                    if self.stream[j] != val:
                        break
                    errors.append(Error(self.label, self.times[j], self.stream[j], "Persistence"))
                    
        slopeMean = float(sum(slopes))/len(slopes)
        slopeSD = sqrt(sum([(i-slopeMean)**2 for i in slopes])/float(len(slopes)))
        for i in range(len(slopes)):
            if (float(slopes[i])-slopeMean)/(slopeSD+.001) > 5:
                errors.append(Error(self.label, self.times[i+1], self.stream[i+1], "Rapid change in slope"))

        print sdLen, meanLen
        print slopeSD, slopeMean
        return errors

    #def insertDriftError(self, range):
        

        

            
            
