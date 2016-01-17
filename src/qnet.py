import numpy as np
import scipy as sp

class blockfaceNet:
    def __init__(self, adjacency):
        self.network = adjacency
        self.bface = {}
        self.carNumber = 0
        for i in range(adjacency.shape[1]):
            self.bface[i] = blockface()
        #list of parking arrays to keep service times synchronized
        self.allSpots = [self.bface[i].spots for i in range(adjacency.shape[i])]
        #can do the same for injections but requires additional input
        
        #for calculating network stats
        #not symmetric, flow assumed to be from row index to column index
        self.totalFlow = np.zeros(self.network.shape)
        
class blockface:
    def __init__(self, index=False, lambd=1.0, mu=5.0, renege_rate=1.0, num_spots=5):
        self.i = index
        self.arrival_rate = lambd
        self.service_rate = mu
        self.renege_rate = renege_rate
        self.queue = {}
        self.num_parking_spots = num_spots
        self.spots = np.array([0.0 for j in range(num_spots)])
        #spot needs to be assigned serve time
            
        #for calculating block face stats
        self.total = 0
        self.served = 0
        self.avg_park_time = 0.0
        self.utilization = 0.0
        
class car:
    def __init__(self, service_time, renege_time):
        #use this to keep track of individual parkers
        self.service_time = service_time
        self.renege_time = renege_time
        self.bfacesAttempted = []

