from qnet import *

QNet = blockfaceNet("/home/chase/projects/net-queue/src/python/QNet3params.txt", ["utilization"])

while QNet.timer < QNet.params.simulation_time:
    #find block numbers of blocks with <=0.0 time till next arrival
    #can use itertools.compress on new arrivals list comprehension
    currently_arriving_blocks = [ j for j, x in enumerate(QNet.new_arrivals) if x < QNet.params.time_resolution ]
    if len(currently_arriving_blocks) > 0:
    #give arriving blocks new arrivals
    #prioritize exogenous arrivals
        for i in currently_arriving_blocks:
            blockindex = QNet.injection_map[i]
            next_arrival_time = np.random.exponential(QNet.bface[blockindex].arrival_rate)
            QNet.new_arrivals[i] = next_arrival_time 
            QNet.bface[blockindex].exogenous += 1
            #try to park, otherwise, drive somewhere else
            QNet.park(blockindex)
    
    for origin in QNet.bface.keys():
        #Checking for any drivers arriving at other blocks based on travel time in street buffer
        #have to loop through every block? Yes, if I care about street direction
        for dest in range(len(QNet.streets[origin])):
            #for each possible destination index, get the block index, neighbors is list of block indexs connected to origin
            #but dest is local index of street connected to origin to save space, 
            #e.g. block 2 to block 3 is connected by block 2's street 1
            destblock = QNet.bface[origin].neighbors[dest]
            #at least first driver needs to be arriving
            if len(QNet.streets[origin][dest]) > 0 and QNet.streets[origin][dest][0] < QNet.params.time_resolution:
                #first driver in list will always be closest to 0 unless drive times vary
                #>>>>>THIS WON'T WORK IF DRIVE TIMES ARE NOT CONSTANT<<<<<<<<<<<
                for driver in QNet.streets[origin][dest]:
                    #could be more than one arriving
                    while QNet.streets[origin][dest][0] < QNet.params.time_resolution:
                        QNet.park(destblock)
                        #Get rid of first driver, go back up and check if next driver is also arriving
                        QNet.streets[origin][dest].pop(0)
                        if len(QNet.streets[origin][dest]) == 0:
                            break
    
    #step simulation forward and collect any flagged global stats
    QNet.step_time()

print("\n==Results==")
for i in QNet.bface.keys():
    if i in QNet.injection_map.values():
        print("block number " + str(i) + " (injector):\n\ttotal arrivals: " + str(QNet.bface[i].total))
        print("\tinjected: " + str(QNet.bface[i].exogenous))
    else:
        print("block number " + str(i) + ":\n\ttotal arrivals: " + str(QNet.bface[i].total))
    print("\tparked: " + str(QNet.bface[i].served))
    print("\taverage utilization: " + str(float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization)) * 100.0) + "%")
print(QNet.totalFlow)
