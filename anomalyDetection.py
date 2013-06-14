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
                        line[j] = -1
                        
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
            times.append(data[i][j][0])
        for j in range(1+offset, len(data[i][j])+offset):
            realSensorStreams.append(SensorStream(sensorStreams[j], times, labels[j]))
        offset += len(data[i][0])
    
    return realSensorStreams

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
        if not isnan(x[i]) and not isnan(y[i]) and x[i] != -1 and y[i] != -1:
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

def compareVecs(interpVecs, realVecs):
    sumDist = 0
    print len(interpVecs), len(realVecs)
    for i in range(min(len(interpVecs), len(realVecs))):
        sumDist += euclidDist(interpVecs[i], realVecs[i])
    return sumDist

def runRAVQ(sensorStreams, timeInt):
    r = ARAVQ(100, 1, .9, 2, .2, timeInt)
    
    states = []
    events = []

    observedTransitions = {}

    #for i in range(138349):
    for i in range(len(sensorStreams[0].getStream())):
        if i%1000 == 0:
            print sensorStreams[0].getCurrTime()
        vec = getVec(sensorStreams, timeInt)
    	r.input(vec)
    	states.append(r.newWinnerIndex)
        if r.newWinnerIndex != r.previousWinnerIndex:
            if observedTransitions.has_key(r.previousWinnerIndex):
                if r.newWinnerIndex not in observedTransitions[r.previousWinnerIndex]:
                    observedTransitions[r.previousWinnerIndex].append(r.newWinnerIndex)
                    events.append(Event(states[i-1], states[i], vec, sensorStreams[0].getTime(i)))
            else:
                observedTransitions[r.previousWinnerIndex] = [r.newWinnerIndex]
                events.append(Event(states[i-1], states[i], vec, sensorStreams[0].getTime(i)))
                    
                    
    for event in events:
        print event
    #print states
    #plt.plot(range(10000), states, '*')
    plotColorStatesNoNumber(states)

    vectors = []
    for model in r.models:
    	vectors.append(model.vector)

    return r, states

def removeStream(sensorStreams, name):
    for stream in sensorStreams:
        if stream.getLabel() == name:
            sensorStreams.remove(stream)
    return sensorStreams

def runTest(sensorStreams, timeInt, answers):
    r = runRavq(sensorStreams, timeInt)

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
    sensorStreams = readin(["wxsta1_Table1.dat"])

    sensorStreams = removeStream(sensorStreams, "RECORD")
    sensorStreams = removeStream(sensorStreams, "weir_lvl_TMx")

    for stream in sensorStreams:
        print stream
    r, states = runRAVQ(sensorStreams, 5)
    saveToFile("storedRavq", r)
    saveToFile("storedStates", states)
    saveToFile("storedSensorStreams", sensorStreams)
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
