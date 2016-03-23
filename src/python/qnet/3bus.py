import sys
import os
from qnet import *

paramFilePath = sys.argv[1]
params = parameters(paramFilePath)

#initialize network
QNet = blockfaceNet(params, stats=["utilization"])

rejects = 0
total_arrivals = 0

#set parking strategy
probBalk = 0.2
probJoin = 0.35
#probObs = (1 - (probBalk + probJoin)) implicitly

#balking calc
#mu
cmu = params.EXOGENOUS_RATE[0,0]
#total number of servers
c = float(params.NUM_SPOTS[0,0] * 3)
#Reward
R = 65.0
#Cost to park
Cp = 0.05
#cost to wait
Cw = 1.5

balk_cond = np.floor(( (R * cmu * c) - (Cp * c) )/ Cw)
  
while QNet.timer < QNet.params.SIMULATION_TIME:
    #currently_arriving_blocks = [ j for j, x in enumerate(list(QNet.new_arrival_timer)) if x < QNet.params.TIME_RESOLUTION ]
    #The above is used for individual blockface arrivals
    if list(QNet.new_arrival_timer)[0] < QNet.params.TIME_RESOLUTION:
        #just using the first block as the total network arrival timer: list(QNet.new_arrival_timer)[0]
        #and choosing a blockface for a driver arrival
        block = np.random.randint(0,3)
        currently_arriving_blocks = list([block])
        total_arrivals += 1
        #for loop normally handles multiple blockface arrival rates that potentially occur simultaneously
        for i in currently_arriving_blocks:
            actionProb = np.random.uniform(0,1)
            blockindex = QNet.injection_map[i]
            
            ####game strategy; parking decisions####
            if actionProb > (1.0 - probBalk):
                #straight up quit
                rejects += 1
            elif actionProb < probJoin:
                #straight up join
                QNet.bface[blockindex].exogenous += 1
                QNet.carIndex += 1
                QNet.cars[QNet.carIndex] = car(QNet.carIndex)
                QNet.park(blockindex, QNet.carIndex)
            else:
                #observe and then join or quit
                available_spots = 0
                in_queue = 0
                for k in range(3):
                    available_spots += len([ j for j, x in enumerate(QNet.all_spots[k]) if x <= QNet.bface[k].renege_rate + QNet.params.TIME_RESOLUTION ])
                    for z in range(2):
                        in_queue += len(QNet.streets[k][z])
                #adjusting balk condition to system state
                balk_factor = in_queue - available_spots
                if balk_factor < balk_cond:
                    QNet.bface[blockindex].exogenous += 1
                    QNet.carIndex += 1
                    QNet.cars[QNet.carIndex] = car(QNet.carIndex)
                    QNet.park(blockindex, QNet.carIndex)
                else:
                    rejects += 1
            ####       
            
            next_arrival_time = np.random.exponential(QNet.bface[blockindex].arrival_rate)
            QNet.new_arrival_timer[0] = next_arrival_time 
            
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
    QNet.step_time()
    
#calculate network statistics
utilizationStats = np.zeros((1,3))
for i in QNet.bface.keys():
        utilizationStats[0, i] = float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization))

total = 0.0
numCars = float(len(QNet.cars.keys()))
for carInd in QNet.cars.keys():
    total += QNet.cars[carInd].total_drive_time
averageWait = total/numCars
        
#Print network statistics    
print("\nResults:\n\n")
print("System stats:\n")
print("\tTotal arrivals: " + str(total_arrivals) + "\n")
print("\tRejects: " + str(rejects) + "\n")
print("\tAverage wait time: " + str(averageWait) + "\n")
print("\tTotal traffic flow: \n" + str(QNet.total_flow) + "\n\n")

print("Blockface stats:\n")
for i in range(len(QNet.bface.keys())):
    print("\tBlockface " + str(i+1) + " utilization: " + str(utilizationStats[0, i]))
