# -*- coding: utf-8 -*-

import numpy as np


def suminverters(data, mean=0): #sums this var for all inverters in each clock tic
    sumdata=[]
    times = len(data[data.keys()[0]])
    for ix in range(times):
        foo=[]
        for keys in data:
            foo.append(data[keys][ix])
        if mean=='mean':
            sumdata.append(findmean(foo))
##                sumdata.filled(np.nan)
        else:
            sumdata.append(np.nansum(foo))
        
    return sumdata


def calcPR(data, kwp): # ignoring dia8esimothta...
        dataPac = suminverters(data['Pac'])
        dataPac = np.array(dataPac)
        dataIr = data['Irradiance']
        if len(dataIr.keys())>1:
            dataIr = suminverters(dataIr, 'mean')
        else:
            dataIr = np.array(dataIr[dataIr.keys()[0]])
        for ix, val in enumerate(dataIr):
            if val < 100: # if too low Ir, PR has no meaning...
                dataIr[ix] = np.nan
        foo1PR = np.true_divide(dataPac, dataIr)
        return np.true_divide(foo1PR, kwp), dataIr, dataPac

def findmean(foo): # calculate vector's mean ignoring nans
    mfoo=np.ma.masked_array(foo, np.isnan(foo))
    return np.mean(mfoo)
