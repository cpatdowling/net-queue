import sys
import os
import numpy as np

#helper functions

def tf(string): #for boolean parameter values
    if string == "False":
        return(False)
    elif string == "True":
        return(True)
    else:
        print("Bad boolean at: " + string)
        print("Defaulting to False")
        return(False)

def sample_dist(distname, distparams):
    #distribution types are encoded in class objects, this function
    #samples accordingly
    if distname == "fixed":
        val = distparams
    elif distname == "exponential":
        val = np.random.exponential(distparams)
    elif distname == "uniform":
        val = np.random.uniform(distparams[0], distparams[1])
    else:
        print("sample_dist (helper) error, distribution type not known.")
        print(distname)
        val = False
    return(val)

class parameters:
    def __init__(self):
        #all parameter values
        self.ALL = ["SIMULATION_TIME", "TIME_RESOLUTION", "DRIVE_TIME_DIST", "DRIVE_TIME_DIST",
                    "EXOGENOUS_INTERARRIVAL", "SERVICE_TIME_DIST", "RENEGE_TIME", "NUM_SPOTS", 
                    "ROAD_NETWORK", "VERBOSE"]
        #If param file passes single float, float is diagonalized across a network matrix
        self.diagonalize = ["EXOGENOUS_INTERARRIVAL", "SERVICE_TIME", "RENEGE_TIME", "NUM_SPOTS"]

        #Simulator parameters
        self.SIMULATION_TIME = 1000.0
        self.TIME_RESOLUTION = 0.001
        self.VERBOSE = True
        
        #Simulator statistics to collect, list of keywords
        self.STATS = [] 
            #"occupancy": measures proportion of servers in use at given time intervals
            #"stationary": collects data to estimate stationary distribution of queues
            #"interrejection": collects data to determine interreject time distribution for queue
            #"traffic": collects data on the number of cars on each street

        #Network parameters
        self.EXOGENOUS_INTERARRIVAL = 1.5 
        self.SERVICE_TIME = 5.0
        self.SERVICE_TIME_DIST = "fixed" #distribution for service times, eg exponential or fixed
        self.RENEGE_TIME = 0.0           #amount of time driver will spend before quitting: not implemented
        self.NUM_SPOTS = 5
        self.DRIVE_TIME = 1.0
        self.DRIVE_TIME_DIST = "exponential" #distribution for drive times, eg exponential or fixed

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
        with open(outFilePath + "/" + ident + "_PARAMS.txt", 'w') as f:
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


