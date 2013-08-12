#!/usr/bin/python

from realTimeSensorStreams import *
from ravq import *
from event import *
from math import sqrt, isnan
from optparse import OptionParser
from email.mime.text import MIMEText
from datetime import datetime
from boto.s3.lifecycle import Lifecycle, Rule, Transition
import os, sys, pickle, smtplib, signal, boto
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
    msg += "Is this really an error? Email Emily at EmilyLDolson@gmail.com and let her know."
    return sendEmail(msg, "Potential sensor error")

def eventAlertTransition(eve):
    """
    Sends a standardized transition event alert out to standard recipients.
    Input: eve - an event object to be reported on.
    Returns boolean indicating success
    """
    msg = "A potential rare event has been detected at " + str(eve.getTime()) + ".\n\n"
    msg += "The FoREST-cat algorithm has flagged this value as likely to be a rare event, rather than an error. This is just a prediction -"
    msg += " this value may, instead, be the result of an erorr. It's also possible that this event isn't particularly rare or interesting.\n\n"
    msg += "This potential event was flagged because of a change in category. This may be a shift into a rare category, or simply a shift"
    msg += " between two similar categories. Thus, it has a fairly high potential to not be interesting.\n\n"
    msg += "Is this really an error? If not, is this a useful event to be alerted to? Does it seem associated with a legitimate shift in the system?"
    msg += "Email Emily at EmilyLDolson@gmail.com and let her know."
    return sendEmail(msg, "EmilyLDolson@gmail.com", "Potential rare event")

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
    msg += "Is this really a bunch of errors? If not, is this a useful event to be alerted to? Email Emily at EmilyLDolson@gmail.com and let her know."
    return sendEmail(msg, "EmilyLDolson@gmail.com", "Potential rare event")

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

def exit_handler(signum, trace):
    """
    Handle exit smoothly
    """
    print "Thank you for using FoREST-Cat. Now exiting."
    log("Recieved exit command. Exiting...\n\n")
    exit(0)

