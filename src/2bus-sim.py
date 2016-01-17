from qnet import *

#simulation variables
SIMULATION_TIME = 1000.0
deltaT = 0.001

#Adjacency of roads
ROAD_NETWORK = np.array([[0,1],
                        [1,0]])
#Nodes which have their own exogenous arrival rate
INJECTIONS = np.array([[1,0],
                       [0,1]])
ARRIVAL_RATE = 1.0
SERVICE_RATE = 2.0
RENEGE_TIME = 0.5
NUM_SERVERS = 5 #currently not used--block faces fixed at 5
    
QNet = blockfaceNet(ROAD_NETWORK)

#keep track of exogenous arrivals, needs to be as long as non-zero injections array
#probably want to make this a diagonal matrix at some point, so at time t it's
#a weighting of the injections matrix
new_arrivals = np.array([0.0,0.0])

#keeping track of people moving from one blockface to next
#key is destination blockface index, value is null for now, could be fixed patience, could be ind. quitter stats
quitters = {}
for bface in QNet.bface.keys():
    quitters[bface] = 0
nextStepQuitters = quitters

t = 0.0
while t < SIMULATION_TIME:
    #find block numbers of blocks with <=0.0 time till next arrival
    #can use itertools.compress on new arrivals list comprehension
    currently_arriving_blocks = [ i for i, x in enumerate(new_arrivals) if x <= 0.0 ]
    if len(currently_arriving_blocks) > 0:
        #give arriving blocks new arrivals
        #prioritize exogenous arrivals
        for i in currently_arriving_blocks:
            next_arrival_time = np.random.exponential(QNet.bface[i].arrival_rate)
            new_arrivals[i] = next_arrival_time 
            #print("new arrival at block " + str(i))
            QNet.bface[i].total += 1

            car_park_time = np.random.exponential(QNet.bface[i].service_rate)
            car_renege_time = QNet.bface[i].renege_rate            
            currently_available_spots = [ j for j, x in enumerate(QNet.allSpots[i]) if x <= car_renege_time ]
            if len(currently_available_spots) > 0:
                #choose the first available spot
                QNet.allSpots[i][currently_available_spots[0]] = car_park_time
                QNet.bface[i].served += 1
            else:
                #car moves to different blockface--uniformly sample from neighbors
                #this is where I'd be tracking flow
                neighbors = [ j for j, x in enumerate(QNet.network[i]) if x == 1 ]
                newBface = np.random.choice(neighbors)
                QNet.totalFlow[i,newBface] += 1
                quitters[newBface] += 1
                
    if any(quitters.values()):
        #handle the people coming from other block faces
        #keys are blockface indecies
        #what I need is for the quitters to reappear after fixed time, they're instantaneously traveling
        #to next block
        for bf in quitters.keys():
            for k in range(quitters[bf]):
                car_park_time = np.random.exponential(QNet.bface[bf].service_rate)
                car_renege_time = QNet.bface[bf].renege_rate  
                currently_available_spots = [ j for j, x in enumerate(QNet.allSpots[bf]) if x <= car_renege_time ]
                if len(currently_available_spots) > 0:
                    #choose the first available spot
                    QNet.allSpots[bface][currently_available_spots[0]] = car_park_time
                    quitters[bf]-=1
                else:
                    #car moves to different blockface--uniformly sample from neighbors
                    #this is where I'd be tracking flow
                    neighbors = [ j for j, x in enumerate(QNet.network[bf]) if x == 1 ]
                    newBface = np.random.choice(neighbors)
                    QNet.totalFlow[bf,newBface] += 1
                    nextStepQuitters[newBface] += 1
                    quitters[bf]-=1
        quitters = nextStepQuitters
                    
    #update block statistics here:
    
    #countdown on next arrival
    new_arrivals = new_arrivals - deltaT
    #countdown on serve times
    QNet.allSpots = [ (spots - deltaT) for spots in QNet.allSpots ]
    
    #increment simulation time
    t += deltaT

print("Total simulation time: " + str(SIMULATION_TIME))
print("Simulation resolution: " + str(deltaT) + "\n")    
for i in QNet.bface.keys():
    print("block number " + str(i) + ": " + str(QNet.bface[i].total) + " total arrivals")
print("\nAsymmetric net bus flows:")
print(QNet.totalFlow)