class nqueue: #this queue class serves as the queue type for both streets and blockfaces
    def __init__(self, category, index, paramsInst):
        self.INDEX = index
        self.CATEGORY = category
        self.TIME_RESOLUTION = paramsInst.TIME_RESOLUTION
        self.ERR_LOG = {} #key is car index, val is error message
        if category == "blockface":
            self.EXOGENOUS_INTERARRIVAL = paramsInst.EXOGENOUS_INTERARRIVAL
            self.SERVICE_TIME = paramsInst.SERVICE_TIME[index, index]
            self.SERVICE_TIME_DIST = paramsInst.SERVICE_TIME_DIST
            self.NUM_SPOTS = paramsInst.NUM_SPOTS[index, index]
            self.ACTIVE_SERVERS = np.zeros((int(self.NUM_SPOTS),))
            self.NEIGHBORING_BLOCKS = []
            
            #statistics
            self.TOTAL = 0
            self.SERVED = 0
            self.EXOGENOUS_ARRIVALS = 0
            self.LAST_REJECT_TIME = 0.0
        
            #stats requiring multiple measurements
            self.OCCUPANCY = []
            self.STATIONARY = []
            self.INTERREJECTION_TIMES = []
            
        elif category == "street":
            self.ORIGIN = index[0]
            self.DESTINATION = index[1]
            self.SERVICE_TIME = paramsInst.DRIVE_TIME
            self.SERVICE_TIME_DIST = paramsInst.DRIVE_TIME_DIST
            self.NUM_SPOTS = np.inf #infinite server queue
            self.ACTIVE_SERVERS = np.zeros((20,)) #assuming a likely maximum capacity, 
                                     #will dynamically expand if needed
            
            #statistics
            self.TOTAL = 0
            
            #stats with multiple measurements
            self.TRAFFIC = []   #number of vehicles currently on road per measurement
        
        else:
            category == "garage" #empty category for now
            print("Unprototyped nqueue category: garage")
            pass
        
    def get_service_time(self):
        service_time = sample_dist(self.SERVICE_TIME_DIST, self.SERVICE_TIME)
        return(service_time)
    
    def get_num_in_service(self):
        num = self.ACTIVE_SERVERS[self.ACTIVE_SERVERS > self.TIME_RESOLUTION].shape[0]
        return(num)
    
    def get_available_servers(self):
        #for determining availability in finite capacity queues
        available = [ j for j, x in enumerate(self.ACTIVE_SERVERS) if x <= self.TIME_RESOLUTION ]
        if self.CATEGORY == "street" and len(available) == 0:
            new_server_array = np.concatenate( (self.ACTIVE_SERVERS, np.zeros((1,))), axis=0)
            self.ACTIVE_SERVERS = new_server_array
            available = [self.ACTIVE_SERVERS.shape[0] - 1]
        return(available)
    
    def get_neighbor_block(self, carInst):
        #asks car instance for search strategy
        newDest = carInst.choose_next_block(self.NEIGHBORING_BLOCKS)
        if newDest == False:
            print("Isolated rejection occured at block-face: " + str(self.INDEX))
        return(newDest)
    
    def new_car(self, carInst, current_time):
        #update global stats
        self.TOTAL += 1
        
        #update servers
        stime = self.get_service_time()
        available_servers = self.get_available_servers()
        self.ACTIVE_SERVERS[available_servers[0]] = stime
        
        if self.CATEGORY == "street":
            #update car stats
            carInst.BLOCK_TIMES.append(current_time)
            carInst.BLOCKS_ATTEMPTED.append(self.ORIGIN)
            carInst.TOTAL_DRIVE_TIME += stime
            
            #update street stats
        
        elif self.CATEGORY == "blockface":
            #update car stats
            carInst.BLOCKS_ATTEMPTED.append(self.INDEX)
            carInst.SERVICE_TIME = stime
            carInst.EXIT_TIME = stime + current_time
            
            #update blockface stats
            self.SERVED += 1
        
        elif self.CATEGORY == "garage":
            pass

class car:
    def __init__(self, index, tracker=False):
        self.INDEX = index
        self.TRACK_STATUS = tracker
        self.ARRIVAL_TIME = 0.0 #simulation time when a car arrived to the network
        self.EXIT_TIME = 0.0    #simulation time when a car exited the network
        self.SERVICE_TIME = 0.0 #how long the car parked for
        self.RENEGE_TIME = 0.0  #how long before a car eventually quit
        self.BLOCK_TIMES = [] #simulation times at which a car was blocked
        self.BLOCKS_ATTEMPTED = [] #indecies of blocks the car attempted to park at, including the successful block
        self.TOTAL_DRIVE_TIME = 0.0 #how long the car spent driving
        self.SEARCH_STRATEGY = "uniform" #develop search strategy here, so next block can be chosen from queue class
                                         #according to this search strategy
            
    def choose_next_block(neighbors):
        #choose from list of integers, neighbors, next block
        if len(neighbors) == 0:
            print("Isolated rejection at network boundary (no out-degree neighbors)")
            next_block = False
        if self.SEARCH_STRATEGY == "uniform":
            next_block = np.random.choice(neighbors)
        return(next_block)

