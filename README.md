# net-queue
Network queue simulator for "To Observe or Not to Observe: Queueing Game Framework for Urban Parking", submitted to IEEE CDC 2016.


Requirements:
	
	-Python 2.7+ or 3.0.1+
	
	-Tested in Python 2.7.6 on Ubuntu 14.04
	
	-NumPy and SciPy for Python 2.7+

Contents:
	
	-src/python/qnet
    		qnet.py: Queueing network class for simulating networks of parking queues.
    		3bus.py: Example 3 bus blockface as described in conference paper
    		
    		
    	-src/python/qgame
    		Scripts for producing equillibrium Nash and social optimum parking strategies given costs
    		Readme for running and producing output
    		
Example network queue simulation:

	-Edit ex1-busparams.txt: "ROAD_NETWORK = $your-working-path$/net-queue/data/params/ex1-busnetwork.txt"
	
	-Navigate to $working-path$/net-queue/src/python or add net-queue/python/src/qnet to your python path
	
	-python 3bus.py $your-working-path$/net-queue/data/params/ex1-busparams.txt
	
	-parking game strategy for this example comes from table 1, On-Street vs Off-Street parking example 1, type SO (socially optimal equillibrium)
