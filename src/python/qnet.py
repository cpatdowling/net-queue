import sys
import os
import numpy as np

class blockfaceNet:
    def __init__(self, paramFilePath):
        self.params = parameters(paramFilePath)
        self.network = self.params.adjacency
        self.injections = self.params.injections
        self.bface = {}
        if any([type(a) == np.ndarray for a in self.params.blockface_params]):
            #one of the blockface params is a diagonal array       
            for i in range(self.network.shape[1]):
                print("haven't implemented individual block parameters yet")
                break
        else:
            #otherwise, blockfaces look the same
            for i in range(self.network.shape[1]):
                self.bface[i] = blockface(index=i, lambd=self.params.lambd, mu=self.params.mu, renege_rate=self.params.renege_rate, num_spots=self.params.num_spots)
        #list of parking arrays to keep service times synchronized
        self.allSpots = [self.bface[i].spots for i in range(self.network.shape[0])]
        #can do the same for injections but requires additional input
        
        #for calculating network stats
        #not symmetric, flow assumed to be from row index to column index
        self.totalFlow = np.zeros(self.network.shape)
        
        #creating timer and indexing injection blocks
        injection_blocks = np.diag(self.injections)
        injection_block_indices = [ i for i, x in enumerate(injection_blocks) if x == 1 ]
        self.injection_map = {}
        for b in range(len(injection_block_indices)):
            self.injection_map[b] = injection_block_indices[b]
        self.new_arrivals = np.zeros((1,len(injection_block_indices)))
        
class parameters:
    #going to want this is I want variation in blockfaces
    def __init__(self, inFilePath):
        self.lambd = 1.0
        self.mu = 5.0
        self.renege_rate= 0.5
        self.num_spots = 5
        self.simulation_time = 1000
        self.time_resolution = 0.001
        self.injections = ""
        self.adjacency = ""
        self.paramMap = {"SIMULATION_TIME": "simulation_time", "DELTA_T": "time_resolution", "ARRIVAL_RATE": "lambd", "SERVICE_RATE": "mu", "RENEGE_TIME": "renege_rate", "NUM_SERVERS": "num_spots", "ROAD_NETWORK": "adjacency", "EXOGENOUS_ARRIVALS": "injections"}
        try:
            inFile = open(inFilePath, 'r')
            lines = inFile.readlines()
            inFile.close()
            for line in lines:
                tokens = line.strip().split("=")
                if line[0] == "#" or line.strip() == "":
                    pass
                elif tokens[0].strip() in self.paramMap.keys():
                    if tokens[0].strip() == "ROAD_NETWORK" or tokens[0].strip() == "INJECTIONS":
                        arr = np.loadtxt(tokens[1].strip(), dtype=np.dtype(int), delimiter=",")
                        setattr(self, self.paramMap[tokens[0].strip()], arr)
                    elif tokens[1].strip()[0] == "/":
                        #parameter is a filepath
                        arr = np.loadtxt(tokens[1].strip(), dtype=np.dtype(float), delimiter=",")
                        setattr(self, self.paramMap[tokens[0].strip()], arr)
                    else:
                        setattr(self, self.paramMap[tokens[0].strip()], float(tokens[1].strip()))
        except Exception as err:
            print("Could not read parameter file:")
            print(err)
        self.blockface_params = [self.lambd, self.mu, self.renege_rate, self.num_spots]
        
class blockface:
    def __init__(self, index=False, lambd=1.0, mu=2.0, renege_rate=.5, num_spots=5):
        self.i = index
        self.arrival_rate = lambd
        self.service_rate = mu
        self.renege_rate = renege_rate
        self.queue = {}
        self.num_parking_spots = num_spots
        self.spots = np.array([0.0 for j in range(int(num_spots))])
        #spot needs to be assigned serve time
            
        #for calculating block face stats
        self.total = 0
        self.exogenous = 0
        self.served = 0
        self.avg_park_time = 0.0
        self.utilization = 0.0
        
class car:
    def __init__(self, service_time, renege_time):
        #use this to keep track of individual parkers
        #probably gonna slow stuff down pretty quick
        self.service_time = service_time
        self.renege_time = renege_time
        self.bfacesAttempted = []
