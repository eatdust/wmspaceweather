#!/usr/bin/python3

#   This file is designed for creating output read by wmSpaceWeather
#
#   Copyright (C) 2024 Chris Ringeval
#
#   getspaceweather is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   getspaceweather is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with getspaceweather.  If not, see <https://www.gnu.org/licenses/>.


import json
import requests
from statistics import median
from datetime import datetime, timezone, timedelta

swtimeformat = '%Y-%m-%dT%H:%M:%SZ'

potsdamGetKp = 'https://kp.gfz-potsdam.de/app/json/?'
geosEspectra = 'https://services.swpc.noaa.gov/json/goes/primary/differential-electrons-6-hour.json'
geosPspectra = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-1-day.json'
geosXflares  = 'https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json'

#I/O to wmspaceweather
outdir = '/tmp/'
wmfilename = 'LatestKp.txt'

def main():

    tnow = datetime.now(timezone.utc)
    deltat = timedelta(hours=3)
    ndt = 8

    #get Kps    
    try:
        kpdates, wmdates, Kps = getLastKpIndices(t=tnow,dt=deltat,n=ndt)
    except:
        print("cannot retrieve Kp data!")
        return

    #get electron fluxes in the last deltat time range
    try:
        edates, E0, E1, E2 = getElectronFluxes(t=tnow,dt=deltat)
        E0m = median(E0)
        E1m = median(E1)
        E2m = median(E2)
    except:
        print("cannot retrieve electron fluxes!")
        E0m = -999
        E1m = -999
        E2m = -999
              
    #get proton fluxes in the last deltat time range
    try:
        pdates, P1, P2, P3 = getProtonFluxes(t=tnow,dt=deltat)
        P1m = median(P1)
        P2m = median(P2)
        P3m = median(P3)

    except:
        print("cannot retrieve proton fluxes!")
        P1m = -999
        P2m = -999
        P3m = -999
              

    #get latest Xflares dates, duration and class
    try:
        xdates, xdt, CX = getLatestXrays()
    except:
        CX = 'Z0.0'

#    print(E0m,E1m,E2m)
#    print(P1m,P2m,P2m)

        
    dumpLatestKp(wmdates,Kps,E1m,E2m,P1m,P2m,P3m,CX)
    

    
def dumpLatestKp(wmdates,Kps,E1,E2,P1,P2,P3,CX):
    f = open(outdir+wmfilename, "w")

    i=0
    for t,k in zip(wmdates,Kps):
        i+=1
        if i <= 8:
            f.writelines([str(t),' ',str(k),'\n'])
    f.writelines([str(E1),'\n'])
    f.writelines([str(E2),'\n'])
    f.writelines([str(P1),'\n'])
    f.writelines([str(P2),'\n'])
    f.writelines([str(P3),'\n'])
    f.writelines([CX,'\n'])

    f.close()
    
    return


    
def getLastKpIndices(t,dt,n):

    endtime = t
    starttime = endtime - (n+1)*dt
    
    startend = "start=" + starttime.strftime(swtimeformat) + "&end=" + endtime.strftime(swtimeformat)
    url = potsdamGetKp + startend  + "&index=Kp"

    result = requests.get(url).json()
    Kps = result['Kp']
    
    i = 1
    dates = []
    wmdates = []
    for sdate in result['datetime']:
        date = datetime.strptime(sdate,swtimeformat)
        dates.append(date)
        wmdates.append(date.strftime('%Y%m%d') + str(i))
        i+=1

    while (len(dates)>8):
        dates.pop(1)

    while (len(wmdates)>8):
        wmdates.pop(1)

    while (len(Kps)>8):
        Kps.pop(1)
        
    return  dates, wmdates, Kps
    

def getElectronFluxes(t,dt):
    endtime = t
    
    url = geosEspectra
    result = requests.get(url).json()

    E1flux = []
    E2flux = []
    E3flux = []
    E4flux = []
    E5flux = []
    E6flux = []
    E7flux = []
    E8flux = []
    E9flux = []
    E10flux = []
    meastime = []

    dE1 = 115-80
    dE2 = 165-115
    dE3 = 235-165
    dE4 = 340-235
    dE5 = 500-340
    dE6 = 700-500
    dE7 = 1000-700
    dE8 = 1900-1000
    dE9 = 3200-1900
    dE10 = 6500-3200
    
    for i in range(len(result)-1,-1,-1):
        achannel = result[i]
        atime = datetime.strptime(achannel['time_tag'],swtimeformat).replace(tzinfo=timezone.utc)
        if (endtime - atime < dt):
            match achannel['energy']:
                case '80-115 keV':
                    E1flux.append(dE1*achannel['flux'])
                case '115-165 keV':
                    E2flux.append(dE2*achannel['flux'])
                case '165-235 keV':
                    E3flux.append(dE3*achannel['flux'])
                case '235-340 keV':
                    E4flux.append(dE4*achannel['flux'])
                case '340-500 keV':
                    E5flux.append(dE5*achannel['flux'])
                case '500-700 keV':
                    E6flux.append(dE6*achannel['flux'])
                case '700-1000 keV':
                    E7flux.append(dE7*achannel['flux'])
                case '1000-1900 keV':
                    E8flux.append(dE8*achannel['flux'])
                case '1900-3200 keV':
                    E9flux.append(dE9*achannel['flux'])
                case '3200-6500 keV':
                    E10flux.append(dE10*achannel['flux'])
                case others:
                    print('energy channel missed: ',achannel['energy'])

            lastsaved = meastime[-1:]
            if lastsaved:
                if (atime != lastsaved[0]):
                    meastime.append(atime)
            else:
                meastime.append(atime)
    

