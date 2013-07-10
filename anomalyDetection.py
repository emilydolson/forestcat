#!/usr/bin/python
from scipy import *
from numpy import *
from sensorStream import *
from statsLib import *
from evalFunctionsLib import *
import matplotlib.pyplot as plt
from math import sqrt, isnan
from ravq import *
from event import *
from pickle import *
from datetime import *
import os, sys
from optparse import OptionParser

def readin(files):
    """
    Mostly just a bunch of nasty string parsing to get
    incoming data arranged into streams, despite the potential
    for these streams to be of different lengths.
    Inputs: files - a list of file names containing data
    Returns: A list of lists denoting sensor streams.
    """
    openFiles = []
    data = []
    sensorStreams = []
    lineLen = 0
    labels = []

    for i in range(len(files)):
        openFiles.append(open(files[i], "r"))
        firstline = openFiles[i].readline()
        firstline = firstline.split(",")
        data.append([])
        for item in firstline:
            labels.append(item.strip(" \"\n\r"))
            sensorStreams.append([])
        
        for line in openFiles[i]:
            line = line.split(",")
            line = [j.strip(",.\n\r \"") for j in line]
            for j in range(len(line)):
                try:
                    line[j] = float(line[j])
                except:
                    if j != 0:
                        line[j] = float("nan")
                        
            data[i].append(line)
    
    print labels
    offset = 0
    realSensorStreams=[]
    for i in range(len(data)):
        times = []
        for j in range(len(data[i])):
            for k in range(1, len(data[i][j])):
                try:
                    sensorStreams[k+offset].append(data[i][j][k])
                except:
                    print len(sensorStreams), k, offset
            times.append(convertDateTime(data[i][j][0]))
        for j in range(1+offset, len(data[i][j])+offset):
            realSensorStreams.append(SensorStream(sensorStreams[j], times, labels[j]))
        offset += len(data[i][0])
    
    return realSensorStreams

def convertDateTime(datestring):
    """
    Takes in a string representing the date and time in
    Hubbard Brook format and return a datetime object
    """
    try: #convert matlab format dates
        datestring=float(datestring)
        return datetime.fromordinal(int(datestring)) + timedelta(days=datestring%1) - timedelta(days = 366)
    except: #convert year-month-day format dates
        year = int(datestring[:4])
        month = int(datestring[5:7])
        date = int(datestring[8:10])
        hour = int(datestring[11:13])
        minute = int(datestring[14:16])
        seconds = int(datestring[17:19])

        return datetime(year, month, date, hour, minute, seconds)

def getVec(sensorStreams,  minutes):
    vec = []
    for stream in sensorStreams:
        if not stream.isActive():
            continue
        vec.append(stream.next(minutes))

    return vec

def euclidDist(x, y):
    dist = 0
    for i in range(len(x)):
        if not isnan(x[i]) and not isnan(y[i]):
            dist += (x[i]-y[i])**2
    return sqrt(dist)

def interp(vectors, reductionFactor):
    newVecs = []
    for i in range(1, len(vectors), reductionFactor):
        for j in range(reductionFactor):
            newVec = []
            for k in range(len(vectors[i])):
                newVec.append((vectors[i][k] - vectors[i-reductionFactor][k])*j/reductionFactor + vectors[i-reductionFactor][k])
            newVecs.append(newVec)
    return newVecs

def checkpoint(r, states, sensorStreams, errors, events, checkid=""):
    if checkid == "":
        checkid = "checkpoint"
    try:
        os.mkdir("results/"+str(checkid)) 
    except:
        pass
    saveToFile("results/"+str(checkid)+"/storedRavq", r)
    saveToFile("results/"+str(checkid)+"/storedStates", states)
    saveToFile("results/"+str(checkid)+"/storedSensorStreams", sensorStreams)
    saveToFile("results/"+str(checkid)+"/errors", errors)
    saveToFile("results/"+str(checkid)+"/events", events)

