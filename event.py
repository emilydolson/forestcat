class Event():
    def __init__(self, prevState, newState, vector, timestep):
        self.prevState = prevState
        self.newState = newState
        self.vector = vector
        self.timestep = timestep
        
    def __str__(self):
        return str(self.prevState) + " -> " + str(self.newState) + ": " + str(self.timestep)