#wmspaceweather has only two electron channels to display, let's bin
#the spectrum into ~non-relativisic (<800 KeV), relativistic (>800 KeV), only highly
#relativistic (>2MeV)

    Elowflux = [sum(x) for x in zip(E1flux,E2flux,E3flux,E4flux,E5flux,E6flux)]
    E800KeV = [sum(x) for x in zip(E7flux,E8flux,E9flux,E10flux)]
    E2MeV= [sum(x) for x in zip(E9flux,E10flux)]

    return meastime, Elowflux, E800KeV, E2MeV


def getProtonFluxes(t,dt):

    endtime = t
    
    url = geosPspectra
    result = requests.get(url).json()

    P1flux = []
    P2Aflux = []
    P2Bflux = []
    P3flux = []
    P4flux = []
    P5flux = []
    P6flux = []
    P7flux = []
    P8Aflux = []
    P8Bflux = []
    P8Cflux = []
    P9flux = []
    P10flux = []    
    meastime = []

    dP1 = 1860-1020
    dP2A = 2300-1900
    dP2B = 3340-2310
    dP3 = 6480-3400
    dP4 = 11000-5840
    dP5 = 23270-11640
    dP6 = 38100-25900
    dP7 = 73400-40300
    dP8A = 98500-83700
    dP8B = 118000-99900
    dP8C = 143000-115000
    dP9 = 242000-160000
    dP10 = 404000-276000
    
    for i in range(len(result)-1,-1,-1):
        achannel = result[i]
        atime = datetime.strptime(achannel['time_tag'],swtimeformat).replace(tzinfo=timezone.utc)
        if (endtime - atime < dt):
            match achannel['channel']:
                case 'P1':
                    P1flux.append(dP1*achannel['flux'])
                case 'P2A':
                    P2Aflux.append(dP2A*achannel['flux'])
                case 'P2B':
                    P2Bflux.append(dP2B*achannel['flux'])
                case 'P3':
                    P3flux.append(dP3*achannel['flux'])
                case 'P4':
                    P4flux.append(dP4*achannel['flux'])
                case 'P5':
                    P5flux.append(dP5*achannel['flux'])
                case 'P6':
                    P6flux.append(dP6*achannel['flux'])
                case 'P7':
                    P7flux.append(dP7*achannel['flux'])
                case 'P8A':
                    P8Aflux.append(dP8A*achannel['flux'])
                case 'P8B':
                    P8Bflux.append(dP8B*achannel['flux'])
                case 'P8C':
                    P8Cflux.append(dP8C*achannel['flux'])
                case 'P9':
                    P9flux.append(dP9*achannel['flux'])
                case 'P10':
                    P10flux.append(dP10*achannel['flux'])                                      
                case others:
                    print('energy channel missed: ',achannel['channel'])

            lastsaved = meastime[-1:]
            if lastsaved:
                if (atime != lastsaved[0]):
                    meastime.append(atime)
            else:
                meastime.append(atime)

    # The three channels of wmspaceweather(>10MeV, >50MeV, >100MeV)
    
    P10MeV = [sum(x) for x in zip(P5flux,P6flux,P7flux,P8Aflux,P8Bflux,P8Cflux,P9flux,P10flux)]
    P50MeV = [sum(x) for x in zip(P7flux,P8Aflux,P8Bflux,P8Cflux,P9flux,P10flux)]
    P100MeV = [sum(x) for x in zip(P8Bflux,P8Cflux,P9flux,P10flux)]
    return meastime, P10MeV, P50MeV, P100MeV

    
def getLatestXrays():
    
    url = geosXflares
    result = requests.get(url).json()[0]
    
    timemax = datetime.strptime(result['max_time'],swtimeformat).replace(tzinfo=timezone.utc)
    startime = datetime.strptime(result['begin_time'],swtimeformat).replace(tzinfo=timezone.utc)
    endtime = datetime.strptime(result['end_time'],swtimeformat).replace(tzinfo=timezone.utc)
    duration = endtime-startime
    
    return timemax, duration, result['max_class']
    




if __name__ == "__main__":
    main()   