def resumeFromCheckpoint(timeInt, checkid="", bufferSize=100, epsilon=1, delta=.9, historySize=2, learningRate=.2):
    if checkid == "":
        checkid = "checkpoint"
    r = loadfromfile(str(checkid)+"/storedRavq")
    states = loadFromFile(str(checkid)+"/storedStates")
    sensorStreams = loadFromFile(str(checkid)+"/storedSensorStreams")
    errors = loadFromFile(str(checkid)+"/errors")
    events = loadFromFile(str(checkid)+"/events")
    return runRAVQ(sensorStreams, timeInt, bufferSize, epsilon, delta, historySize, learningRate, checkid, r, states, errors, events)

def compareVecs(interpVecs, realVecs):
    sumDist = 0
    print len(interpVecs), len(realVecs)
    for i in range(min(len(interpVecs), len(realVecs))):
        sumDist += euclidDist(interpVecs[i], realVecs[i])
    return sumDist

def runRAVQ(sensorStreams, timeInt, bufferSize=100, epsilon=1, delta=.9, historySize=2, learningRate=.2, checkid="", r=None, states=[], errors=[], events=[]):
    if r == None:
        r = ARAVQ(bufferSize, epsilon, delta, historySize, learningRate, timeInt)

    #observedTransitions = {}

    for i in range(len(sensorStreams[0].getStream())):
        if i%1000 == 0:
            checkpoint(r, states, sensorStreams, errors, events, checkid)
            print "Checkpoint saved at " + str(sensorStreams[0].getCurrTime())
        vec = getVec(sensorStreams, timeInt)
    	errs = r.input(vec)[2]
        if errs != 1 and errs != []:
            errors += [Error(sensorStreams[i].label, sensorStreams[i].getCurrTime(), vec[i]) for i in errs]
    	states.append(r.newWinnerIndex)
        if r.newWinnerIndex != r.previousWinnerIndex:
            #if observedTransitions.has_key(r.previousWinnerIndex):
                #if r.newWinnerIndex not in observedTransitions[r.previousWinnerIndex]:
                    #observedTransitions[r.previousWinnerIndex].append(r.newWinnerIndex)
            events.append(Event(states[i-1], states[i], vec, sensorStreams[0].getTime(i)))
        elif errs == 1:
            events.append(Event(states[i], states[i], vec, sensorStreams[0].getTime(i)))
                    
                    
    for event in events:
        print event
    #print states
    #plt.plot(range(10000), states, '*')
    #plotColorStatesNoNumber(states)

    vectors = []
    for model in r.models:
    	vectors.append(model.vector)

    return r, states, events, errors

def removeStream(sensorStreams, name):
    success = False
    for stream in sensorStreams:
        if stream.getLabel() == name:
            sensorStreams.remove(stream)
            success = True

    if not success:
        print "Stream", name, "not found in list."
    return sensorStreams

def runTest(realErrors, realEvents, recErrors, recEvents):

    curRec = 0
    curReal = 0

    falseposError = 0
    falsenegError = 0
    trueposError = 0
    truenegError = 0

    falseposEvent = 0
    falsenegEvent = 0
    trueposEvent = 0
    truenegEvent = 0
    
    for error in recErrors:
        while error.getTime() > realErrors[currReal].getTime():
            currReal += 1
            falsnegError += 1
        if error.getTime() < realErrors[currReal].getTime():
            falseposError += 1
        elif error.getTime() == realErrors[currReal].getTime:
            if error.getSensor() == realErrors[currReal].getSensor():
                trueposError += 1
                currReal += 1
            else:
                it = 1
                success = False
                while error.getTime() == realError[currReal+it].getTime():
                    if error.getSensor() == realErrors[currReal + it].getSensor():
                        trueposError += 1
                        realErrors.pop(currReal+it)
                        success = True
                        break
                if not success:
                    falseposError += 1
       
    truenegError = len(states)-falseposError-trueposError-falsenegError

    for event in recEvents:
        while event.getTime() > realEvents[currReal].getTime():
            currReal += 1
            falsnegEvent += 1
        if event.getTime() < realEvents[currReal].getTime():
            falseposEvent += 1
        elif event.getTime() == realEvents[currReal].getTime:
            trueposEvent += 1
       
    truenegEvent = len(states)-falseposEvent-trueposEvent-falsenegEvent

    print "\nError detection statistics:"
    print "True (?) negatives:", truenegError
    print "True positives:", trueposError
    print "False negatives:", falsenegError
    print "False (?) positives:", falseposError
    print
    print "Accuracy:", (trueposError+truenegError)/len(states)
    print "Sensitivity:", (trueposError)/(trueposError+falsenegError)
    print "Specificity:", truenegError/(truenegError+falseposError)

    print "\nEvent detection statistics:"
    print "True (?) negatives:", truenegEvent
    print "True positives:", trueposEvent
    print "False negatives:", falsenegEvent
    print "False (?) positives:", falseposEvent
    print
    print "Accuracy:", (trueposEvent+truenegEvent)/len(states)
    print "Sensitivity:", (trueposEvent)/(trueposEvent+falsenegEvent)
    print "Specificity:", truenegEvent/(truenegEvent+falseposEvent)

