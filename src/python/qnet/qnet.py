import sys
import os
import numpy as np

def tf(string):  
    #converting string boolean values to true boolean type for parameter values
    if string == "False":
        return(False)
    elif string == "True":
        return(True)
    else:
        print("Bad boolean at: " + string)
        print("Defaulting to False")
        return(False)

class parameters:
    def __init__(self):
        #all parameter values
        self.ALL = ["SIMULATION_TIME", "TIME_RESOLUTION", "DRIVE_TIME", "DRIVE_DIST",
                    "EXOGENOUS_INTERARRIVAL", "SERVICE_TIME", "RENEGE_TIME", "NUM_SPOTS", 
                    "ROAD_NETWORK"]
        #If param file passes single float, float is diagonalized across a network matrix
        self.diagonalize = ["EXOGENOUS_INTERARRIVAL", "SERVICE_TIME", "RENEGE_TIME", "NUM_SPOTS"]

        #Simulator parameters
        self.SIMULATION_TIME = 1000.0
        self.TIME_RESOLUTION = 0.001

        #Network parameters
        self.EXOGENOUS_INTERARRIVAL = 1.5 
        self.SERVICE_TIME = 5.0
        self.SERVICE_RATE_DIST = "fixed" #distribution for service times, eg exponential or fixed
        self.RENEGE_TIME = 0.0
        self.NUM_SPOTS = 5
        self.DRIVE_TIME = 1.0
        self.DRIVE_DIST = "exponential" #distribution for drive times, eg exponential or fixed

        #Directed network topologies
        #Default network is 2-cycle
        self.ROAD_NETWORK = np.array([[0,1],
                                      [1,0]])
        self.networks = ["ROAD_NETWORK"] #list is hold over for multiple overlaid networks (parking garages)
        
    def read(self, inFilePath):
        #read parameter file
        inFile = open(inFilePath, 'r')
        lines = inFile.readlines()
        for line in lines:
            tokens = line.strip().split("=")
            if line[0] == "#" or line.strip() == "":
                pass
            elif tokens[1].strip()[0] == "/":
                try:
                    arr = np.loadtxt(tokens[1].strip(), dtype=np.dtype(float), delimiter = ",")
                    setattr(self, tokens[0].strip(), arr)
                except Exception as err:
                    print("Error reading parameter file path at line: ")
                    print(line)
                    print(err)
            elif tokens[1].strip()[0] == "T" or tokens[1].strip()[0] == "F":
                setattr(self, tokens[0].strip(), tf(tokens[1].strip()))
            else:
                try:
                    #float parameters
                    setattr(self, tokens[0].strip(), float(tokens[1].strip()))
                except:
                    #string parameters
                    setattr(self, tokens[0].strip(), tokens[1].strip())

        for att in self.diagonalize:
            if type(getattr(self, att)) != np.ndarray:
                setattr(self, att, getattr(self, att) * np.eye(self.ROAD_NETWORK.shape[1]))
            
    def write(self, outFilePath, ident):
        with open(outFilePath + "/" + ident + "_params.txt", 'w') as f:
            for att in self.ALL:
                if att in self.diagonalize:
                    f.write(att + " = " + outFilePath + "/" + ident + "_" + att + ".txt \n")
                    try:
                        np.savetxt(outFilePath + "/" + ident + "_" + att + ".txt", getattr(self, att), delimiter=",")
                    except:
                        out = getattr(self, att) * np.eye(self.ROAD_NETWORK.shape[1])
                        np.savetxt(outFilePath + "/" + ident + "_" + att + ".txt", out, delimiter=",")
                elif att in self.networks:
                    f.write(att + " = " + outFilePath + "/" + ident + "_" + att + ".txt \n")
                    np.savetxt(outFilePath + "/" + ident + "_" + att + ".txt", getattr(self, att), delimiter=",")
                else:
                    f.write(att + " = " + str(getattr(self, att)) + "\n")


       
class blockface:
    def __init__(self, index=False, lambd=1.0, mu=2.0, renege=0.0, num_spots=5, garage = False):
        self.i = index
        self.arrival_rate = lambd
        self.service_rate = mu
        self.renege_rate = renege
        self.num_parking_spots = num_spots
        self.spots = np.array([0.0 for j in range(int(num_spots))])
        self.neighbors = []
        self.neighbor_streets = {}
        if int(garage) == 1 or garage == True:
            self.garage = True
        else:
            self.garage = False
        
        #for calculating block face stats
        self.total = 0
        self.exogenous = 0
        self.served = 0
        self.avg_park_time = 0.0 #sanity check, should be service rate
        self.utilization = [] #records percent servers in use at regular time inervals
        self.num_in_service = [] #records total number of cars currently in service at regular time intervals
        self.queue_length = [] #looks at incoming roads
        self.isolated_rejects = 0
        self.parking_garage_rejects = 0
        self.last_reject_time = 0.0
        self.inter_reject_times = []

