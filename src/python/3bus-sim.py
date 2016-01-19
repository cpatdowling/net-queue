from qnet import *

QNet = blockfaceNet("/home/chase/projects/net-queue/src/python/QNet3params.txt")

#keeping track of people moving from one blockface to next
#key is destination blockface index, value is number of quitters moving to new block face
quitters = {}
for bface in QNet.bface.keys():
    quitters[bface] = 0
nextStepQuitters = quitters

t = 0.0
deltaT = QNet.params.time_resolution
while t < QNet.params.simulation_time:
    #find block numbers of blocks with <=0.0 time till next arrival
    #can use itertools.compress on new arrivals list comprehension
    currently_arriving_blocks = [ i for i, x in enumerate(QNet.new_arrivals) if x <= 0.0 ]
    if len(currently_arriving_blocks) > 0:
        #give arriving blocks new arrivals
        #prioritize exogenous arrivals
        for i in currently_arriving_blocks:
            blockindex = QNet.injection_map[i]
            next_arrival_time = np.random.exponential(QNet.bface[blockindex].arrival_rate)
            QNet.new_arrivals[i] = next_arrival_time 
            
            QNet.bface[blockindex].total += 1
            QNet.bface[blockindex].exogenous += 1

            car_park_time = np.random.exponential(QNet.bface[blockindex].service_rate)
            car_renege_time = QNet.bface[blockindex].renege_rate            
            currently_available_spots = [ j for j, x in enumerate(QNet.allSpots[blockindex]) if x <= car_renege_time ]
            if len(currently_available_spots) > 0:
                #parking available, choose the first available spot
                QNet.allSpots[blockindex][currently_available_spots[0]] = car_park_time
                QNet.bface[blockindex].served += 1
            else:
                #car moves to different blockface--uniformly sample from neighbors
                neighbors = [ j for j, x in enumerate(QNet.network[blockindex]) if x == 1 ]
                newBface = np.random.choice(neighbors)
                QNet.totalFlow[blockindex,newBface] += 1
                quitters[newBface] += 1
                
    if any(quitters.values()):
        #handle the people coming from other block faces
        #keys are blockface indecies
        #what I need is for the quitters to reappear after fixed time, they're instantaneously traveling
        #to next block
        for dest_bf in quitters.keys():
            for k in range(quitters[dest_bf]):
                #for each kth car arriving at this node from previous time step
                car_park_time = np.random.exponential(QNet.bface[dest_bf].service_rate)
                car_renege_time = QNet.bface[dest_bf].renege_rate  
                currently_available_spots = [ j for j, x in enumerate(QNet.allSpots[dest_bf]) if x <= car_renege_time ]
                if len(currently_available_spots) > 0:
                    #parking available, choose the first available spot
                    QNet.allSpots[dest_bf][currently_available_spots[0]] = car_park_time
                    QNet.bface[dest_bf].served += 1
                    quitters[dest_bf] -= 1
                else:
                    #car moves on to different blockface--uniformly sample from neighbors
                    neighbors = [ j for j, x in enumerate(QNet.network[dest_bf]) if x == 1 ]
                    newBface = np.random.choice(neighbors)
                    QNet.totalFlow[dest_bf,newBface] += 1
                    quitters[dest_bf] -= 1
                    nextStepQuitters[newBface] += 1
                QNet.bface[dest_bf].total += 1
        for bface in quitters:
            quitters[bface] += nextStepQuitters[bface]
    
    #countdown on next arrival
    QNet.new_arrivals = QNet.new_arrivals - deltaT
    #countdown on serve times
    QNet.allSpots = [ (spots - deltaT) for spots in QNet.allSpots ]
    
    #increment simulation time
    t += deltaT
    if t % (QNet.params.simulation_time / 10) <= QNet.params.time_resolution and t >= 10.0:
        print(str(int(t / (QNet.params.simulation_time/100))) + "% complete")
        
    #if traffic overflows, break loop
    if any([ j for j, x in enumerate(quitters.values()) if x > (QNet.bface[1].num_parking_spots * QNet.params.simulation_time * 10) ]):
        print("\n==Exception==")
        print("Traffic overflow at simulation time: " + str(t))
        print("Total flow: ")
        print(QNet.totalFlow)
        break

print("\n==Results==")
for i in QNet.bface.keys():
    print("block number " + str(i) + ": " + str(QNet.bface[i].total) + " total arrivals")
print(QNet.totalFlow)
