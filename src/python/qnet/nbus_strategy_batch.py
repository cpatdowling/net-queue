import sys
import os
from qnet import *

paramFilePath = sys.argv[1]
saveDir = sys.argv[2]
params = parameters()
params.read(paramFilePath)

#strategy
probObs = float(sys.argv[3])
probBalk = float(sys.argv[4])
probJoin = float(sys.argv[5])

#initialize network
QNet = blockfaceNet(params, stats=["utilization", "traffic", "rejection"])

total_arrivals = 0
balks = 0
  
while QNet.timer < QNet.params.SIMULATION_TIME:
    currently_arriving_blocks = [ j for j, x in enumerate(list(QNet.new_arrival_timer)) if x < QNet.params.TIME_RESOLUTION ]
    if len(currently_arriving_blocks) > 0:
        for i in currently_arriving_blocks:
            actionProb = np.random.uniform(0,1)
            total_arrivals += 1
            blockindex = QNet.injection_map[i]
            if actionProb > (1.0 - probBalk):
                #straight up quit
                balks += 1
            elif actionProb < probJoin:
                #straight up join
                QNet.bface[blockindex].exogenous += 1
                QNet.carIndex += 1
                QNet.cars[QNet.carIndex] = car(QNet.carIndex)
                QNet.park(blockindex, QNet.carIndex)
            else:
                #observe then quit or join
                available_spots = []
                for k in range(len(QNet.bface.keys())):
                    num_open = len([ j for j, x in enumerate(QNet.all_spots[k]) if x <= QNet.bface[k].renege_rate + QNet.params.TIME_RESOLUTION ])
                    if num_open > 0:
                        available_spots.append(k)
                if len(available_spots) > 0:
                    blockindex = available_spots[np.random.randint(len(available_spots))]
                    QNet.bface[blockindex].exogenous += 1
                    QNet.carIndex += 1
                    QNet.cars[QNet.carIndex] = car(QNet.carIndex)
                    QNet.park(blockindex, QNet.carIndex)
                else:
                    balks += 1

            next_arrival_time = np.random.exponential(QNet.bface[blockindex].arrival_rate)
            QNet.new_arrival_timer[i] = next_arrival_time        
                   
    for origin in QNet.bface.keys():
        for dest in range(len(QNet.bface[origin].neighbors)):
	        destblock = QNet.bface[origin].neighbors[dest][1]
	        if len(QNet.streets[origin][dest]) > 0 and QNet.streets[origin][dest][0][1] < QNet.params.TIME_RESOLUTION:       
		        while QNet.streets[origin][dest][0][1] < QNet.params.TIME_RESOLUTION:
		            carIndex = QNet.streets[origin][dest][0][0]
		            QNet.park(destblock, carIndex)
		            QNet.streets[origin][dest].pop(0)
		            if len(QNet.streets[origin][dest]) == 0:
			            break
    QNet.step_time(supress=True, debug=False)
    
#calculate network statistics
utilizationStats = np.zeros((1,len(QNet.bface.keys())))
avgInterRejection = np.zeros((1, len(QNet.bface.keys())))
for i in QNet.bface.keys():
        utilizationStats[0, i] = float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization))
        try:
            avgInterRejection[0, i] = float(sum(QNet.bface[i].inter_reject_times))/float(len(QNet.bface[i].inter_reject_times))
        except:
            avgInterRejection[0, i] = 0.0
        
#colate street traffic stats
#this is super fuckin hacky, damn streets, need to make blocks and streets the same
#queue class and then just instantiate them accordingly, access all information for
#a block or a street from their class instance
num_streets = 0
for origin in range(len(QNet.streets_traffic.keys())):
    for dest in range(len(QNet.streets_traffic[origin])):
        num_streets += 1
trafficStats = np.zeros((len(QNet.clock), 1+num_streets))
for t in range(len(QNet.clock)):
    trafficStats[t, 0] = QNet.clock[t]
    for j in range(len(QNet.streets_traffic.keys())):
        for k in range(len(QNet.streets_traffic[j])):
            trafficStats[t, j+k+1] = QNet.streets_traffic[j][k][t]

total = 0.0
numCars = float(len(QNet.cars.keys()))
for carInd in QNet.cars.keys():
    total += QNet.cars[carInd].total_drive_time
    #print(QNet.cars[carInd].bfaces_attempted)
averageWait = np.array([[total/numCars]])



#Write
simulation_ID = str(np.random.randint(1,100000))

np.savetxt(saveDir + "/traffic_total_flow_" + simulation_ID + ".txt", QNet.total_flow, delimiter=",")

np.savetxt(saveDir + "/traffic_over_time_" + simulation_ID + ".txt", trafficStats, delimiter=",")

np.savetxt(saveDir + "/utilization_" + simulation_ID + ".txt", utilizationStats, delimiter=",")

np.savetxt(saveDir + "/avg_interrejection_" + simulation_ID + ".txt",
avgInterRejection, delimiter = ",")

np.savetxt(saveDir + "/avg_wait_" + simulation_ID + ".txt", averageWait, delimiter = ",")



if False:        
    #Print network statistics    
    print("\nResults:\n\n")
    print("System stats:\n")
    print("\tTotal arrivals: " + str(total_arrivals) + "\n")
    print("\tAverage wait time: " + str(averageWait) + "\n")
    print("\tTotal traffic flow: \n" + str(QNet.total_flow) + "\n\n")
    
    print("Blockface stats:\n")
    for i in range(len(QNet.bface.keys())):
        print("\tBlockface " + str(i+1) + " utilization: " + str(utilizationStats[0, i]))