class blockfaceNet:
    def __init__(self, paramInstance, stats=[]):
        self.PARAMS = paramInstance
        self.PARAMS.STATS = stats
        self.TIMER = 0.0
        self.STOPWATCH = []
        self.NUM_MEASUREMENTS = 1000.0 #number of measurements for in situ sensors
        
        num_blocks = self.PARAMS.ROAD_NETWORK.shape[1]
        self.BLOCKFACES = {}
        for ii in range(num_blocks):
            self.BLOCKFACES[ii] = nqueue("blockface", ii, self.PARAMS)
            neighboring_blocks = [ j for j, x in enumerate(self.PARAMS.ROAD_NETWORK[ii,:]) if x == 1 ]
            self.BLOCKFACES[ii].NEIGHBORING_BLOCKS = neighboring_blocks
        
        #new arrival timer        
        arrival_times = np.diag(self.PARAMS.EXOGENOUS_INTERARRIVAL)
        self.INJECTION_BLOCKS = [ i for i, x in enumerate(arrival_times) if float(x) != 0.0 ]
        self.NEW_ARRIVAL_TIMER = np.zeros((len(self.INJECTION_BLOCKS),))
        for bi in range(len(self.INJECTION_BLOCKS)):
            curr = self.INJECTION_BLOCKS[bi]
            inittime = self.BLOCKFACES[curr].get_service_time()
            self.NEW_ARRIVAL_TIMER[bi] = inittime   
        
        self.STREETS = {} #key is origin blockface, value is dict of streets with 
                          #destinations by key
        for origin in range(num_blocks):
            self.STREETS[origin] = {}
            for dest_n in self.BLOCKFACES[origin].NEIGHBORING_BLOCKS:
                self.STREETS[origin][dest_n] = nqueue("street", (origin,dest_n), self.PARAMS)
                
        self.CARS = {} #index keys to car object values, keeps track of all arrivals to system
    
    def step_time(self):
        self.TIMER += self.PARAMS.TIME_RESOLUTION
        #countdowns
        for block in self.BLOCKFACES.keys():
            self.BLOCKFACES[block].ACTIVE_SERVERS -= self.PARAMS.TIME_RESOLUTION
            for st in self.STREETS[block]: #streets originating from the current block
                self.STREETS[block][st].ACTIVE_SERVERS -= self.PARAMS.TIME_RESOLUTION
                
        if self.TIMER % (self.PARAMS.SIMULATION_TIME / 10) <= self.PARAMS.TIME_RESOLUTION:
            if self.PARAMS.VERBOSE == True:
                print(str(int(self.TIMER / (self.PARAMS.SIMULATION_TIME/100))) + "% complete")
        
        #sensor measurements
        if self.TIMER % (self.PARAMS.SIMULATION_TIME / self.NUM_MEASUREMENTS) <= self.PARAMS.TIME_RESOLUTION:
            self.STOPWATCH.append(self.TIMER)
            self.collect_timer_stats()
            
            
    def collect_timer_stats(self):
        #stats collected at times recorded by self.STOPWATCH, to few to bother with options function
        if "occupancy" in self.PARAMS.STATS:
            self.update_occupancy()
                
        if "stationary" in self.PARAMS.STATS:
            self.update_stationary()
            
        if "traffic" in self.PARAMS.STATS:
            self.update_traffic()
            
    #simulation statistics for blockfaces
    #STOPWATCH determined statistics
    def update_occupancy(self):
        for block in self.BLOCKFACES.keys():
            spots = float(self.BLOCKFACES[block].NUM_SPOTS)
            parked = float(self.BLOCKFACES[block].get_num_in_service())
            self.BLOCKFACES[block].OCCUPANCY.append(parked/spots)
            
    def update_stationary(self):
        for block in self.BLOCKFACES.keys():
            parked = float(self.BLOCKFACES[block].get_num_in_service())
            self.BLOCKFACES[block].STATIONARY.append(parked)
            
    def update_traffic(self):
        for src in self.STREETS.keys():
            for dest in self.STREETS[src].keys():
                traff = float(self.STREETS[src][dest].get_num_in_service())
                self.STREETS[src][dest].TRAFFIC.append(traff)
    
    #event determined statistics (measured when it happens)
    def update_interrejection(self, block):
        #updating rejection time sensor and appending rejection times
        last_reject = self.BLOCKFACE[block].LAST_REJECT_TIME
        inter_reject = self.TIMER - last_reject
        self.BLOCKFACE[block].INTERREJECTION_TIMES.append(inter_reject)
        self.BLOCKFACE[block].LAST_REJECT_TIME = self.TIMER
    
    def park(self, block, carIndex):
        available_spots = self.BLOCKFACES[block].get_available_servers()        
        if len(available_spots) > 0:
            self.BLOCKFACES[block].new_car(self.CARS[carIndex], self.TIMER) #update queue with new car
        else:
            if "interrejection" in self.PARAMS.STATS:
                self.update_interrejection(block)
            try:
                next_blockface = self.BLOCKFACES[block].get_neighbor_block(self.CARS[carIndex]) #takes car as argument for search strategy
                self.STREETS[block][next_blockface].new_car(self.CARS[carIndex], self.TIMER) #update queue with new car
            except Exception as err:
                print("Isolated reject error at blockface " + str(block))
                print(err)
                self.BLOCKFACES[block].ERR_LOG[carIndex] = err

