#Adapted by Emily Dolson from code from the pyrobot pyrobot project, 
#originally modified for CS81 at Swarthmore College
#Spring 2012, by Lisa Meeden

from pyrobot.brain.conx import *
from random import random
from math import sqrt
from event import *

class Region:
    """
    The region class, adapted from the GNG region class used for CBIM,
    handles all state-specific features. Most notably, this includes the
    "expert" (neural net in this implementation) used for predicting
    sensor values on the next time step. However, it also keeps track of 
    running means and standard deviations for each sensor.
    """
    def __init__(self, inputVectorSize, targetVectorSize, errors, n):
        """
        In original IAC timeWindow was 15 and smoothing was 25.
        """
        self.inputVectorSize = inputVectorSize
        self.targetVectorSize = targetVectorSize
        self.errors = errors #stores prediction error on each step
        self.name = "R" + str(n) #region name
        self.timeWindow = 15 #Time window for error tracking 
        self.smoothing = 25 #smoothing for error tracking
        self.inputs = [] #list of input vectors
        self.targets = [] #list of  target vectors associated with inputs
        self.trace = []
        self.timeStep = 0 #keeps track of number of points in this state
        self.sensitivity = 3 #number of SDs out a point needs to be flagged
                            #as anomalous

        #Set up three layer, fully connected, feedforward neural net
        self.expert = Network()
        self.expert.addLayer("input", self.inputVectorSize)
        self.expert.addLayer("hidden", self.inputVectorSize)
        self.expert.addLayer("output", self.targetVectorSize)
        self.expert.connect("input", "hidden")
        self.expert.connect("hidden", "output")
        self.expert.resetEpoch = 1
        self.expert.resetLimit = 1
        self.expert.momentum = 0
        self.expert.epsilon = 0.5

        #Set up running means and standard deviations
        self.runningMeans = [0.0 for i in range(inputVectorSize)]
        self.runningSDs = [0.0 for i in range(inputVectorSize)]

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
        
        """
        for i in range(len(vec)):
            if abs(self.runningMeans[i] - vec[i]) > currSDs[i]*self.sensitivity:
                potErrs.append(i)
        
        if len(potErrs) < .5*len(vec):
            return vec, potErrs
        else:
            return vec, 1
        """
        return vec, None
            
    def inVecCuriosity(self, vec, prevVec):
        """
        Handles incoming vectors when curiosity module (which also handles
        error tolerance) is active. 
        Input: vec - the vector of sensor values for the current timestep
        prevVec - the vector of sensor values for previous time step (so that
        we can so what predictions they would have elicited)
        
        """
        self.timeStep += 1

        #Calculate prediction error
        prediction = self.askExpert([i.value for i in prevVec])
        predErr = 0
        errs = []

        for i in range(len(vec)):
            if math.isnan(vec[i].value):
                vec[i].value = prediction[i]
                errs.append(Error(vec[i].source+" "+vec[i].name, vec[i].time, vec[i].value, prediction[i], 
                       "missing or out of range data"))
            else:
                predErr += (prediction[i] - vec[i].value)**2

        print "Prediction Error:", predErr, prediction

        #Computer running means and standard deviations
        currSDs = []
        for i in range(len(vec)):
            if self.runningMeans[i] == 0:
                self.runningMeans[i] = vec[i].value
                currSDs.append(0)
            else:
                #Wellford's algorithm (running means)
                prevMean = self.runningMeans[i]
                self.runningMeans[i] += (vec[i].value-prevMean)/self.timeStep
                self.runningSDs[i] += (vec[i].value-prevMean)*(vec[i].value-self.runningMeans[i])
                currSDs.append(sqrt(self.runningSDs[i]/(self.timeStep - 1)))

        #Add this vector to the neural net's training set
        self.addExemplar(prevVec, vec) #A bit self-reinforcing, but what
        self.trainExpert() #can we do about it?
        
        potErrs = []
        for i in range(len(vec)):
            if abs(self.runningMeans[i] - vec[i].value) > currSDs[i]*self.sensitivity or vec[i].replaced:
                potErrs.append(Error(vec[i].source+" "+vec[i].name, vec[i].time, vec[i].value, vec[i].replaced, (vec[i].flag if vec[i].flag==None else "Abnormal value")))
            else:
                vec[i].sensor.errorState = False
        if len(potErrs) < .5*len(vec):
            return vec, potErrs
        else:
            return vec, None #"None" in place of potential errors indicates that
                     #this has been determined most likely to be a rare event

    def trainExpert(self):
        """
        Train the expert on most recent exemplar.
        """
        print self.targets[-1]
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
        """
        Make a graph of error over time
        """
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
