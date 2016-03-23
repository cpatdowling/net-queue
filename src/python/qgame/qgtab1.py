'''
    Code to Compute Nash equilibrium in queuing game.
    By: Lillian J. Ratliff
    2016.14.03
    Code to recreate examples in the table.
'''


import numpy as np
from math import factorial as fact
import random
#from funcs import *
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import os
import csv
import pickle

def ndmesh(*args):
    ''' Extends meshgrid to n>2 dimensions ''' 
    args = map(np.asarray,args)
    return np.broadcast_arrays(*[x[(slice(None),)+(None,)*i] for i, x in enumerate(args)])


class game:
    def __init__(self,lam, Co, mu, c, Cp, Cw, R, n, Coff=0.0, isOFFS=False):
        self.lam = lam
        self.Co = Co
        self.mu = mu
        self.c = c
        self.Cp = Cp
        self.Cw = Cw
        self.R = R
        self.n = n
        self.Coff = Coff
        self.rho=self.lam/(self.c*self.mu)
        self.ns=int(np.floor((self.R*self.mu*self.c-self.Cp*self.c)/self.Cw))
        self.isOFFS=isOFFS
    
    def xi(self,Pb):
        return (1-Pb)*self.rho
    
    def eta(self,Pj):
        return Pj*self.rho

    def S1(self,Pb):
        t1 = sum([(self.c*self.xi(Pb))**k/fact(k) for k in range(0,self.c)])
        return float(t1)

    def S2(self,Pb):
        t1 = (self.c**self.c/fact(self.c))*sum([self.xi(Pb)**k for k in
                                                  range(self.c,self.ns)])
        return float(t1)
    
    def S3(self,Pb):
        t1 = (self.c**self.c/fact(self.c))*sum([(self.xi(Pb)**k)*(k+1) 
                                        for k in range(self.c,self.ns)])
        return float(t1)

    def S4(self,Pb): 
        t1 = sum([((self.c*self.xi(Pb))**k)*(k+1)/fact(k) for k in
                    range(0,self.c)])
        return float(t1)

    def S5(self,Pb,Pj):
        t1 = ((self.c**self.c/fact(self.c))*(self.xi(Pb)**self.ns)
                *sum([self.eta(Pj)**(k-self.ns) for k in range(self.ns,
                                                               self.n)]))
        return float(t1)

    def S6(self, Pb, Pj):
        t1 = (self.c**self.c/fact(self.c))*sum([self.eta(Pj)**(k-self.ns)
                *(self.xi(Pb)**self.ns)*(k+1) for k in range(self.ns,self.n)])
        return float(t1)

    def p0(self,Pb,Pj):
        xi_  = self.xi(Pb)
        eta_ = self.eta(Pj)
        t1   = self.S1(Pb)+self.S2(Pb)
        t2   = ((self.c**self.c/fact(self.c))*xi_**(self.ns)
                    *(1-eta_**(self.n-1-self.ns))/(1-eta_))
        return float(((t1+t2)**(-1)))
    
    def Uo(self,Pb,Pj, sign=1.0):
        xi_  = self.xi(Pb)
        eta_ = self.eta(Pj)
        t1   = self.p0(Pb,Pj)*((self.R-self.Cp/self.mu)*(self.S1(Pb)+self.S2(Pb)))
        t2   = self.p0(Pb,Pj)*(-1.0*self.Cw/(self.c*self.mu)*(self.S3(Pb)+self.S4(Pb)))
        return (sign*(t1+t2-self.Co))

    def Uj(self,Pb,Pj, sign=1.0):
        xi_  = self.xi(Pb)
        eta_ = self.eta(Pj)
        t1   = (self.p0(Pb,Pj)*((self.R-self.Cp/self.mu)
                               *(self.S1(Pb)+self.S2(Pb)+self.S5(Pb,Pj))))
        t2   = (self.p0(Pb,Pj)*(-1.0*self.Cw/(self.c*self.mu)
                                *(self.S3(Pb)+self.S4(Pb)+self.S6(Pb,Pj))))
        return sign*(t1+t2)

    def Uso(self,x, sign=1.0):
        t1=self.lam*x[1]*self.Uj(x[0],x[1])
        t2=self.lam*(1-x[0]-x[1])*self.Uo(x[0],x[1])
        return (t1+t2)
  
    def J(self,x):
        t1=self.lam*x[1]*self.Uj(x[0],x[1])
        t2=self.lam*(1-x[0]-x[1])*self.Uo(x[0],x[1])
        t3=self.lam*x[0]*(self.R-self.Coff/self.mu)
        return -(t1+t2+t3)

    def algnash(self,x0, eps=5e-3,delta=5e-3, ub=0.0):
        ''' Best Response algorithm to compute Nash
            inputs: 
                x0    : initial condition
                eps   : tolerance for diff between welfares
                delta : tolerance for stopping condition
                ub    : balking cost, non-zero for off-street parking
            output:
                pstar : best response
                ix    : number of iterations before convergence
                utils : utility values

        '''
        po=x0[0]; pb=x0[1]; pj=x0[2]
        pstar=[po,pb,pj]
        uo=self.Uo(pstar[1],pstar[2])
        uj=self.Uj(pstar[1],pstar[2])
        initial=[uo,uj]
        ix=0
        utils=[]
        case1=0; case2=0; case3=0; case4=0; case5=0; case6=0; case7=0;
        while True: 
            utils.append([uo,uj]) # store utility values
            gamma=random.random() # choose random gamma for convex combo
            ix=ix+1               # count iterations
            # tests for case 7
            tests=0
            if abs(uo-ub)<eps:
                tests=tests+1
            if abs(uj-ub)<eps:
                tests=tests+1
            if abs(uo-uj)<eps:
                tests=tests+1
            # tests for case6:
            test6=0
            if (abs(uj-ub)<eps):
                test6+=1
            if min(uj,ub)>uo+eps:
                test6=test6+1
            # tests for case4:
            test4=0
            if (abs(uo-ub)<eps):
                test4+=1
            if min(uo,ub)>uj+eps:
                test4=test4+1
            #tests for case 5:
            test5=0
            if abs(uj-uo)<eps:
                test5=test5+1
            if min(uj,uo)>eps+ub:
                test5=test5+1
            
            if uo> (max(uj,ub)+eps):
                case1+=1
                pstar1=[1.0,0.0,0.0] #po,pb,pj
            elif ub>(max(uj,uo)+eps):
                case2+=1
                pstar1=[0.0,1.0,0.0]
            elif uj>(max(uo,ub)+eps):
                case3+=1
                pstar1=[0.0,0.0,1.0]
            elif test4>=2:
                case4+=1
                pstar1=[po/(po+pb),pb/(po+pb),0]
            elif test5>=2:
                case5+=1
                pstar1=[po,0.0,1-po]
            elif test6>=2:
                case6+=1
                pstar1=[0,pb,1-pb]
            elif tests>=2:
                case7+=1
                pstar1=[po,pb,pj]
            if abs(pstar1[0]-pstar[0])+abs(pstar1[1]-pstar[1])<delta:
                break
            
            pbr=np.asarray(pstar)*gamma+(1-gamma)*np.asarray(pstar1) #[po,pb,pj])
            pstar=pbr.tolist()
            po=pstar[0]; pb=pstar[1]; pj=pstar[2]
            uo=self.Uo(pstar[1],pstar[2])
            uj=self.Uj(pstar[1],pstar[2])
        # convert to debug later
        #case=[case1, case2, case3, case4, case5, case6, case7]
        return [pstar,ix, utils]


    def getSOpt(self,splex):
        ''' Compute social optimum
            uses scipy optimize, should pass derivative later
            input:
                splex  : 1-simplex (2 variables)
            output:
                swlf   : social welfare
                sopt   : social optimum
        '''
        cons=({'type': 'ineq',
            'fun': lambda x: np.array([1-x[0]-x[1]]), 
            'jac': lambda x: np.array([-1.0,-1.0])},
            {'type': 'ineq',
            'fun': lambda x: np.array([x[0]+x[1]]), 
            'jac': lambda x: np.array([1.0,1.0])},
            {'type': 'ineq',
            'fun': lambda x: np.array([0*x[0]+x[1]]), 
            'jac': lambda x: np.array([0.0,1.0])},
            {'type': 'ineq',
            'fun': lambda x: np.array([x[0]+0.0*x[1]]), 
            'jac': lambda x: np.array([1.0,0.0])},
            {'type': 'ineq',
            'fun': lambda x: np.array([-x[0]+1+0.0*x[1]]), 
            'jac': lambda x: np.array([-1.0,0.0])},
            {'type': 'ineq',
            'fun': lambda x: np.array([0.0*x[0]+1-1.0*x[1]]), 
            'jac': lambda x: np.array([0.0,-1.0])})
  
        xout_=[]
        pout=[]
        obj=[]
        for x0 in splex:
            res=minimize(self.J,x0,method='SLSQP', constraints=cons,
                         options={'disp':False})
            xout_.append(res['x']) #Pb,Pj
            xout=res['x']
            obj.append(-1.0*res['fun'])
            pout.append([1-xout[0]-xout[1],xout[0],xout[1]])
        sopt=np.mean(pout,axis=0)
        swlf=np.mean(obj)
        return [swlf,sopt]

    def getNash(self,splex, eps=5e-3,delta=5e-3):
        ''' Function that returns Nash equilibrium and Nash welfare
            inputs:
                splex  : 2-simplex (3 variables)
                eps    : Nash algorithm tolerance for distance between welfares
                delta  : Nash algothihm tolerance for termination
            outputs:
                nwlf   : Nash welfare
                nash   : Nash equilibrium
        '''
        pvals=[] # storage nash for each value in simplex
        it=[]
        for zz in splex:
            # check if this is off v. on street
            if self.isOFFS:
                ub_=(self.R-self.Coff/self.mu)
            else:
                ub_=0.0
            # compute Nash
            [pout,ix,utils]=self.algnash(zz,eps=5e-3, delta=5e-3,ub=ub_)

            pvals.append(pout)
            it.append(ix)
        # take mean of all runs over the whole simplex (should be close)
        nash=np.mean(pvals,axis=0)
        # compute Nash cost
        nashcost = lambda Pb,Pj: (self.lam*Pj*self.Uj(Pb,Pj)
                                +self.lam*(1-Pj-Pb)*self.Uo(Pb,Pj))
        nwlf=nashcost(nash[1],nash[2])
        return [nwlf,nash]


