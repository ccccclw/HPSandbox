#! /usr/bin/env python

import random
import string
import math
import os, sys, copy, pickle

import scipy.sparse
import scipy.linalg
import scipy

from msmbuilder.MSMLib import *

from scipy.io import mmread, mmwrite

sys.path.append('../')
from HelperTools import *

from ssaCalculator import ssaCalculator


usage = """Usage: sample.py infile.mtx microstates.dat NumSamplesPerState NumTrials outName

    Will write a series of files:
        tCounts.outName.NumSamplesPerState.0.mtx,
        ....
        tCounts.outName.NumSamplesPerState.(NumTrials-1).mtx
"""

if len(sys.argv) < 6:
    print usage
    sys.exit(1)
             
microTFn = sys.argv[1]
microstatesFn = sys.argv[2]
nsamples = int(sys.argv[3])
ntrials = int(sys.argv[4])
outName = sys.argv[5]
Adaptive = True

################
# Main program

# Read in transition matrix
if os.path.exists(microTFn):
    T = mmread(microTFn)
    print T
else:
    print "Can't find file:", microTFn, '...exiting'
    sys.exit(1)


# Read in microstate info
mInfo = MicrostateInfo(microstatesFn)

print 'mInfo', mInfo

############################
# generate increasing numbers of transition counts

NumStates = T.shape[0]
NumSamplesPerState = [nsamples for i in range(NumStates)]
NumTrials = ntrials

T = T.tolil()

jumpFn = microTFn+'.jumps'
if os.path.exists(jumpFn):
    print 'Reading jump probabilities from:', jumpFn, '...'
    fin = open(jumpFn,'r')
    jumps = pickle.load(fin)
    fin.close()
    print '...Done.'
else:
    print 'Making a dictionary of jump probabiilities...'
    jumps = {}   # {i, (possible_j, jprobs)}

    for i in range(NumStates):
        
        # look for possible transitions
        possible_j = T[i,:].nonzero()[1]
        #print i, '-->', 'possible_j', possible_j
        jprobs = np.array(T[i,possible_j].todense())
        jprobs = jprobs.reshape(jprobs.shape[1],)
        jumps[i] = (possible_j, jprobs)
        if i%100 == 0:
            print i, jumps[i]

    print 'pickling jumps to', jumpFn, '...'
    fout = open(jumpFn,'w')
    pickle.dump(jumps,fout)
    fout.close()
    print 'Done.'
    
C = scipy.sparse.lil_matrix((int(NumStates),int(NumStates)))
TotalCounts = 0

for trial in range(NumTrials):

    for i in range(NumStates):

        #if i%100 == 0:
        #    print 'Sampling', NumSamplesPerState[i], 'transitions from state', i, 'of', NumStates, '...'

        # look for possible transitions
        possible_j = jumps[i][0]
        jprobs = jumps[i][1]
        
        # sample counts from state i
        for k in range(NumSamplesPerState[i]):
            j = possible_j[draw_index(jprobs)]
            C[i,j] += 1
            
    TotalCounts += sum(NumSamplesPerState)
    print 'Sampled', trial*NumSamplesPerState[0], 'from each of 15037 states.  TotalCounts =', TotalCounts

    mmwrite('tCounts.uniform.%s.%d.%d.mtx'%(outName,nsamples,trial), C)

del C
    

