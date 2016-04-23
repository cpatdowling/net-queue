import sys
import os
from qnet import *

paramFilePath = sys.argv[1]
params = parameters(paramFilePath)

#initialize network
QNet = blockfaceNet(params, stats=["utilization"])

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
	                for driver in QNet.streets[origin][dest]:
		                while QNet.streets[origin][dest][0][1] < QNet.params.TIME_RESOLUTION:
		                    carIndex = QNet.streets[origin][dest][0][0]
		                    QNet.park(destblock, carIndex)
		                    QNet.streets[origin][dest].pop(0)
		                    if len(QNet.streets[origin][dest]) == 0:
			                    break
    QNet.step_time(supress=True)
    
#calculate network statistics
utilizationStats = np.zeros((1,len(QNet.bface.keys())))
for i in QNet.bface.keys():
        utilizationStats[0, i] = float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization))

total = 0.0
numCars = float(len(QNet.cars.keys()))
for carInd in QNet.cars.keys():
    total += QNet.cars[carInd].total_drive_time
averageWait = total/numCars

#Write
np.savetxt("/home/chase/projects/quals/data/vanilla/utilization" + str(np.random.randint(1,100000)) + ".txt", utilizationStats, delimiter=",")

"""        
#Print network statistics    
print("\nResults:\n\n")
print("System stats:\n")
print("\tTotal arrivals: " + str(total_arrivals) + "\n")
print("\tAverage wait time: " + str(averageWait) + "\n")
print("\tTotal traffic flow: \n" + str(QNet.total_flow) + "\n\n")

print("Blockface stats:\n")
for i in range(len(QNet.bface.keys())):
    print("\tBlockface " + str(i+1) + " utilization: " + str(utilizationStats[0, i]))
"""
