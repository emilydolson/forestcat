"""
The realTimeSensorStreams library contains class for gracefully handling
the messy intricasies of real time sensor data.

Copyright 2012-2013, Emily Dolson, distributed under the Affero GNU Public
License.

    This file is part of FoREST-cat.

    FoREST-cat is free software: you can redistribute it and/or modify
    it under the terms of the Affero GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FoREST-cat is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Affero GNU General Public License for more details.

    You should have received a copy of the Affero GNU General Public License
    along with FoREST-cat.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__= "Emily Dolson <EmilyLDolson@gmail.com>"
__version__= "1.0"

from datetime import datetime, timedelta
from math import isnan

def loadDictFromFile(filename):
    """
    Reads from the file with the specified (string) name,
    and makes a dictionary in which each line is an entry.
    Everything before the first comma in the line is the key,
    and the value is a list of the remaining comma-separated items.
    """
    d = {}
    infile = open(filename)
    for line in infile:
        sline = line.split(",")
        sline = [w.strip() for w in sline]
        d[sline[0]] = sline[1:]
    infile.close()
    return d

def findNormVals(name):
    """
    This is a horrible horrible function. It is designed exclusively
    for the purpose of matching variable names with hard-coded values
    as quickly as possibly, in the Hubbard Brook context specifically.
    Input: name - a string indicating the name of the variable in datafiles.
    Returns: a tuple containing the minimum possible value for this
    variable, the maximum, and the label of the variable.
    """
    name = name.lower().split("_")
    if len(name) >= 1 and name[0] == "ws":
        return (0, 100, "wind speed (m/s)")
    elif len(name) >= 1 and name[0] == "slrkj": #no actual upper bound
            return (0, 1500, "solar radiation/m2 (kJ)") #but this seems safe
    elif len(name) >= 1 and name[0] == "slrkw": 
            return (0, 1.5, "solar radiation/m2 (kW)")
    elif len(name) == 1:
        if name[0] == "cond" or name[0] == "ct":
            return (.005, 7, name[0])
        if name[0] == "precipitation" or name[0] == "reportpcp":
            return (0, 1, "precipitation (in)")
        if name[0][3:] == "airtc":
            return (-40, 60, "air temperature (c)")
        if name[0] == "gageminv" or name[0][:8] == "actdepth":
            return(0, 16, "rain gauge depth")
        if name[0] == "rh":
            return (0,100, "relative humidity")
        if name[0] == "winddir":
            return (0, 360, "wind direction (degrees)")
        if name[0] == "acttemp":
            return (0, 50, "rain gauge water temperature (c)")
        else:
            print name, "not found in lookup table"
    
    elif len(name) >= 2 and ((name[0]=="air" and name[1][:4]=="temp") or name[0]=="airtc"):
        return (-40, 60, "air temperature (c)")
        
    elif len(name) == 3 and name[2] == "avg":
        if name[0] == "ec":
            return (0, 8, "ec")
        if name[0] == "perm":
            return(1, 81, "perm")
        if name[0] == "vwc":
            return (.05, .5, "vwc")
        if name[0] == "tsoil":
            return (-10, 70, "soil temperature (c)")

    elif len(name) >= 2 and ((name[0] == "weir" and name[1] == "lvl") or 
                             (name[0] == "lvl" and name[1] == "ft")):
        return (0, 2, "level (ft)")
    
    elif len(name) >=2 and name[0] == "flume" and name[1] == "lvl":
        return (-.6, 60, "flume level (feet)") #this is a problem

    elif len(name) == 3:
        if name[1] == "air" and name[2][:4] == "temp":
            return (-40, 60, "air temperture (c)")
        if name[0] == "cr1000" and name[1] == "panel" and name[2] == "temp":
            return (-40, 60, "panel temperature (c)")
        if name[0] == "rain" and name[1] == "in" and name[2] == "tot":
            return (0, 1, "precipitation (inches)")

    elif len(name) == 2:
        if name[0] == "temp" and name[1] == "c":
            return (0, 50, "water temperature (c)")
        if name[0] == "relative" and name[1] == "humidity":
            return (0, 100, "relative humidity")
        if name[0] == "bucket" and name[1] == "depth":
            return (0, 16, "rain gauge depth")
    
    return None

def convertDateTime(datestring):
    """
    Takes in a string representing the date and time in
    Hubbard Brook format and return a datetime object
    """
    if datestring == "":
        return None
    if datestring[0] == "A": #MODIS format
        year = int(datestring[1:5])
        day = int(datestring[5:])
        return datetime(year, 1, 1, 0, 0, 0) + timedelta(day-1)

    if datestring[0] == "(": #datetime object format
        d = eval(datestring)
        return datetime(d[0], d[1], d[2], d[3], d[4], d[5])

    try: #MATLAB format
        datestring=float(datestring)
        return datetime.fromordinal(int(datestring)) + timedelta(days=datestring%1) - timedelta(days = 366)

    except ValueError: #Hubbard Brook Format
        try:
            year = int(datestring[:4])
            month = int(datestring[5:7])
            date = int(datestring[8:10])
            hour = int(datestring[11:13])
            minute = int(datestring[14:16])
            seconds = int(datestring[17:19])
            return datetime(year, month, date, hour, minute, seconds)
        except (TypeError, IndexError, ValueError) as e:
            #This is not a date in any recognized format
            return None

class rtSensorStream:
    """
    This class handles the stream of data from a single sensor.
    """
    def __init__(self, name, source):
        """
        Inputs: name - variable name of this sensor in file (string)
        source - file that this stream can be found in (string)
        """
        self.name = name #Variable name of sensor from file
        streamInfo = findNormVals(name)
        if streamInfo == None:
            print "ERROR! Stream", source, name, "not found"
            return

        minVal, maxVal, self.label = streamInfo
        #self.label = self.label #Label for graphs
        self.source = source #File this sensor is in
        self.range = (minVal, maxVal) #minimum and maximum
             #possible values for sensor, for normalization
        self.valBuffer = [] #stores data to be processed
            #Should valBuffer maybe be a better data structure?
            #It will normally be FIFO, but occasionally things
            #will need to be rearranged by date. The overhead
            #of a priority queue is probably still not worth it.

        self.currTime = None #The time that this sensor thinks it is
        self.lastVal = None #The last value emitted by this sensor.
        self.freq = None #How frequently does this sensor take measurements?
        self.errorState = False #Is this sensor currently in an errorState?
                          #(used to avoid sending too many e-mails)

    """
    def __init__(self, stream):
        ""
        Inputs: name - variable name of this sensor in file (string)
        source - file that this stream can be found in (string)

        The version is basically a copy constructor.
        ""
        self.name = stream.name #Variable name of sensor from file
        self.label = stream.label #Label for graphs
        self.source = stream.source #File this sensor is in
        self.range = stream.range #minimum and maximum
             #possible values for sensor, for normalization
        self.valBuffer = stream.valBuffer #stores data to be processed
            #Should valBuffer maybe be a better data structure?
            #It will normally be FIFO, but occasionally things
            #will need to be rearranged by date. The overhead
            #of a priority queue is probably still not worth it.

        self.currTime = stream.currTime #The time that this sensor thinks it is
        self.lastVal = stream.lastVal #The last value emitted by this sensor.
        self.freq = stream.freq #How frequently does this sensor take measurements?
        self.errorState = stream.errorState #Is this sensor currently in an errorState?
                          #(used to avoid sending too many e-mails)
    """
    def __str__(self):
        return self.source + " " + self.name + " " + self.label + " " + str(self.range) + ": " + str(self.valBuffer[:min(5, len(self.valBuffer))]) + ("..." if len(self.valBuffer) > 5 else "")
    
    def next(self, time):
        """
        Returns the next value this sensor recorded if there is one.
        Otherwise, returns the value most recently emitted.

        Input: time - a datetime object indicating the time at which
        the datapoint in which this value will be used was taken.
        This is necessary because sensors often send data to the
        server in chunks, such that there are a number of data
        points to be processed at once, each of which were
        recorded at a different point slightly in the past.
        We don't want to use values from what is, from the internal
        perspective, the future. Of course, there might be a useful
        way to do so that could be explored in a future version.

        Returns: an rtSensorValue object containing the appropriate
        value from the sequence
        """
        if len(self.valBuffer) > 0 and time >= self.valBuffer[0].time:
            #There is a value in the buffer to emit
            self.lastVal = self.valBuffer[0] 
            self.currTime = self.lastVal.time
            return self.valBuffer.pop(0)
        
        if self.lastVal != None and time >= self.lastVal.time:
            #No values in buffer, re-emit most recent value
            self.currTime = self.lastVal.time
            return self.lastVal
        
        if self.lastVal == None:
            #There have never been any values in the buffer
            print "ERROR: Initial values required for all sensors"

        else:
            #The time specified is before any of the available data
            print "ERROR: Nonlinear time! (WibbblyWobblyTimeyWimeyException)"

    def normalize(self, val):
        """
        Normalize a value based on the range for this sensor
        All values are normalized before storage.
        Input: val - a float (the value)
        Returns: a float between 0 and 1
        """
        return (val-self.range[0])/(self.range[1]-self.range[0])

    def getOrigVal(self, val):
        """
        Reverses the normalization process.
        Inputs: val - a float between 0 and 1 representing
        a normalized value
        Returns: a float between the sensor's minimum and maximum
        values.
        """
        return val*(self.range[1]-self.range[0]) + self.range[0]

    def sync(self, time):
        """
        Removes values from buffer that are before the specified time.
        This is useful in the case where this sensor's frequency is faster
        than the interval at which FoREST-cat is processing data.
        Input: time - a datetime object indicating the time to sync to
        """
        while(len(self.valBuffer) > 1):
            if self.valBuffer[1].time <= time:
                self.lastVal = self.valBuffer.pop(0)
            else:
                self.currTime = self.valBuffer[0].time
                return
            self.currTime = self.valBuffer[0].time

    def addToBuff(self, val, time):
        """
        Handles adding new values to buffer.
        Inputs: val - float indicating value to add
        time - datetime object indicating time at which value was recorded
        """

        if (len(self.valBuffer)>0 and time < self.valBuffer[-1].time):
            #if this item doesn't belong at the end of the buffer,
            #put it where it does belong
            i = 0
            while self.valBuffer[i].time < time:
                i += 1
            self.valBuffer.insert(i, rtSensorValue(self, time, self.normalize(val)))
            if i == 0:
                self.currTime = time

        elif self.lastVal != None and time < self.lastVal.time:
            #This is from before the last value submitted.
            #Don't add it.
            return
        
        else:
            #we can just add the value to the back
            self.valBuffer.append(rtSensorValue(self, time, self.normalize(val)))
            if len(self.valBuffer) == 1:
                self.currTime = time

class SensorArray:
    """
    A class for keeping track of a number of rtSensorStream objects and
    making sure that they are synchronied and contain the desired data.
    """
    def __init__(self, dictFile, startTime):
        """
        Inputs: dictfile - name of file indicating which files to examine
        for which variables (string)
        startTime - datetime object indicating earliest time to accept data from
        """
        self.currTime = startTime
        self.keepGoing = False
        self.nameSenseDict = {} #dictionary linking file names to rtSensorStream
        #objects to be updated by that file

        nameVarDict = loadDictFromFile(dictFile)
        for key in nameVarDict.keys():
            if key.find("+") != -1: #sometimes data is split across files
                sKey = key.split("+") #the "+" shortcut handles that
                senseList = [rtSensorStream(i, sKey[0]) for i in nameVarDict[key]]
                #store pointer to same object in both dicts
                self.nameSenseDict[sKey[0]] = senseList
                self.nameSenseDict[sKey[1]] = senseList
            else:
                self.nameSenseDict[key] = [rtSensorStream(i, key) for i in nameVarDict[key]]
        self.getData()
        self.initFreqs()
        self.keepGoing = False
    
    def __len__():
        n = 0
        for key in self.nameSenseDict.keys():
            n += len(self.nameSenseDict[key])

        return n

    def getNext(self, timeDiff):
        """
        Generate the next vector to feed into FoREST-cat.
        Inputs: timeDiff - how much after the last timestep is this
        timestep supposed to be (int)?
        Returns: a list of the appropriate values from all sensors
        """
        self.keepGoing = False
        self.currTime += timedelta(minutes=timeDiff)
        vec = []
        keys = self.nameSenseDict.keys()
        keys.sort() #be absolutely positive that order is consistent
        for key in keys:
            for sensor in self.nameSenseDict[key]:
                sensor.sync(self.currTime)
                vec.append(sensor.next(self.currTime))
                if abs(vec[-1].time - self.currTime) > sensor.freq*2:
                    vec[-1].value = float("nan") #interpolate
                if len(sensor.valBuffer) > 0:
                    self.keepGoing = True
        return vec

    def initFreqs(self):
        """
        Iterate through sensors and caculate frequencies by comparing time
        stamps of first and second values. Theoretically it might be good
        to use a slgithly larger sample size. Also, this would need to be
        changed a bit to work in a situation where the data were actually
        arriving in completely real time.
        """
        for key in self.nameSenseDict.keys():
            for sensor in self.nameSenseDict[key]:
                if len(sensor.valBuffer) > 1:
                    sensor.freq = sensor.valBuffer[1].time - sensor.valBuffer[0].time

    def pollCurrTimes(self):
        """
        Looks through current times of all the sensors and sets
        the array current time to the latest of these.
        We always want to use the most recent data available at a given
        time step. Therefore, the current time of the array should always
        be the latest time of any item in the next vector. Therefore,
        we set currTime to the latest currTime available.
        """
        for key in self.nameSenseDict.keys():
            for sensor in self.nameSenseDict[key]:
                if sensor.currTime != None and sensor.currTime  > self.currTime:
                    self.currTime = sensor.currTime

    def getData(self):
        """
        Opens source files and reads in any data with a time stamp
        later than the current time for each sensor to the sensor
        buffers.
        """
        for key in self.nameSenseDict.keys(): #keys are file names
            infile = open("RTD/"+key)
            infile.readline() #Skip header

            #Figure out columns of each variable
            labels = infile.readline().split(",") #second line has labels
            labels = [l.strip("\'\"\r\n ") for l in labels]

            #Make sure format is correct
            if labels[0] != "TIMESTAMP":
                #This could screw everything up
                print "INVALID FILE FORMAT!"
                return False
            
            #Get list of indices of variables of interest
            indices = []
            for var in self.nameSenseDict[key]:
                found = False
                for i in range(len(labels)):
                    if not found and var.name == labels[i]:
                        indices.append(i)
                        found = True
                if not found:
                    print "Index for", var.name, "not found!"
                    return False
            
            #Get data
            #print indices
            for line in infile:
                sline = line.split(",")
                sline[0] = convertDateTime(sline[0].strip("\' \""))
                if sline[0] == None or sline[0] <= self.currTime:
                    continue #skip too-early lines
                for i in range(len(indices)):
                    try:
                        sline[indices[i]] = float(sline[indices[i]])
                    except ValueError: #not a number
                        sline[indices[i]] = float("nan")
                    #add data to buffer
                    self.nameSenseDict[key][i].addToBuff(sline[indices[i]], sline[0])

            infile.close()
            
            #If any sensor has stuff left in the buffer, there will
            #be stuff to process, so tell the main loop to do so
            for sensor in self.nameSenseDict[key]:
                if len(sensor.valBuffer) > 0:
                    self.keepGoing = True

        #Make sure everything is at the right time
        self.pollCurrTimes()
        for key in self.nameSenseDict.keys():
            #In case timeInt > sensor.freq, make
            #sure that all sensors have the latest
            #possible value up next
            for sensor in self.nameSenseDict[key]:
                sensor.sync(self.currTime)
        
class rtSensorValue():
    """
    This class allows for the storing of metadata with values.
    """
    def __init__(self, sensor, time, value):
        """
        Inputs: sensor - pointer to sensor that produced this value
        time - datetime object indicating when this point was recorded
        value - float indicating value recorded.
        """
        self.sensor = sensor 
        self.time = time 
        self.value = value 
        self.replaced = False #was this value interpolated because
                        #of an invalid number?
        self.flag = None #If this value was replaced, why?
        self.bin = None #for information theory analysis

        if isnan(self.value):
            self.replaced = True #This is going to get
            self.flag = "Missing" #replaced although not yet

        if self.value < 0 or self.value > 1: 
            #print value, sensor.getOrigVal(value), "value out of range from", sensor
            self.value = float("nan")
            self.replaced = True
            self.flag = "Out of range"
