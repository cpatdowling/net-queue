from qnet import *

paramFilePath = sys.argv[1]
saveDir = sys.argv[2]

params = parameters()
params.read(paramFilePath)
params.VERBOSE = False
params.STATS = ["occupancy", "traffic", "interrejection", "stationary"]

#initialize network
QNet = blockfaceNet(params)

#simulate
QNet.simulate()

#output
rep = report(QNet, saveDir)
rep.write_to_file()
         
