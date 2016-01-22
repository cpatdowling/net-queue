import sys
import numpy as np

class parameters:
    def __init__(self, inFilePath):
        #accepts a filepath to a parameter file or a dictionary
        #of parameters directly--these values must be specified
        #carefully to reflect value types below, i.e. np.array or float
        self.lambd = 1.0
        self.mu = 5.0
        self.renege_rate= 0.0
        self.drive_time = 1.0
        self.num_spots = 5
        self.simulation_time = 1000
        self.time_resolution = 0.001
        self.injections = ""
        self.adjacency = ""
        self.paramMap = {"SIMULATION_TIME": "simulation_time", "DELTA_T": "time_resolution",
                         "ARRIVAL_RATE": "lambd", "SERVICE_RATE": "mu", "RENEGE_TIME": "renege_rate",
                         "NUM_SERVERS": "num_spots", "ROAD_NETWORK": "adjacency", "EXOGENOUS_ARRIVALS": "injections"}
        if type(inFilePath) == str:
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
        else:
            paramDict = inFilePath
            for key in paramDict:
                try:
                    setattr(self, key, paramDict[key])
                except:
                    print("Inputing param dict, key not found: " + key)
            
        
        #reevalute when doing different kinds of blockfaces
        self.blockface_params = [self.lambd, self.mu, self.renege_rate, self.num_spots]

class blockfaceNet:
    def __init__(self, paramInstance, stats = []):
        # I want to create a param instance outside of a blockfaceNet instance
        #and pass it into blockfaceNet as an argument, that will allow me to edit
        #the param instance beforehand if looping through values
        self.params = paramInstance
        self.stats = stats
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
                self.bface[i] = blockface(index=i, lambd=self.params.lambd, mu=self.params.mu, 
                                          renege_rate=self.params.renege_rate, num_spots=self.params.num_spots)
                self.bface[i].neighbors = [ j for j, x in enumerate(self.network[i]) if x == 1 ]
                for k in range(len(self.bface[i].neighbors)):
                    self.bface[i].neighbor_streets[k] = streetlane(index = (i, self.bface[i].neighbors[k]))
        
        #list of parking arrays to keep service times synchronized
        self.allSpots = [self.bface[i].spots for i in range(self.network.shape[0])]
        
        #list of street arrays for people who quit, keep travel times synchronized
        self.streets = {}
        for origin in range(self.network.shape[0]):
            self.streets[origin] = list()
            for n in range(len(self.bface[origin].neighbors)):
                dest = self.bface[origin].neighbors[n]
                self.streets[origin].append(self.bface[origin].neighbor_streets[n].traffic)
        
        #creating timer and indexing injection blocks
        injection_blocks = np.diag(self.injections)
        injection_block_indices = [ i for i, x in enumerate(injection_blocks) if x == 1 ]
        self.injection_map = {}
        for b in range(len(injection_block_indices)):
            self.injection_map[b] = injection_block_indices[b]
        self.new_arrivals = np.zeros((1,len(injection_block_indices)))
        self.timer = 0.0
        
        #for calculating network stats
        #not symmetric, flow assumed to be from row index to column index
        self.totalFlow = np.zeros(self.network.shape)
        
    def step_time(self):
        self.timer = self.timer + self.params.time_resolution
        #countdown on next exogenous arrival
        self.new_arrivals = self.new_arrivals - self.params.time_resolution
        #countdown on serve times
        self.allSpots = [ (spots - self.params.time_resolution) for spots in self.allSpots ]
        #countdown on inter blockface arrival
        for origin in self.streets.keys():
            self.streets[origin] = [ list((np.array(dest) - self.params.time_resolution)) for dest in self.streets[origin] ]
        
        #print progress
        if self.timer % (self.params.simulation_time / 10) <= self.params.time_resolution:
            print(str(int(self.timer / (self.params.simulation_time/100))) + "% complete")
            
        if "utilization" in self.stats:
            #update utilization stats
            #lower time resolution to save time
            if self.timer % (self.params.simulation_time / 100) <= self.params.time_resolution:
                for block in self.bface.keys():
                    spots = float(self.bface[block].num_parking_spots)
                    parked = float(len([ i for i, x in enumerate(self.allSpots[block]) if x > 0.0 ]))
                    self.bface[block].utilization.append(parked/spots)
    
    def park(self, destblock):
        #attempt to snag parking at a destination blockface
        self.bface[destblock].total += 1
        currently_available_spots = [ j for j, x in enumerate(self.allSpots[destblock]) if x <= self.bface[destblock].renege_rate  ]
        if len(currently_available_spots) > 0:
            #parking available, choose the first available spot
            car_park_time = np.random.exponential(self.bface[destblock].service_rate)  
            self.allSpots[destblock][currently_available_spots[0]] = car_park_time
            self.bface[destblock].served += 1
        else:
            #car moves to different blockface--uniformly sample from neighbors
            newBface = np.random.choice(self.bface[destblock].neighbors)
            newBfaceIndex = np.where(self.bface[destblock].neighbors == newBface)[0][0]
            self.totalFlow[destblock,newBface] += 1
            if len(self.streets[destblock][newBfaceIndex]) > self.params.simulation_time * self.params.lambd * 10:
                print("shits blowing up")
                #raise self.overflow
            else:
                self.streets[destblock][newBfaceIndex].append(self.params.drive_time)
    
    def overflow(Exception):
        print("\n==Exception==")
        print("Traffic overflow at simulation time: " + str(self.timer))
        print("Total flow: ")
        print(self.totalFlow)

        
class blockface:
    def __init__(self, index=False, lambd=1.0, mu=2.0, renege_rate=.5, num_spots=5):
        self.i = index
        self.arrival_rate = lambd
        self.service_rate = mu
        self.renege_rate = renege_rate
        self.queue = {}
        self.num_parking_spots = num_spots
        #this attribute is dormant, all updates are made to blockfaceNet.allSpots, but
        #self.spots is used to construct allSpots for different sized blockfaces
        self.spots = np.array([0.0 for j in range(int(num_spots))])
        self.neighbors = []
        self.neighbor_streets = {}
        
        #for calculating block face stats
        self.total = 0
        self.exogenous = 0
        self.served = 0
        self.avg_park_time = 0.0
        self.utilization = []

            
class streetlane:
    def __init__(self, index):
        #index is (origin, dest) wrt whole newtork
        self.index = index
        self.weight = False
        #countdown timer for arriving traffic at next blockface
        self.traffic = []

class car:
    def __init__(self, service_time, renege_time):
        #use this to keep track of individual parkers
        #probably gonna slow stuff down pretty quick
        self.service_time = service_time
        self.renege_time = renege_time
        self.bfacesAttempted = []

