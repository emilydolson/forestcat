#Based on code from pyrobot, modified for CS81 at Swarthmore College
#Spring 2012, by Lisa Meeden

from pyrobot.brain.conx import *
from random import random
from math import sqrt
from event import *

class Region:
    def __init__(self, inputVectorSize, targetVectorSize, errors, n, timeWindow):
        """
        In original IAC timeWindow was 15 and smoothing was 25.
        """
        self.inputVectorSize = inputVectorSize
        self.targetVectorSize = targetVectorSize
        self.errors = errors
        self.name = "R" + str(n)
        self.timeWindow = timeWindow
        self.smoothing = 15
        self.inputs = []
        self.targets = []
        self.trace = []
        self.expert = Network()
        self.expert.addLayer("input", self.inputVectorSize)
        self.expert.addLayer("output", self.targetVectorSize)
        self.expert.connect("input", "output")
        self.expert.resetEpoch = 1
        self.expert.resetLimit = 1
        self.expert.momentum = 0
        self.expert.epsilon = 0.5
        self.runningMeans = [0.0 for i in range(inputVectorSize)]
        self.runningSDs = [0.0 for i in range(inputVectorSize)]
        self.timeStep = 0
        self.sensitivity = 3 #number of SDs out a point needs to be to be error

    def inVec(self, vec):
        self.timeStep += 1
        currSDs = []
        for i in range(len(vec)):
            if self.runningMeans[i] == 0:
                self.runningMeans[i] = vec[i]
                currSDs.append(0)
            else:
                #Wellford's algorithm
                prevMean = self.runningMeans[i]
                self.runningMeans[i] += (vec[i]-prevMean)/self.timeStep
                self.runningSDs[i] += (vec[i]-prevMean)*(vec[i]-self.runningMeans[i])
                currSDs.append(sqrt(self.runningSDs[i]/(self.timeStep - 1)))

        potErrs = []
        for i in range(len(vec)):
            if abs(self.runningMeans[i] - vec[i]) > currSDs[i]*self.sensitivity:
                potErrs.append(i)
        
        if len(potErrs) < .5*len(vec):
            return potErrs
        else:
            return 1
            
    def inVecCuriosity(self, vec):
        self.timeStep += 1
        currSDs = []
        for i in range(len(vec)):
            if self.runningMeans[i] == 0:
                self.runningMeans[i] = vec[i]
                currSDs.append(0)
            else:
                #Wellford's algorithm
                prevMean = self.runningMeans[i]
                self.runningMeans[i] += (vec[i]-prevMean)/self.timeStep
                self.runningSDs[i] += (vec[i]-prevMean)*(vec[i]-self.runningMeans[i])
                currSDs.append(sqrt(self.runningSDs[i]/(self.timeStep - 1)))
        
        self.addExemplar(vec)
        
            

    def trainExpert(self):
        """
        Train the expert most recent exemplar.
        """
        self.expert.step(input = self.inputs[-1], output = self.targets[-1])
    def trainExpertOnAll(self):
        """
        Train the expert on all exemplars.
        """
        self.expert.setInputs(self.inputs)
        self.expert.setOutputs(self.targets)
        self.expert.train()
    def askExpert(self, input):
        """
        Find out what the expert predicts for the given input.
        """
        self.expert['input'].copyActivations(input)
        self.expert.propagate()
        return self.expert['output'].activation
    def storeError(self, error, step):
        """
        Errors are stored with the most recent at the head of the list.
        """
        self.errors.insert(0, error)
        n = self.timeWindow + self.smoothing
        if len(self.errors) > n:
            self.trace.append((step, sum(self.errors[:n])/float(n)))
    def makeErrorGraph(self):
        if len(self.trace) == 0:
            return
        fp = open(self.name + ".err", "w")
        for step, err in self.trace:
            fp.write("%d %.6f\n" % (step, err))
            fp.flush()
        fp.close()
    def learningProgress(self):
        """
        Returns the learning progress which is an approximation of
        the first derivative of the error.
        """
        if len(self.errors) < (self.timeWindow + self.smoothing + 1):
            return 0
        decrease = self.meanErrorRate(0) - self.meanErrorRate(self.timeWindow)
        return  -1 * decrease
    def meanErrorRate(self, start):
        """
        Returns the average error rate over self.smoothing steps
        starting from the given start index.
        """
        result = 0
        end = start + self.smoothing + 1
        if end > len(self.errors):
            return 0
        for i in range(start, end, 1):
            result += self.errors[i]
        return result / float(self.smoothing + 1)
    def addExemplar(self, input, target):
        """
        Adds the given input and target to the appropriate lists.
        """
        self.inputs.append(input)
        self.targets.append(target)
    def exemplarsToStr(self):
        if len(self.inputs) < 5:
            return ""
        result = ""
        for i in range(1,5):
            result += "Input: "
            for inVal in self.inputs[-i]:
                result += "%.3f " % inVal
            result += "\n"
            result += "Target: "
            for tarVal in self.targets[-i]:
                result += "%.3f " % tarVal
            result += "\n"
        return result
