import sys
import os
import numpy as np
from qnet import *

import pickle

paramFilePath = sys.argv[1]
saveDir = sys.argv[2]
params = parameters()
params.read(paramFilePath)

#initialize network
QNet = blockfaceNet(params, stats=["utilization", "traffic", "rejection", "stationary"])

total_arrivals = 0
  
while QNet.timer < QNet.params.SIMULATION_TIME:
    currently_arriving_blocks = [ j for j, x in enumerate(list(QNet.new_arrival_timer)) if x < QNet.params.TIME_RESOLUTION ]
    if len(currently_arriving_blocks) > 0:
        for i in currently_arriving_blocks:
            total_arrivals += 1
            blockindex = QNet.injection_map[i]
            QNet.bface[blockindex].exogenous += 1
            QNet.carIndex += 1
            QNet.cars[QNet.carIndex] = car(QNet.carIndex)
            QNet.park(blockindex, QNet.carIndex)

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
maxSpaces = int(np.max(QNet.params.NUM_SPOTS))
stationaryDistributions = np.zeros((len(QNet.bface.keys()), maxSpaces+1))
stationaryBins = range(maxSpaces+2) #+1 for when block is empty, +1 for open max interval in np.histogram, maxSpaces + 1 relevant values
for i in QNet.bface.keys():
    utilizationStats[0, i] = float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization))
    statDist = list(np.histogram(QNet.bface[i].num_in_service, bins=stationaryBins, density=True)[0])
    for k in range(len(statDist)):
        stationaryDistributions[i, k] = statDist[k]
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
    #print(QNet.cars[carInd].bfaces_attempted) #potential error in wait times
averageWait = np.array([[total/numCars]])






#Write
simulation_ID = str(np.random.randint(1,100000))

np.savetxt(saveDir + "/traffic_total_flow_" + simulation_ID + ".txt", QNet.total_flow, delimiter=",")

np.savetxt(saveDir + "/traffic_over_time_" + simulation_ID + ".txt", trafficStats, delimiter=",")

np.savetxt(saveDir + "/utilization_" + simulation_ID + ".txt", utilizationStats, delimiter=",")

np.savetxt(saveDir + "/avg_interrejection_" + simulation_ID + ".txt",
avgInterRejection, delimiter = ",")

np.savetxt(saveDir + "/avg_wait_" + simulation_ID + ".txt", averageWait, delimiter = ",")

np.savetxt(saveDir + "/stationary_dist_" + simulation_ID + ".txt", stationaryDistributions, delimiter = ",")



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
