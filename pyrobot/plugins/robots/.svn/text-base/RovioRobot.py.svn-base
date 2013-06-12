from pyrobot.robot.rovio import RovioRobot
from pyrobot.system.share import ask

def INIT():
    dict = ask("Which Rovio do you wish to connect to?",
               [("Rovio IP/URL", "")])
    return RovioRobot(dict["Rovio IP/URL"]) 
