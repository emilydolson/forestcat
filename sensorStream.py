from math import isnan

class SensorStream():
    def __init__(self, data, times, label):
        self.stream = data
        self.times = times
        self.active = True
        time1 = times[0]
        time2 = times[1]
        time1 = float(time1.split()[1][3:5])
        time2 = float(time2.split()[1][3:5])
        self.freq = time2-time1
        self.label = label
        self.curr = 0
        self.minutesElapsed = 0
        self.normConst = max(data[:500])
        if isnan(self.normConst) or self.normConst == 0 or self.normConst < 0:
            self.normConst = 1

    def __str__(self):
        return self.label + ": " + ", ".join([str(i) for i in self.stream[:3]]) + "...   ..." + ", ".join([str(i) for i in self.stream[-3:]])

    def next(self, minutes):
        self.minutesElapsed += minutes
        while self.minutesElapsed > self.freq:
            self.minutesElapsed -= self.freq
            self.curr += 1
        return self.stream[self.curr]/self.normConst

    def isActive(self):
        return self.active

    def setActive(self):
        self.active = True

    def setInactive(self):
        self.active = False
