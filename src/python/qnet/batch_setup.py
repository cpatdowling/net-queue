import sys
import os

mc = sys.argv[1]
exphandle = sys.argv[2]
paramfile = sys.argv[3]
outputdir = sys.argv[4]

if not os.path.exists(outputdir):
    os.mkdir(outputdir)

mcfile = open(outputdir + "/runMC.sh", "w")

#can vary some parameter value and output the changing parameter value to looped directories

for i in range(int(mc)):
    if not os.path.exists(outputdir + "/" + exphandle):
        os.mkdir(outputdir + "/" + exphandle)
    mcfile.write("python /home/chase/projects/net-queue/src/python/qnet/nbus_batch.py " + paramfile + " " + outputdir + "/" + exphandle + "\n")

mcfile.close()