def main():

    #Install exit handler - program will exit when it receives SIGINT
    signal.signal(signal.SIGINT, exit_handler)

    # Get command line aruments
    parser = OptionParser()
    parser.add_option("-t", "--timeInt", default = 15, action ="store", dest="timeInt", type= "float", help="The frequency with which to evaluate the current vector of the most recent data.")
    parser.add_option("-b", "--bufferSize", default=100, action="store", dest="bufferSize", type= "int", help="Buffer size for RAVQ")
    parser.add_option("-e", "--epsilon", default=1, action="store", dest="epsilon", type="float", help="Epsilon for RAVQ")
    parser.add_option("-d", "--delta", default=.9, action = "store", dest="delta", type= "float", help="Delta for RAVQ")
    parser.add_option("-s", "--historySize", default=2, dest="historySize", type= "int", help="History size for the RAVQ.")
    parser.add_option("-l", "--learningRate", action="store", default=.2, nargs=1, dest="learningRate", type= "float", help="Learning rate for the ARAVQ")
    parser.add_option("-c", "--checkid", action = "store", default="", dest="checkid", help="ID of checkpoint to save files under.")
    parser.add_option("-r", "--restart", action = "store_true", default=False, dest="restart", help="Restart from previous run?")
    (opts, args) = parser.parse_args()

    #Initialize ravq
    if opts.restart:
        print "Loading stored ravq from file..."
        r = loadFromFile("ravq") #default file for storing ravq
        if r == None:
            log("Failed to load RAVQ. Closing...")
            sendEmail("Failed to load RAVQ, FoREST-cat is closing.", 
                  "FoREST-cat load fail", "seaotternerd@gmail.com")
            exit()
        log("Loaded RAVQ")
    else:
        log("Generating new RAVQ...")
        r = ARAVQ(opts.bufferSize, opts.epsilon, opts.delta, 3, opts.historySize, opts.learningRate)
        log("RAVQ generated.")

    #Set up Amazon Web Services stuff
    s3Conn = boto.connect_s3()
    bucket = s3Conn.get_bucket("forest-cat")
    today = {0 : datetime.fromordinal(1)} #dictionary so it can modified in handler
    lifecycle = Lifecycle()
    for item in ["log", "ravq", "events", "errors", "states"]:
        #set rules for transition to Glacier
        to_glacier = Transition(days=7, storage_class = "GLACIER")
        rule = Rule(item+"Rule", item, "Enabled", transition = to_glacier)
        lifecycle.append(rule)
    bucket.configure_lifecycle(lifecycle)

    def alarm_handler(signum, frame):
        """
        This function will get called any time the alarm goes off.
        It is defined here so that it will have access to main() local
        variables. This supports an event-driven design.
        """
        
        signal.alarm(60*opts.timeInt) #set next alarm
        log("Starting processing...")

        #get data
        data = [1,2,3] #get this somehow
        log("Data retrieved")

        #send data to RAVQ
        vec, errs = r.input(data, r.prevVec)[2:]
        log("Input processed: " + str(vec))

        #Save state categorization
        if os.path.exists("states"):
            stateFile = open("states", "a")
            stateFile.write(str(r.newWinnerIndex) +"\n")
            stateFile.close()
        else:
            stateFile = open("states", "w+")
            stateFile.write(str(r.newWinnerIndex) +"\n")
            stateFile.close()

        #save RAVQ
        saveToFile("ravq", r)
        log("RAVQ stored. Handling events and errors.")

        #Send alerts
        if errs != None and errs != []:
            if os.path.exists("errors"):
                errorFile = open("errors", "a")
            else:
                errorFile = open("errors", "w+")
        
            for e in errs:
                log(str(e))
                errorAlert(e)
                if errorFile != None:
                    errorFile.write(e.sensor + ", " + str(e.time) + ", " + str(e.value) + ", " 
                           + e.flag + ", " + str(e.replace) + "\n")

            errorFile.close()

        #Handle events - Check for both event types
        if r.newWinnerIndex != r.previousWinnerIndex:
            ev = Event(r.previousWinnerIndex, r.newWinnerIndex, vec, now(), "state transition")
            eventAlertTransition(ev)
            log("Potential event: " + str(ev))
            if os.path.exists("events"):
                eventFile = open("events", "a")
            else:
                eventFile = open("events", "w+")
            eventFile.write(str(ev.prevState) + ", " + str(ev.newState) + ", " 
                     + str(ev.vector) + ", " + str(ev.time) + ", " + ev.reason + "\n")
            eventFile.close()

        elif errs == 1:
            ev = Event(states[i], states[i], vec, now(), "anomalous number of errors")
            eventAlertAnomaly(ev)
            log("Potential event: " + str(ev))
            if os.path.exists("events"):
                eventFile = open("events", "a")
            else:
                eventFile = open("events", "w+")
            eventFile.write(str(ev.prevState) + ", " + str(ev.newState) + ", " + 
                    str(ev.vector) + ", " + str(ev.time) + ", " + ev.reason + "\n")
            eventFile.close()

        log("Timestep complete.\n\n")

        #If it's a new day, archive files in S3
        if today[0] != datetime.date(datetime.now()):
            for item in ["log", "ravq", "events", "errors", "states"]:
                #store in s3
                try: #exception handling in boto documentation is kind of vaugue
                    key = boto.s3.key.Key(bucket)
                    key.key = item+str(today)
                    key.set_contents_from_filename(item)
                except Exception as e:
                    sendEmail("Received execption " + str(e), 
                      "Something went wrong in boto", "seaotternerd@gmail.com")  

                #clear old files
                infile = open(item, "w+")
                infile.write("")
                infile.close()

            today[0] = datetime.date(datetime.now())
            print today, datetime.date(datetime.now())
    
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(1) #go off once at start-up
    while True:
        signal.pause() #process sleeps until alarm goes off

main()