def saveToFile(filename, thing):
    fp = open(filename, 'w')
    pick = Pickler(fp)
    pick.dump(thing)
    fp.close()

def loadFromFile(filename):
    fp = open(filename, 'r')
    unpick = Unpickler(fp)
    result = unpick.load()
    fp.close()
    return result

def main():

    """
    timeInt = 15
    bufferSize = 100
    delta = .9
    historySize = 2
    learningRate = .2
    sensorFiles = ["wxsta1_alldat.csv"]
    removeStreams = []
    checkid = ""
    epsilon = 1
    """

    parser = OptionParser()
    parser.add_option("-t", "--timeInt", default = 15, action ="store", dest="timeInt", type= "float", help="The frequency with which to evaluate the current vector of the most recent data.")
    parser.add_option("-b", "--bufferSize", default=100, action="store", dest="bufferSize", type= "int", help="Buffer size for RAVQ")
    parser.add_option("-e", "--epsilon", default=1, action="store", dest="epsilon", type="float", help="Epsilon for RAVQ")
    parser.add_option("-d", "--delta", default=.9, action = "store", dest="delta", type= "float", help="Delta for RAVQ")
    parser.add_option("-s", "--historySize", default=2, dest="historySize", type= "int", help="History size for the RAVQ.")
    parser.add_option("-l", "--learningRate", action="store", default=.2, nargs=1, dest="learningRate", type= "float", help="Learning rate for the ARAVQ")
    parser.add_option("-f", "--sensorFiles", action="store",default=["wxsta1_alldat.csv"], dest="sensorFiles", type="string", help="Files containing data to used.")
    parser.add_option("-r", "--removeStreams", action = "store", default="[]", dest="removeStreams", help="Streams to not use.", type="string")
    parser.add_option("-c", "--checkid", action = "store", default="", dest="checkid", help="ID of checkpoint to save files under.")
    (opts, args) = parser.parse_args()
    print sys.argv
    print opts
    print args

    sensorStreams = readin(eval(opts.sensorFiles))

    for stream in eval(opts.removeStreams):
        sensorStreams = removeStream(sensorStreams, stream)

    for stream in sensorStreams:
        print stream
    
    #e = sensorStreams[11].scanForErrors()

    #for err in e:
        #print err

    #print "Running RAVQ with epsilon %, delta %, learning rate %", opts.epsilon, opts.delta, opts.learningRate

    r, states, events, errors = runRAVQ(sensorStreams, opts.timeInt, opts.bufferSize, opts.epsilon, opts.delta, opts.historySize, opts.learningRate, opts.checkid)
    checkpoint(r, states, sensorStreams, errors, events)
    
    """
    #vecs1 = []
    #for i in range(1000):
        #vecs1.append(getVec(sensorStreams, 5))

    print sensorStreams[3]
    vecs1 = [[i] for i in sensorStreams[3].getStream()]

    vecs2 = interp(vecs1, 2)

    print compareVecs(vecs2, vecs1)
    """
    #r, states = runRAVQ(sensorStreams)
    
main()