if __name__ == "__main__":
    plot=True
    N=10000
    N=int(np.sqrt(N))**2
    x01=np.linspace(0.0,1.0, np.sqrt(N))
    x02=np.linspace(0.0,1.0, np.sqrt(N))
    x03=np.linspace(0.0,1.0, np.sqrt(N))
    # create 2 simplex
    splex2=[]
    for x1 in x01:
        splex2.append([x1, 1-x1])
    splex2_=np.asarray(splex2)
    # create 3 simplex
    splex3=[]
    for z1,x1 in zip(splex2,x01):
        splex3.append([z1[0]*(1-x1),z1[1]*(1-x1),x1])
        splex3.append([z1[1]*(1-x1),z1[0]*(1-x1),x1])
    
    # set parameters
    c = 30; mu = 1/120.0;  n = 100; 
    Coff=0.962; 
    #lam,Co,mu,c,Cp,Cw,R,n,Coff=Coff,isOFFS=True
    dic={0: [1/5.,0.25,mu,c,0.05,0.8,75,n,0,False],
         1: [1/4.85,0.5,mu,c,0.05,0.75,75,n,0,False],
         2: [1/4.5,2.0,mu,c,0.075,0.5,75,n,0,False],
         3: [1/4.5,3.85,mu,c,0.05,1.5,65,n,0.962,True],
         4: [1/4.75,3.85,mu,c,0.05,1.5,65,n,0.962,True]}
    lamvals=[]
    rho_=np.linspace(0.1,0.9,1)
    lam_=np.linspace(0.025,0.225,1)
    lam = lam_[0];
    # constants for welfare
    x1=[0,0,0,10,12]
    param_nam=['lam','Co','mu','c','Cp','Cw','R','n', 'Coff']
    #param_val=[lam,c,mu,Cp, R, Co, n, Cw,Coff]
    var=rho_
    var_=lam_
    par='pr3_'
    sopt_=[]; swlf_=[]; nwlf_=[]; nash_=[];
    for ind in range(0,5):
        [lam,Co,mu,c,Cp,Cw,R,n,Coff,isOFFS]=dic[ind]
        g=game(lam,Co,mu,c,Cp,Cw,R,n,Coff=Coff,isOFFS=True)

        [swlf,sopt]=g.getSOpt(splex2)
        [nwlf,nash]=g.getNash(splex3)
        print 'social optimum    =  %s' % sopt
        print 'social welfare    =  %s' % swlf
        print 'nash equilibrium  =  %s' % nash
        print 'nash welfare      =  %s' % nwlf

        sopt_.append(sopt)
        swlf_.append([swlf+x1[ind])
        nash_.append(nash)
        nwlf_.append([nwlf+x1[ind]])
        #lamvals.append([lam])


    if not os.path.exists(par+'/'):
        os.mkdir(par+'/')

    with open('./'+par+'/'+par+'params.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows([param_nam, dic[0],dic[1],dic[2],dic[3],dic[4]])

    with open('./'+par+'/'+par+'nash.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(['Po','Pb','Pj'])
        a.writerows(nash_)
    with open('./'+par+'/'+par+'so.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(['Po','Pb','Pj'])
        a.writerows(sopt_)
    #with open('./'+par+'/'+par+'lam.csv', 'w') as fp:
    #    a = csv.writer(fp, delimiter=',')
    #    a.writerows(lamvals)
    with open('./'+par+'/'+par+'sowelf.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(['swlf'])
        a.writerows(swlf_)
    with open('./'+par+'/'+par+'ncost.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(['nwlf'])
        a.writerows(nwlf_)
    
    
    pickle.dump([swlf_, nwlf_, var_], open("./"+par+"/welfdata"+par+".p","wb"))
