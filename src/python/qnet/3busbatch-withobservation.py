import sys
sys.path.append("/home/chase/projects/net-queue/src/python")
import os
from qnet_refactor import *

workingPath = "/home/chase/Dropbox/UWSDOT/tex/src_/"
paramDir = sys.argv[1]

runs = int(sys.argv[3])

#drive_time = "1.0"
drive_time = "10.0"

try:
    os.mkdir(workingPath + paramDir + "-" + sys.argv[2] + "-sim")
except:
    pass

def write_param_file(paramDir):
    #read paramDir + nash.csv
    #Po,Pb,Pj columns, rows data
    Cw = 0.0
    with open(workingPath + paramDir + "/" + paramDir + sys.argv[2] + ".csv", 'r') as f:
        lines = f.readlines()
        """
        probabilities = np.zeros((len(lines)-1,3))
        for j in range(len(lines)):
            if j == 0:
                pass
            else:
                tokens = lines[j].strip().split(",")
                for k in range(len(tokens)):
                    probabilities[j-1,k] = float(tokens[k])
        """
        probs = lines[1].strip().split(",")
    
    
    #read p0Cw.csv
    #rows data, single column
    try:
        with open(workingPath + paramDir + "/" + paramDir + "Cw.csv", 'r') as f:
            lines = f.readlines()
            waitingCosts = np.zeros((len(lines),1))
            for u in range(len(lines)):
                val = float(lines[u].strip())
                waitingCosts[u]
            Cw = np.mean(waitingCosts)
    except:
        pass
    
    #p0params.csv
    with open(workingPath + paramDir + "/" + paramDir + "params.csv", 'r') as f:
        lines = f.readlines()
        headers = lines[0].strip().split(",")
        data = lines[1].strip().split(",")
        paramDict = {}
        for item in range(len(headers)):
            paramDict[headers[item].strip()] = float(data[item])
            if headers[item].strip() == "Cw":
                Cw = float(data[item].strip())
           
    #write simulator parameter file to deal with array expansion of single parameter values
    #for each blockface       
    with open(workingPath + paramDir + "-" + sys.argv[2] + "-sim/busparams.txt", 'w') as out:
        for header in paramDict.keys():
            if header == "lam":
                out.write("EXOGENOUS_RATE = " + str(1.0 / paramDict["lam"]) + "\n")
                #out.write("EXOGENOUS_RATE = 10.0\n")
            elif header == "c":
                out.write("NUM_SPOTS = " + str(int(float(paramDict["c"]) / 3.0)) + "\n")
            elif header == "mu":
                out.write("SERVICE_RATE = " + str(1.0 / paramDict["mu"]) + "\n")
                #out.write("SERVICE_RATE = 10.0\n")  
            else:
                pass
        out.write("ROAD_NETWORK = /home/chase/projects/net-queue/src/python/test/busnetwork.txt\n")
        out.write("SIMULATION_TIME = 10000.0\n")
        out.write("DRIVE_TIME = " + drive_time + "\n")
        out.write("RENEGE_TIME = 0.0\n")
        
    return(Cw, probs, paramDict)
    
Cwait, nashProbs, simulationParams = write_param_file(paramDir)

params = parameters(workingPath + paramDir + "-" + sys.argv[2] + "-sim/busparams.txt")

utilizationStats = np.zeros((runs,4))
averageWaitTime = np.zeros((runs,2))

probObs = float(nashProbs[0])
probBalk = float(nashProbs[1])
probJoin = float(nashProbs[2])

#balking calc
#mu
cmu = float(simulationParams["mu"])
#total number of servers
c = float(simulationParams["c"])
#Reward
R = float(simulationParams["R"])
#Cost to park
Cp = float(simulationParams["Cp"]) * float(1.0 / simulationParams["lam"])
#cost to wait
Cw = Cwait

balk_cond = np.floor(( (R * cmu * c) - (Cp * c) )/ Cw)

#additional stats
rejects = 0
total_arrivals = 0

#######SIMULATOR#########

for jj in range(runs):
    #params.EXOGENOUS_RATE = params.EXOGENOUS_RATE + (float(jj) * step)
    QNet = blockfaceNet(params, stats=["utilization"])
    
    while QNet.timer < QNet.params.SIMULATION_TIME:
        #currently_arriving_blocks = [ j for j, x in enumerate(list(QNet.new_arrival_timer)) if x < QNet.params.TIME_RESOLUTION ]
        #jackknifing single arrival timer
        if list(QNet.new_arrival_timer)[0] < QNet.params.TIME_RESOLUTION:
            block = np.random.randint(0,3)
            currently_arriving_blocks = list([block])
            total_arrivals += 1
            #doesn't need to be a for loop in this case, 
            #just leaving as is for multi-arrival node set up
            for i in currently_arriving_blocks:
                actionProb = np.random.uniform(0,1)
                blockindex = QNet.injection_map[i]
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

    for i in QNet.bface.keys():
        utilizationStats[jj, i+1] = float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization))
    #calculate average wait time
    total = 0.0
    numCars = float(len(QNet.cars.keys()))
    for carInd in QNet.cars.keys():
        total += QNet.cars[carInd].total_drive_time
        averageWait = total/numCars
    averageWaitTime[jj,1] = averageWait
    utilizationStats[jj,0] = QNet.params.EXOGENOUS_RATE[0,0]
    averageWaitTime[jj,0] = QNet.params.EXOGENOUS_RATE[0,0]
    
avgOut = ("/home/chase/Dropbox/UWSDOT/tex/src_/" + paramDir + "-" + sys.argv[2] + "-sim" + "/averageWait" + str(np.random.randint(1,100000)) + ".txt")
avgFile = open(avgOut, 'w')
utilizationOut = ("/home/chase/Dropbox/UWSDOT/tex/src_/" + paramDir + "-" + sys.argv[2] + "-sim" + "/utilization" + str(np.random.randint(1,100000)) + ".txt")
utilFile = open(utilizationOut, 'w')

#dataOut = ("/home/chase/projects/net-queue/data/3bus-p0/stats" + str(np.random.randint(1,100000)) + ".txt")
dataOut = ("/home/chase/Dropbox/UWSDOT/tex/src_/" + paramDir + "-" + sys.argv[2] + "-sim" + "/stats" + str(np.random.randint(1,100000)) + ".txt")
dataFile = open(dataOut, 'w')
dataFile.write("total_arrivals: " + str(total_arrivals) + "\n")
dataFile.write("rejects: " + str(rejects) + "\n")
dataFile.write("total traffic flow: " + str(QNet.total_flow) + "\n")

np.savetxt(avgFile, averageWaitTime, delimiter=",")
np.savetxt(utilFile, utilizationStats, delimiter=",")
