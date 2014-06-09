 #!/usr/bin/python

"""
FoREST-cat is a program for detecting errors and rare events in real-time 
wireless sensor network data. It guesses which anomalies are errors and
which are rare events by looking at data from a variety of sensors at once.

Copyright 2012-2013, Emily Dolson, distributed under the Affero GNU Public
License.
"""

__author__= "Emily Dolson <EmilyLDolson@gmail.com>"
__version__= "1.0"

"""
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

from realTimeSensorStreams import *
from ravq import *
from event import *
from math import sqrt, isnan
from optparse import OptionParser
from email.mime.text import MIMEText
from datetime import datetime
import os, sys, pickle, smtplib, signal, subprocess
import matplotlib.pyplot as plt

def log(text):
    """
    Automated function for making log entries. Text is the text of the entry.
    Returns boolean indicating success
    """
    try: #we don't want this crashing on non-critical exceptions
        if os.path.exists("log"):
            logfile = open("log", "a")
        else:
            logile = open("log", "w+")
        logfile.write(str(datetime.now()) + ": " + str(text)+"\n")
        logfile.close()
    except Exception as e:
        sendEmail("Received execption " + str(e) + "while trying to make log entry: " + str(datetime.now()) + ": " + text, "FoREST-cat log file", "seaotternerd@gmail.com")

def sendEmail(sendStr, subject, recepient="seaotternerd@gmail.com"):
    """
    Sends an e-mail to the predesignated list of people.
    Inputs: sendstr = the text of the e-mail to send (string)
    subject = the subject of the email (string)
    """
    msg = MIMEText(sendStr)
    sender = "sensorerrorsandevents.hbef@gmail.com"
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = "seaotternerd@gmail.com"
    
    try: #we don't want this crashing on non-critical exceptions
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo
        s.login(sender, "mirrorlake")
        s.sendmail("sender", ["seaotternerd@gmail.com"], msg.as_string())
        s.quit()
        log("E-mail sent! Subject:" + subject)
        return True

    except Exception as e:
        log("Attempt to send e-mail failed with exception " + str(e))
        return False

def errorAlert(err):
    """
    Sends a standardized error alert message out to standard set of recipients.
    Input: err - an error object to be reported on
    Returns boolean indicating success
    """
    msg = "A potential error (" + err.flag + ") has been detected in " + err.getSensor() + " at " + str(err.getTime()) + ".\n\n"
    msg += "The potentially erroneous value was " + str(err.value) + "."
    if err.replaced != None:
        msg += "In order to continue with the functioning of the algorithm, this value was replaced with" + str(err.replaced) + "."
    msg += "The FoREST-cat algorithm has flagged this value as likely to be an error. This is just a prediction -"
    msg += " this value may, instead, be the result of a rare event.\n\n"
    msg += "Please help improve FoREST-cat by answering a 2-question survey: "
    msg += "https://docs.google.com/forms/d/1bgDqDnBTGfrt_qgotQcOmdFZ8EHqVY7UiKi1SWZB1-c/viewform?entry.1751902321=Cannot+be+determined&entry.1322398871=Maybe&entry.1034004670=Unknown&entry.234465177\n\n"
    msg += "Something going wrong? E-mail the developer at EmilyLDolson@gmail.com."
    return sendEmail(msg, "Potential sensor error", "EmilyLDolson@gmail.com")

def eventAlertTransition(eve):
    """
    Sends a standardized transition event alert out to standard recipients.
    Input: eve - an event object to be reported on.
    Returns boolean indicating success
    """
    msg = "A potential rare event has been detected at " + str(eve.getTime()) + ".\n\n"
    msg += "The FoREST-cat algorithm has flagged this value as likely to be a rare event, rather than an error. This is just a prediction -"
    msg += " this value may, instead, be the result of an erorr. It's also possible that this event isn't particularly rare or interesting, in which case you may or may not think it's actually worth being alerted to.\n\n"
    msg += "This potential event was flagged because of a change in category. This may be a shift into a rare category, or simply a shift"
    msg += " between two similar categories. Thus, it has a fairly high potential to not be interesting.\n\n"
    msg += "Please help improve FoREST-cat by answering a 2-question survey: "
    msg += "https://docs.google.com/forms/d/11gw-_Mo2Hn0C7dolZbVQKf46M5DAdSLqfOC6IxQdeyw/viewform?entry.1751902321=Cannot+be+determined&entry.2112662628=Transition&entry.1322398871=Maybe&entry.1034004670&entry.234465177\n\n"
    msg += "Something going wrong? E-mail the developer at EmilyLDolson@gmail.com."
    return sendEmail(msg, "Potential rare event", "EmilyLDolson@gmail.com")

def eventAlertAnomalous(eve):
    """
    Sends a standardized transition event alert out to standard recipients.
    Input: eve - an event object to be reported on.
    Returns boolean indicating success
    """
    msg = "A potential rare event has been detected in at " + str(eve.getTime()) + ".\n\n"
    msg += "The FoREST-cat algorithm has flagged this value as likely to be a rare event, rather than an error. This is just a prediction. \n\n"
    msg += "This potential event was flagged because of a high number of anomalous values occuring at the same time. It is possible that all of these"
    msg += " sensors are reporting erroneous values.\n"
    msg += "Please help improve FoREST-cat by answering a 2-question survey: "
    msg += "https://docs.google.com/forms/d/11gw-_Mo2Hn0C7dolZbVQKf46M5DAdSLqfOC6IxQdeyw/viewform?entry.1751902321=Cannot+be+determined&entry.2112662628=Anomalous+values&entry.1322398871=Maybe&entry.1034004670&entry.234465177\n\n"
    msg += "Something going wrong? E-mail the developer at EmilyLDolson@gmail.com."
    return sendEmail(msg, "Potential rare event", "EmilyLDolson@gmail.com")

def saveStateInfo(ravq, sensors):
    outfile = open("state_info.csv", "w")

    senseList = []
    for i in range(len(sensors)):
        senseList.append(sensors[i].source + "-" + sensors[i].name)

    outfile.write(",".join(senseList))

    for model in ravq.models:
        outfile.write(",".join([str(i) for i in model.vector]) + "\n")

    outfile.close()

def saveToFile(filename, thing):
    """
    Generic pickling wrapper, stores a pickled version of "thing" in the file denoted by the filename string.
    Returns boolean indicating success
    """ 
    try: #we don't want this crashing on non-critical exceptions
        fp = open(filename, 'w')
        pick = pickle.Pickler(fp)
        pick.dump(thing)
        fp.close()
        return True

    except Exception as e:
        log("Attempt to pickle a thing failed with exception " + str(e))
        sendEmail("Received execption " + str(e) + "while trying to pickle a thing at " + str(datetime.now()), 
                  "FoREST-cat pickle fail", "seaotternerd@gmail.com")
        return False

def loadFromFile(filename):
    """
    Generic unpickling wrapper, loads whatever pickled object is stored in the file denoted by the filename string.
    """
    try: #we don't want this crashing on non-critical exceptions
        fp = open(filename, 'r')
        unpick = pickle.Unpickler(fp)
        result = unpick.load()
        fp.close()
        return result
    
    except Exception as e:
        log("Attempt to unpickle a thing failed with exception " + str(e))
        sendEmail("Received execption " + str(e) + "while trying to unpickle a thing at " + str(now()), 
                  "FoREST-cat unpickle fail", "seaotternerd@gmail.com")
        return None

def makeDate(option, opt, value, parser):
    """
    Function to create a date object as a callback
    from option parser. Value is a string of numbers separated
    by commas.
    """
    args = value.split(",")
    return datetime(args)

def saveProgress(states, errors, events, sensors, r):
    """
    Helper function to save all progress thus far to appropriate files.
    """
    #Save state categorization
    if os.path.exists("states"):
        stateFile = open("states", "a")
    else:
        stateFile = open("states", "w+")
    for state in states:
        stateFile.write(str(",".join(str(i) for i in state)) +"\n")
    stateFile.close() 
    log("States written to file")

    #Save errors if there are any
    if len(errors) > 0 :
        if os.path.exists("errors"):
            errorFile = open("errors", "a")
        else:
            errorFile = open("errors", "w+")
        for error in errors:
            errorFile.write(error)
        errorFile.close()
        log("Errors written to file.")

    #Save events if there are any
    if len(events) > 0:
        if os.path.exists("events"):
            eventFile = open("events", "a")
        else:
            eventFile = open("events", "w+")
        for event in events:
            eventFile.write(str(event))
        eventFile.close()
        log("Events written to file")

    #save RAVQ
    saveToFile("ravq", r)
    saveToFile("time", sensors.currTime)
    saveStateInfo(r, sensors)
    log("RAVQ stored.")

def getInput():
    """
    Run command line argument parser and return results
    """
    parser = OptionParser()
    parser.add_option("-t", "--timeInt", default = 5, action ="store", dest="timeInt", type= "float", help="The frequency with which to evaluate the current vector of the most recent data.")
    parser.add_option("-R", "--refresh-rate", default = 60, action = "store", dest="refreshRate", type="int", help="How frequently (in minutes) are new data available at the pull location?")
    parser.add_option("-p", "--pull-location", default = "edolson@gromit.sr.unh.edu:/d1/proj/hbrook/sensor/field/RTD", action="store", dest="pullLocation", type="string", help="Location from which data can be pulled in real-time.")
    parser.add_option("-E", "--eventThreshold", default=.5, action="store", dest="eventThreshold", type="float", help="Percent of sensors that must exhibit errors to qualify as suspected event.")
    parser.add_option("-b", "--bufferSize", default=100, action="store", dest="bufferSize", type="int", help="Buffer size for RAVQ")
    parser.add_option("-e", "--epsilon", default=1, action="store", dest="epsilon", type="float", help="Epsilon for RAVQ")
    parser.add_option("-d", "--delta", default=.9, action = "store", dest="delta", type= "float", help="Delta for RAVQ")
    parser.add_option("-s", "--historySize", default=2, dest="historySize", type= "int", help="History size for the RAVQ.")
    parser.add_option("-l", "--learningRate", action="store", default=.2, nargs=1, dest="learningRate", type= "float", help="Learning rate for the ARAVQ")
    parser.add_option("-c", "--checkid", action = "store", default="", dest="checkid", help="ID of checkpoint to save files under.")
    parser.add_option("-r", "--restart", action = "store_true", default=False, dest="restart", help="Restart from previous run?")
    parser.add_option("-C", "--config-file", action = "store", default="forestcat.config", dest="config", help="Configuration file")
    parser.add_option("-i", "--inject-eratics", action = "store_true", default=False, dest="injectEratics", help="Inject simulated eratic errors into data.")
    parser.add_option("-T", "--test", action = "store_true", default=False, dest="test", help="Run FoREST-cat in test mode (don't store data in Amazon cloud).")
    parser.add_option("-D", "--startDate", action = "callback", callback=makeDate, type="string", default=datetime(2013, 7, 25, 1, 1, 1), dest="startDate", help="The earliest time point to use in this run.")
    (opts, args) = parser.parse_args()
    return opts

def main():

    def exit_handler(signum, trace):
        """
        Handle exit smoothly and save progress
        """
        print "Thank you for using FoREST-Cat. Saving progress."
        log("Recieved exit command. Saving progress\n")
        if "states" not in globals():
            states = []
            errors = []
            events = []
        if "sensors" in dir() and "r" in dir():
            saveProgress(states, errors, events, sensors, r)
            log("Progress saved.\n")
        print "Exiting..."
        log("Exiting...\n\n")
        exit(0)

    #Install exit handler - program will exit when it receives SIGINT
    signal.signal(signal.SIGINT, exit_handler)

    # Get command line aruments
    opts = getInput()

    print "Welcome to the FoREST-cat program for detecting errors and rare events in data from multiple sensory modalities."

    #Initialize data
    if not opts.test:
        try:
            subprocess.check_call(["rsync", "-e", "ssh", "-avz", opts.pullLocation, "."])
        except Exception as e:
            log("Call to rsync failed")
            sendEmail("Call to rsync failed with exception " + str(e), "rsync fail", "seaotternerd@gmail.com")
        else:
            log("call to rsync successful")

    if not opts.restart: #if we aren't loading a pre-existing RAVQ, we need to 
        #do this before generating the new one, so we know how many sensors there are
        log("loading sensors")
        sensors = SensorArray(opts.config, opts.startDate)
        initData = sensors.getNext(opts.timeInt) #this doesn't get input
        #if we want to be really efficient, fix this one day
        log("sensors loaded")
        saveToFile("sensors", sensors)
    
    #Initialize ravq
    if opts.restart:
        print "Loading stored ravq from file..."
        r = loadFromFile("ravq") #default file for storing ravq
        opts.startDate = loadFromFile("time")
        if r == None or opts.startDate == None:
            log("Failed to load RAVQ. Closing...")
            sendEmail("Failed to load RAVQ, FoREST-cat is closing.", 
                  "FoREST-cat load fail", "seaotternerd@gmail.com")
            exit()
        log("Loaded RAVQ")
    else:
        log("Generating new RAVQ...")
        r = ARAVQ(opts.bufferSize, opts.epsilon, opts.delta, len(initData), opts.historySize, opts.learningRate)
        log("RAVQ generated.")

    if opts.restart: #if we are loading a pre-existing RAVQ, we need to 
        #do this after loading it, so we know when the start date is
        log("loading sensors")
        sensors = SensorArray(opts.config, opts.startDate)
        initData = sensors.getNext(opts.timeInt) #this doesn't get input
        #if we want to be really efficient, fix this one day
        log("sensors loaded")
        saveToFile("sensors", sensors)

    #Set up Amazon Web Services stuff
    if not opts.test:
        from boto.s3.lifecycle import Lifecycle, Rule, Transition
        import boto
        s3Conn = boto.connect_s3()
        bucket = s3Conn.get_bucket("forest-cat")
        lifecycle = Lifecycle()
        for item in ["log", "ravq", "events", "errors", "states"]:
            #set rules for transition to Glacier
            to_glacier = Transition(days=7, storage_class = "GLACIER")
            rule = Rule(item+"Rule", item, "Enabled", transition = to_glacier)
            lifecycle.append(rule)
        bucket.configure_lifecycle(lifecycle)

    today = {0: datetime.date(datetime.now())} #dictionary so it can modified in handler

    def alarm_handler(signum, frame):
        """
        This function will get called any time the alarm goes off.
        It is defined here so that it will have access to main() local
        variables. This supports an event-driven design.
        """
        log("Starting processing...")

        #get data
        #check for updates with rsync - RSA keys need to be appropriately configured for this to work
        if not opts.test:
            try:
                subprocess.check_call(["rsync", "-e", "ssh", "-avz", opts.pullLocation, "."])
            except Exception as e:
                log("Call to rsync failed")
                #sendEmail("Call to rsync failed with exception " + str(e), "rsync fail", "seaotternerd@gmail.com")
            else:
                log("call to rsync successful")
                sensors.getData()

        states = []
        errors = []
        events = []
        
        while sensors.keepGoing:
            #Get data
            data = sensors.getNext(opts.timeInt)
            log("Data retrieved")

            #send data to RAVQ
            vec, errs = r.input(data, r.prevVec)[2:]
            log("Input processed: " + str(vec))

            states.append((r.newWinnerIndex, sensors.currTime))

            #Handle events - Check for both event types
            if r.newWinnerIndex != r.previousWinnerIndex:
                ev = Event(r.previousWinnerIndex, r.newWinnerIndex, vec, data[0].time, "state transition")
                if not r.eventState:
                    eventAlertTransition(ev)
                    r.eventState = True

                log("Potential event: " + str(ev))
                events.append(str(ev.prevState) + ", " + str(ev.newState) + ", " 
                         + str(ev.vector) + ", " + str(ev.time) + ", " + ev.reason + "\n")

            elif len(errs) > len(sensors)*opts.eventThreshold:
                ev = Event(r.previousWinnerIndex, r.newWinnerIndex, vec, data[0].time, "anomalous number of errors")
                if not r.eventState:
                    eventAlertAnomalous(ev)
                    r.eventState = True
                log("Potential event: " + str(ev))
                events.append(ev)
            
            elif len(errs) > 0: #Handle errors
                for e in errs:
                    log(str(e))
                    if not e.sensor.errorState:
                        errorAlert(e)
                        e.sensor.errorState = True
                    errors.append(e.sensor + ", " + str(e.time) + ", " + str(e.value) + ", " 
                               + e.flag + ", " + str(e.replace) + "\n")
           
            else:
                r.eventState = False
            log("Timestep complete.\n")

        signal.alarm(60*opts.refreshRate) #set next alarm
        log("Buffer emptied.\n\n")

        #Save stuff
        saveProgress(states, errors, events, sensors, r)

        #If it's a new day, archive files in S3
        if today[0] != datetime.date(datetime.now()) and not opts.test:
            for item in ["log", "ravq", "events", "errors", "states"]:
                #store in s3
                try: #exception handling in boto documentation is kind of vague
                    key = boto.s3.key.Key(bucket)
                    key.key = item+str(today)
                    key.set_contents_from_filename(item)
                    #clear old files
                    infile = open(item, "w+")
                    infile.write("")
                    infile.close()
                except Exception as e:
                    sendEmail("Received execption " + str(e), 
                      "Something went wrong in boto", "seaotternerd@gmail.com") 

            today[0] = datetime.date(datetime.now())
            print today, datetime.date(datetime.now())
    
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(1) #go off once at start-up
    while True:
        signal.pause() #process sleeps until alarm goes off

main()
