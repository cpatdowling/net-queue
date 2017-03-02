# net-queue

# Publications
(NOTE: Branch version 1.1 -- not master) Network queue simulator for "How Much Urban Traffic is Searching for Parking", submitted to KDD 2017: https://arxiv.org/pdf/1702.06156.pdf

-Averaged block-face occupancy data is available in /net-queue/data/simulation/belltownsims/belltowndata/belltownmodeldata
-Daily block-face occupancy data is publically available at https://data.seattle.gov/ and also through contacting the Seattle
	Department of Transportation (SDOT) directly
-Daily traffic volume data for May 2016 (used in this paper) is available through, from Stephen Barham, SDOT: https://public.tableau.com/profile/stephen.barham#!/vizhome/shared/SNMHR2RC6

(NOTE: Branch version 1.0 -- not master) Network queue simulator for "To Observe or Not to Observe: Queueing Game Framework for Urban Parking", submitted to IEEE CDC 2016: https://arxiv.org/pdf/1603.08995.pdf

src/matlab for analysis of the stationary distribution of symmetric network queues is current with the master branch--instructions contained in individual functions/scripts.

-------------------------------------------------------------------------------------------------------------------------------
# Simulator

Requirements:
	
	-Python 2.7+ or 3.0.1+
	
	-Tested in Python 2.7.6 on Ubuntu 14.04
	
	-NumPy for Python 2.7+

Contents:
	
	-src/python/qnet
    		qnet.py: Queueing network class for simulating networks of parking queues.
    		3bus.py: Example 3 bus blockface as described in conference paper
    		
    		
    	-src/python/qgame
    		Scripts for producing equillibrium Nash and social optimum parking strategies given costs
    		Readme for running and producing output
    		
Example network queue simulation:

	-Edit net-queue/data/params/ex1-busparams.txt: "ROAD_NETWORK = $your-working-path$/net-queue/data/params/ex1-busnetwork.txt"
	
	-Navigate to $working-path$/net-queue/src/python/qnet or add net-queue/src/python/qnet to your python path
	
	-python 3bus.py $your-working-path$/net-queue/data/params/ex1-busparams.txt
	
	-parking game strategy for this example comes from table 1, On-Street vs Off-Street parking example 1, type SO (socially optimal equillibrium)
