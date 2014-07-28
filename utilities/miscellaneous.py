#!/usr/bin/python2.7
# encoding: utf-8

from __future__ import division
import numpy as np
from datetime import datetime
from datetime import timedelta

def date2py(matlab_datenum):
    python_datetime = datetime.fromordinal(int(matlab_datenum)) + \
        timedelta(days=matlab_datenum%1) - timedelta(days = 366)

    return python_datetime

def op_angles_from_vectors(u, v, debug=False):
    """
    This function takes in vectors in the form (u,v) and compares them in
    order to find the angles of the vectors without any wrap-around issues.
    This is accomplished by finding the smallest difference between angles
    compared at different wrap-around values.
    This appears to work correctly.

    Inputs:
    ------
      -u = velocity component along x (West-East) direction, 1D array
      -v = velocity component along y (South-North) direction, 1D array
    Outputs:
    -------
      -angle = corresponidng angle in degrees, 1D array
    Notes:
    -----
      -Angles are reported in compass coordinates, i.e. 0 and 360 deg.,
       0/360=East, 90=North, 180=West, 270=South
    """
    if debug:
        print 'Computing angles from velocity component...'
        start = time.time()

    phi = np.mod((-1.0*np.arctan2(v,u)) * (180.0/np.pi) + 90.0, 360.0)
    if len(phi.shape)==1:#Assuming the only dimension is time
        #Compute difference between angles
        diff1 = np.abs(phi[:-1]-phi[1:]) #initial difference between angles
        diff2 = np.abs(phi[:-1]-phi[1:]-360.0) #diff when moved down a ring
        diff3 = np.abs(phi[:-1]-phi[1:]+360.0) #diff when moved up a ring

        index1 = np.where((diff2 < diff1) & (diff2 < diff3))[0]
        index2 = np.where((diff3 < diff1) & (diff3 < diff2))[0]

        phi[index1] = np.mod(phi[index1] - 360.0, 360.0)
        phi[index2] = np.mod(phi[index2] + 360.0, 360.0)
    elif len(phi.shape)==2:#Assuming the only dimension is time and sigma level
        #Compute difference between angles
        diff1 = np.abs(phi[:-1,:]-phi[1:,:]) #initial difference between angles
        diff2 = np.abs(phi[:-1,:]-phi[1:,:]-360.0) #diff when moved down a ring
        diff3 = np.abs(phi[:-1,:]-phi[1:,:]+360.0) #diff when moved up a ring

        index1 = np.where((diff2 < diff1) & (diff2 < diff3))[0]
        index2 = np.where((diff3 < diff1) & (diff3 < diff2))[0]

        phi[index1] = phi[index1] - 360.0
        phi[index2] = phi[index2] + 360.0
    else: #Assuming the only dimension is time ,sigma level and element
        #Compute difference between angles
        diff1 = np.abs(phi[:-1,:,:]-phi[1:,:,:]) #initial difference between angles
        diff2 = np.abs(phi[:-1,:,:]-phi[1:,:,:]-360.0) #diff when moved down a ring
        diff3 = np.abs(phi[:-1,:,:]-phi[1:,:,:]+360.0) #diff when moved up a ring

        index1 = np.where((diff2 < diff1) & (diff2 < diff3))[0]
        index2 = np.where((diff3 < diff1) & (diff3 < diff2))[0]

        phi[index1] = phi[index1] - 360.0
        phi[index2] = phi[index2] + 360.0     

    if debug:
        end = time.time()
        print "...processing time: ", (end - start)
    
    return phi

def depth_at_FVCOM_element(ind, trinodes, time_ind):
    """
    Input:
      -ind = element index, integer
      -trinodes = grid trinodes
      -time_ind = reference time indexes for surface elevation, list of integer
    Output: deoth at element, 1D array

    """
    indexes = trinodes[ind,:]
    h = self._grid.h[indexes]
    zeta = np.mean(self._var.el[time_ind,indexes],0) + h[:]   
    siglay = self._grid.siglay[:,indexes]
    z = zeta[None,:]*siglay[:,:]
    dep = np.mean(z,1)

    return dep

def time_to_index(t_start, t_end, time, debug=False):
    """Convert datetime64[us] string in FVCOM index"""
        # Find simulation time contains in [t_start, t_end]
        t = time.shape[0]
        l = []
        for i in range(t):
            date = datetime.fromordinal(int(time[i])) + \
                   timedelta(days=time[i]%1)-timedelta(days=366)
            l.append(date)
        time = np.array(l,dtype='datetime64[us]')
        t_slice = [t_start, t_end]
        t_slice = np.array(t_slice,dtype='datetime64[us]')

        if t_slice.shape[0] != 1:
            argtime = np.argwhere((time>=t_slice[0])&
                                  (time<=t_slice[-1])).flatten()
        if debug:
            print 'Argtime: ', argtime

def signal_extremum(signal):
    """
    This function spots the extremum of a random signal(x).
    Inputs:
      - signal: 1D array of n elements
    Outputs:
      - extremum: 1D array of n elements
      - indices: list containing extremum indices
    """

    extremum = np.zeros(signal.shape[0])
    indices = []

    S = np.sign(signal[0] - signal[1])
    N = (np.arange(signal.shape[0]-2)) + 1

    for i in N:
        E = np.sign(signal[i] - signal[i+1])
        if (E != S):
            extremum[i] = 1.0
            indices.append(i)
            S = np.sign(S*(-1.0))
    
    return extremum, indices

def exceedance_SSE(x, signal, extremum, indices):
    """
    This function calculate the excedence curve of a Sea Surface Elevation signal(x).
    Inputs:
      - x: 1D array of n elements
      - signal: 1D array of n elements
      - extremum: 1D array of n elements
      - indices: list containing extremum indices
    Outputs:
      - Exceedance: list of % of occurences
      - Ranges: list of signal amplitude bins
    """

    N = len(indices)
    period = []
    amp = []
    time_stamp = []

    for i in range(N-1):
        p = x[indices[i+1]]-x[indices[i]]
        if p > (60*60*3): #exceeds 3 hour ramping
            period.append(p)
            amp.append(abs(signal[indices[i]]-signal[indices[i+1]]))
            time_stamp.append(indices[i])

    Max = round(max(amp),1)	
    dy = round((Max/10.0),1)
    Ranges = np.arange(0,(Max + dy), dy)
    Exceedance = np.zeros(Ranges.shape[0])
    Period = np.sum(period)

    N = len(amp)
    M = len(Ranges)

    for i in range(M):
        r = Ranges[i]
        for j in range(N):
            if amp[j] > r:
                Exceedance[i] = Exceedance[i] + period[j]

    Exceedance = (Exceedance * 100) / Period

    return Exceedance, Ranges, amp, time_stamp