class street:
    def __init__(self, index, min_travel=1.0, max_travel=100.0):
        #index is (origin, dest) wrt whole newtork
        self.index = index
        self.weight = False
        #this is where I'll put some sort of parameters for the get_travel_time function below
        self.capacity = False
        self.min_travel_time = min_travel
        self.max_travel_time = max_travel
        #driver index and countdown timer tuple for arriving traffic at next blockface
        self.traffic = []
        #this is where I'm keeping track of the number of cars on the road at each stats time step
        self.volume = []
        
    def get_travel_time(self, block, dist="fixed", val=1.0):
        #want to reference parameter class
        if dist=="fixed":
            travelTime = val
        elif dist=="exponential":
            travelTime = np.random.exponential(val)
        elif dist=="interval":
            travelTime = self.min_travel_time
            if len(self.traffic) > block.num_parking_spots and len(self.traffic) < self.max_travel_time - block.num_parking_spots:
                travelTime += len(self.traffic)
            elif len(self.traffic) > block.num_parking_spots:
                travelTime = self.max_travel_time
        return(travelTime)
        
class car:
    def __init__(self, index, tracker=False):
        #use this to keep track of individual parkers
        self.index = index
        self.track_status = tracker
        self.service_times = []
        self.renege_times = []
        self.bfaces_attempted = []
        self.total_drive_time = 0.0

