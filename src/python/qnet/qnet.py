import numpy as np

class parameters:
    def __init__(self, inFilePath):
        #Global parameters
        self.SIMULATION_TIME = 1000.0
        self.TIME_RESOLUTION = 0.001
        self.DRIVE_TIME = 1.0
        self.BLOCKS_BEFORE_QUIT = 0.0
        self.GARAGE_PROB = 0.0
        self.GARAGE_NEIGHBOR_EFFECT = False
        
        #Network parameters
        self.EXOGENOUS_RATE = 1.5 
        self.SERVICE_RATE = 5.0
        self.RENEGE_TIME = 0.0
        self.NUM_SPOTS = 5
        #If param file passes single float, float is diagonalized across a network
        #matrix--not efficient use of memory but helps with later steady state computation
        self.diagonalize = ["EXOGENOUS_RATE", "SERVICE_RATE", "RENEGE_TIME", "NUM_SPOTS"]
        
        self.ROAD_NETWORK = ""
        self.GARAGE_NETWORK = ""

        #read parameter file
        try:
            inFile = open(inFilePath, 'r')
            lines = inFile.readlines()
            for line in lines:
                tokens = line.strip().split("=")
                if line[0] == "#" or line.strip() == "":
                    pass
                elif tokens[1].strip()[0] == "/":
                    arr = np.loadtxt(tokens[1].strip(), dtype=np.dtype(float), delimiter = ",")
                    setattr(self, tokens[0].strip(), arr)
                else:
                    setattr(self, tokens[0].strip(), float(tokens[1].strip()))
            for att in self.diagonalize:
                if type(getattr(self, att)) != np.ndarray:
                    setattr(self, att, getattr(self, att) * np.eye(self.ROAD_NETWORK.shape[1]))
        except Exception as err:
            print("Could not read parameter file.")
            print(err)

        if self.GARAGE_NETWORK == "":
            self.GARAGE_NETWORK = np.zeros(self.ROAD_NETWORK.shape)
       
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
        self.avg_park_time = 0.0
        self.utilization = []
        self.queue_length = []
        self.isolated_rejects = 0
        self.parking_garage_rejects = 0

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
        
        self.all_spots = []
        for ii in range(num_blocks):
            self.bface[ii] = blockface(index=ii, lambd=self.params.EXOGENOUS_RATE[ii,ii],
                                       mu=self.params.SERVICE_RATE[ii,ii], 
                                       renege=self.params.RENEGE_TIME[ii,ii], 
                                       num_spots = self.params.NUM_SPOTS[ii,ii], garage = self.params.GARAGE_NETWORK[ii,ii])
            neighboring_blocks = [ j for j, x in enumerate(self.params.ROAD_NETWORK[ii]) if x == 1 ]
            block_ids = [ i for i in range(len(neighboring_blocks)) ]
            self.bface[ii].neighbors = zip(block_ids, neighboring_blocks)
            
            for k in range(len(self.bface[ii].neighbors)):
                self.bface[ii].neighbor_streets[k] = street(index = (ii, self.bface[ii].neighbors[k][1]))

            self.all_spots.append(self.bface[ii].spots)
        
        self.streets = {}
        for origin in range(num_blocks):
            self.streets[origin] = list()
            for dest_n in range(len(self.bface[origin].neighbors)):
                self.streets[origin].append(self.bface[origin].neighbor_streets[dest_n].traffic)
                
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
                if self.params.GARAGE_NEIGHBOR_EFFECT == 1.0:
                    self.bface[self.bface[ii].neighbors[k][1]].garage = True
        
    def step_time(self, supress=False):
        self.timer = self.timer + self.params.TIME_RESOLUTION  
        #countdowns
        self.new_arrival_timer = self.new_arrival_timer - self.params.TIME_RESOLUTION
        self.all_spots = [ (spots - self.params.TIME_RESOLUTION) for spots in self.all_spots ]
        for origin in self.streets.keys():
            for street in range(len(self.streets[origin])):
                if len(self.streets[origin][street]) > 0:
                    self.streets[origin][street] = [ (self.streets[origin][street][k][0], self.streets[origin][street][k][1] - self.params.TIME_RESOLUTION) for k in range(len(self.streets[origin][street])) ]
                else:
                    #self.streets[origin][street] = list()
                    pass
        #print progress
        if supress == True:
            pass
        else:
            if self.timer % (self.params.SIMULATION_TIME / 10) <= self.params.TIME_RESOLUTION:
                print(str(int(self.timer / (self.params.SIMULATION_TIME/100))) + "% complete")
            
        if "utilization" in self.stats:
            if self.timer % (self.params.SIMULATION_TIME / 100) <= self.params.TIME_RESOLUTION:
                for block in self.bface.keys():
                    spots = float(self.bface[block].num_parking_spots)
                    parked = float(len([ i for i, x in enumerate(self.all_spots[block]) if x >  self.params.TIME_RESOLUTION ]))
                    self.bface[block].utilization.append(parked/spots)
        
        if "queue-length" in self.stats:
            if self.timer % (self.params.SIMULATION_TIME / 100) <= self.params.TIME_RESOLUTION:
                for block in self.streets.keys():
                    #incoming streets
                    num_streets = float(len(self.streets[block]))
                    total = 0.0
                    for strt in self.streets[block]:
                        total += float(len(strt))
                    avg_length = total/num_streets
                    self.bface[block].queue_length.append(avg_length)
            
    def park(self, block, carIndex):
        self.bface[block].total += 1
        #no wait time at a block for the moment
        #available_spots = [ j for j, x in enumerate(self.all_spots[block]) if x <= self.bface[block].renege_rate + self.params.TIME_RESOLUTION ]
        available_spots = [ j for j, x in enumerate(self.all_spots[block]) if x <= self.params.TIME_RESOLUTION ]
        garageProb = np.random.uniform(0,1)
        if self.bface[block].garage == True and garageProb < self.params.GARAGE_PROB:
            self.bface[block].parking_garage_rejects += 1
        elif len(available_spots) > 0:
            car_park_time = np.random.exponential(self.bface[block].service_rate)
            self.all_spots[block][available_spots[0]] = car_park_time
            self.bface[block].served += 1
        else:
            try:
                newDest = self.bface[block].neighbors[np.random.choice([ i for i in range(len(self.bface[block].neighbors)) ])]
                newBface = newDest[1]
                newBfaceIndex = newDest[0]
                drive_time = self.bface[block].neighbor_streets[newBfaceIndex].get_travel_time(self.bface[newBface], dist="exponential", val = self.params.DRIVE_TIME)
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
                    self.total_flow[block, newBface] += 1
                    self.streets[block][newBfaceIndex].append((carIndex, drive_time))
                    self.streets[block][newBfaceIndex].sort(key = lambda t: t[1])
            except Exception as err:
                print("isolated reject error at blockface " + str(block))
                print(err)
                self.bface[block].isolated_rejects += 1