class blockfaceNet:
    def __init__(self, paramInstance, stats=[]):
        self.params = paramInstance
        num_blocks = self.params.ROAD_NETWORK.shape[1]
        self.stats = stats
        self.timer = 0.0
        self.bface = {}
        self.cars = {}
        self.carIndex = 0
        self.trakers = []
        #for plotting values over time
        self.clock = []
        self.measurement_increment = 1000.0 #sensor resolution (number of measurements)
        
        self.all_spots = []
        for ii in range(num_blocks):
            self.bface[ii] = blockface(index=ii, lambd=self.params.EXOGENOUS_RATE[ii,ii],
                                       mu=self.params.SERVICE_RATE[ii,ii], 
                                       renege=self.params.RENEGE_TIME[ii,ii], 
                                       num_spots = self.params.NUM_SPOTS[ii,ii], garage = self.params.GARAGE_NETWORK[ii,ii])
            neighboring_blocks = [ j for j, x in enumerate(self.params.ROAD_NETWORK[ii]) if x == 1 ]
            block_ids = [ i for i in range(len(neighboring_blocks)) ]
            self.bface[ii].neighbors = zip(block_ids, neighboring_blocks)
            
            #not sure if neighbor_streets is actively using the street class, it is, little convoluted though--polling street class for travel time in step time function
            for k in range(len(self.bface[ii].neighbors)):
                self.bface[ii].neighbor_streets[k] = street(index = (ii, self.bface[ii].neighbors[k][1]))

            self.all_spots.append(self.bface[ii].spots)
        
        self.streets = {}
        self.streets_traffic = {}
        
        for origin in range(num_blocks):
            #ideally I'd invoke a street class item here that has the below list, as well as the rest of the street class attributes
            #self.street_traffic is going to be a placeholder for the functionality I want
            self.streets[origin] = list()  
            self.streets_traffic[origin] = list()          
            for dest_n in range(len(self.bface[origin].neighbors)):
                self.streets[origin].append(self.bface[origin].neighbor_streets[dest_n].traffic)
                self.streets_traffic[origin].append(list())
                
        self.injection_b = np.diag(self.params.EXOGENOUS_RATE)
        injection_blocks = np.diag(self.params.EXOGENOUS_RATE)
        injection_block_indicies = [ i for i, x in enumerate(injection_blocks) if float(x) != 0.0 ]
        self.injection_map = {}
        for b in range(len(injection_block_indicies)):
            self.injection_map[b] = injection_block_indicies[b]
        self.new_arrival_timer = np.zeros(len(injection_block_indicies))
        
        self.total_flow = np.zeros(self.params.ROAD_NETWORK.shape)
        
        for ii in range(num_blocks):
            for k in range(len(self.bface[ii].neighbors)):
                if self.params.GARAGE_NEIGHBOR_EFFECT == True:
                    self.bface[self.bface[ii].neighbors[k][1]].garage = True
    
    def debug(self):
        #could pass class attribute name and then have it print all the values, that would be cool
        #current printing some street values
        print("self.streets: ")
        print(self.streets)
        print("\nself.streets[0]: ")
        print(self.streets[0])
        print("\nself.streets[0][0]: ")
        print(self.streets[0][0])
        
    def step_time(self, supress=False, debug=False):
        self.timer = self.timer + self.params.TIME_RESOLUTION  
        #countdowns
        self.new_arrival_timer = self.new_arrival_timer - self.params.TIME_RESOLUTION
        self.all_spots = [ (spots - self.params.TIME_RESOLUTION) for spots in self.all_spots ]
        for origin in self.streets.keys():
            for street in range(len(self.streets[origin])):
                if len(self.streets[origin][street]) > 0:
                    self.streets[origin][street] = [ (self.streets[origin][street][k][0], self.streets[origin][street][k][1] - self.params.TIME_RESOLUTION) for k in range(len(self.streets[origin][street])) ]
                else:
                    pass
        #print progress
        if supress == True:
            pass
        else:
            if self.timer % (self.params.SIMULATION_TIME / 10.0) <= self.params.TIME_RESOLUTION:
                print(str(int(self.timer / (self.params.SIMULATION_TIME/100))) + "% complete")
                
                if debug == True:
                    #can edit debug class to decide what to print
                    self.debug()
            
        if self.timer % (self.params.SIMULATION_TIME / self.measurement_increment) <= self.params.TIME_RESOLUTION:
            self.clock.append(self.timer)
        
            if "utilization" in self.stats:
                for block in self.bface.keys():
                    spots = float(self.bface[block].num_parking_spots)
                    parked = float(len([ i for i, x in enumerate(self.all_spots[block]) if x >  self.params.TIME_RESOLUTION ]))
                    self.bface[block].utilization.append(parked/spots)
                    
            if "stationary" in self.stats:
                for block in self.bface.keys():
                    parked = float(len([ i for i, x in enumerate(self.all_spots[block]) if x >  self.params.TIME_RESOLUTION ]))
                    self.bface[block].num_in_service.append(parked)

                    
            if "traffic" in self.stats:
                #individual street basis
                for origin in range(len(self.bface.keys())):
                    for street in range(len(self.streets[origin])):
                        traf = len(self.streets[origin][street])
                        self.streets_traffic[origin][street].append(traf)
        
            if "queue-length" in self.stats:
                #per block basis
                for block in self.streets.keys():
                    #incoming streets
                    num_streets = float(len(self.streets[block]))
                    total = 0.0
                    for strt in self.streets[block]:
                        total += float(len(strt))
                    avg_length = total/num_streets
                    self.bface[block].queue_length.append(avg_length)
                    
            if "rejection" in self.stats:
                #set default block to measure interrejection time
                pass
            
    def park(self, block, carIndex):
        self.bface[block].total += 1
        #no wait time at a block for the moment
        #available_spots = [ j for j, x in enumerate(self.all_spots[block]) if x <= self.bface[block].renege_rate + self.params.TIME_RESOLUTION ]
        available_spots = [ j for j, x in enumerate(self.all_spots[block]) if x <= self.params.TIME_RESOLUTION ]
        garageProb = np.random.uniform(0,1)
        if self.bface[block].garage == True and garageProb < self.params.GARAGE_PROB:
            self.bface[block].parking_garage_rejects += 1
        elif len(available_spots) > 0:
            if self.params.SERVICE_RATE_DIST == "fixed":
                car_park_time = self.bface[block].service_rate
            else:
                car_park_time = np.random.exponential(self.bface[block].service_rate)
            self.all_spots[block][available_spots[0]] = car_park_time
            self.bface[block].served += 1
        else:
            try:
                if "rejection" in self.stats:
                    #updating rejection time sensor and appending rejection times
                    last_reject = self.bface[block].last_reject_time
                    curr_time = self.timer
                    inter_reject = curr_time - last_reject
                    self.bface[block].inter_reject_times.append(inter_reject)
                    self.bface[block].last_reject_time = curr_time
                else:
                    pass
                newDest = self.bface[block].neighbors[np.random.choice([ i for i in range(len(self.bface[block].neighbors)) ])]
                newBface = newDest[1]
                newBfaceIndex = newDest[0]
                if self.params.DRIVE_DIST == "fixed":
                    drive_time = self.params.DRIVE_TIME
                else:
                    drive_time = self.bface[block].neighbor_streets[newBfaceIndex].get_travel_time(self.bface[newBface], dist=self.params.DRIVE_DIST, val = self.params.DRIVE_TIME)
                if self.params.BLOCKS_BEFORE_QUIT != 0.0:
                    if self.cars[carIndex].total_drive_time > self.params.BLOCKS_BEFORE_QUIT * self.params.DRIVE_TIME:
                        self.bface[block].parking_garage_rejects += 1
                    else:
                        self.cars[carIndex].total_drive_time += drive_time
                        self.total_flow[block, newBface] += 1
                        self.streets[block][newBfaceIndex].append((carIndex, drive_time))
                        self.streets[block][newBfaceIndex].sort(key = lambda t: t[1])
                else:
                    self.cars[carIndex].total_drive_time += drive_time
                    self.cars[carIndex].bfaces_attempted.append(block)
                    self.total_flow[block, newBface] += 1
                    self.streets[block][newBfaceIndex].append((carIndex, drive_time))
                    self.streets[block][newBfaceIndex].sort(key = lambda t: t[1])
            except Exception as err:
                print("Isolated reject error at blockface " + str(block))
                print(err)
                self.bface[block].isolated_rejects += 1
