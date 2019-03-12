﻿#!/python
# -*- coding: utf-8 -*-

### http://sametmax.com/lencoding-en-python-une-bonne-fois-pour-toute/
from __future__ import unicode_literals
### https://www.systutorials.com/241727/how-to-print-a-line-to-stderr-and-stdout-in-python/
# Permet en python 2.7 print("your message", file=sys.stderr) comme en Python 3
from __future__ import print_function
# http://python-future.org/compatible_idioms.html#long-integers
from builtins import int
# from past.builtins import long

"""
Construire une structure de donnees,
liste ordonnee (clef = timestamp) de 
structure des informations dispo entre 2 timestamps
"""

# Pour calcul de distance...
from math import sin, cos, acos, pi

import cgitb
cgitb.enable(format='text')
import pyodbc
import sqlite3
import hashlib
### http://sweetohm.net/article/introduction-yaml.html
import yaml
### https://docs.python.org/fr/2/tutorial/inputoutput.html#reading-and-writing-files
### http://sametmax.com/faire-manger-du-datetime-a-json-en-python/
import json
import sys
import os
# import shutil
#import string
import pathlib
import argparse
import configparser
import re
#from collections import OrderedDict
import collections
import time
import datetime
import decimal

decimal.getcontext().prec = 2
TAB = '\t'
FileOutSep = TAB
FileOutHeader = False
Verbose = True
#dIni['verbose'] = Verbose
dtNow  = datetime.datetime.today()
tsNow = dtNow.timestamp()
dt1970 = datetime.datetime(1970, 1, 1)


# LatLonPrefered = "RMC"
LatLonPrefered = "GLL"


#bShowIdentifier = os.getenv("dsXidentifier", False)

## fichier a traiter
me = sys.argv[0]
#args = sys.argv[1:]
if (len(sys.argv) != 3) :
    print(me + " : Pas le bon nombre de parametres.", file=sys.stderr)
    print("Usage : " + me + " <Chemin et nom du fichier NMEA> <identifiant nmea reference de temps (GPRMC, IIGLL, ..)>", file=sys.stderr)
    quit()
else :
    nmeaFilename = sys.argv[1]
    srcEpoch = sys.argv[2]
    if (srcEpoch[0:1] == "$") :
        srcEpoch = srcEpoch[1:]
    srcEpoch = srcEpoch.upper()
    if (len(srcEpoch) == 5) :
        print("I;Reference de temps a partir de NMEA [" + srcEpoch + "] depuis le ficher NMEA [" + nmeaFilename + "]", file=sys.stderr)
    else :
        print(me + " ", file=sys.stderr)
        print("Usage : " + me + " <Chemin et nom du fichier NMEA> <identifiant nmea reference de temps (GPRMC, IIZDA, ..)>", file=sys.stderr)
        quit()

## Tests prealables, fichier NMEA 
if (not os.path.exists(nmeaFilename)) :
    print("E:Fichier", nmeaFilename, "introuvable", file=sys.stderr)
    quit()

## TS ISO8601 epoch
iso8601 = time.strftime("%Y%m%d%H%M%S")
epoch = int(time.time())
# print(datetime.datetime.now().isoformat()) # 2017-10-31T10:52:02.101865
# print(time.strftime("%Y-%m-%d %H:%M:%S")) # 2017-10-31 10:52:02
# print(int(time.time())) # 1509443642

## Informations sur le fichier a importer
BLOCKSIZE = 65536
hasher = hashlib.md5()
with open(nmeaFilename, 'rb') as afile:
    buf = afile.read(BLOCKSIZE)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(BLOCKSIZE)
#print(hasher.hexdigest())
fileCheck = hasher.hexdigest()

mTimeEpoch = int(os.path.getmtime(nmeaFilename)) # format epoch
# print("mTimeEpoch : " + str(mTimeEpoch))
# print(datetime.datetime.utcfromtimestamp(mTimeEpoch)) # 2017-10-19 13:40:11
mTimeStruct = time.localtime(mTimeEpoch)
# print("mTimeStruct : " + str(mTimeStruct)) # mTimeLocal : time.struct_time(tm_year=2017, tm_mon=10, tm_mday=19, tm_hour=15, tm_min=40, tm_sec=11, tm_wday=3, tm_yday=292, tm_isdst=1)
mTimeIso = time.strftime("%Y%m%d%H%M%S", mTimeStruct)
# print("mTimeIso : " + mTimeIso)
basename = os.path.basename(nmeaFilename)

##
## (option) Timestamp en epoch au début et/ou en TS à la fin de chaque ligne NMEA
##

##  Place disponible (2 x la taille du fichier)
# nmeaFilenameSize = os.path.getsize(nmeaFilename)
nmeaFilenameName, nmeaFilenameExtension = os.path.splitext(nmeaFilename)
# print("", )
# shutil.copyfile(nmeaFilename, )

## Quelle information NMEA est la plus pertinente a utiliser ?
## RMC et ZDA
"""
$GPRMC,193428,A,4729.9205,N,00222.6770,W,0.0,143.5,200917,2.9,W,D*1C

       1         2 3       4 5        6 7   8   9    10  11|
       |         | |       | |        | |   |   |    |   | |
$--RMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,xxxx,x.x,a*hh
1) Time (UTC)
2) Status, V = Navigation receiver warning
3) Latitude
4) N or S
5) Longitude
6) E or W
7) Speed over ground, knots
8) Track made good, degrees true
9) Date, ddmmyy
10) Magnetic Variation, degrees
11) E or W
12) Checksum
$GPRMC	055827.000,A,4715,0596,N,131,7996,W,23,3,356,0,261115,,,N*43
$GPRMC	055927.000,A,4715,3027,N,131,7799,W,13,6,5,0,261115,,,N*4C

$IIZDA,hhmmss.ss,xx,xx,xxxx,,*hh
       I         I  I  I_Année
       I         I  I_Mois
       I         I_jour
       I_Heure
$IIZDA	194020,20,09,2017,,*5E
$IIZDA	152520,07,07,2017,,*5A

!AIVDM, !AIVDO, $AIALR, $AITXT
$GPAPB, $GPBOD, $GPGBS, $GPGGA, $GPGLL, $GPGSA, $GPGSV, $GPRMB, $GPRMC, $GPRTE, $GPTXT, $GPVTG, $GPWPL
$IIDBT, $IIDPT, $IIGLL, $IIHDG, $IIHDM, $IIMTA, $IIMTW, $IIMWD, $IIMWV, $IIVHW, $IIVLW, $IIVTG, $IIVWR, $IIVWT, $IIZDA
$PMGNS, $PSRT
"""
dJson = dict()
dJson['name'] = basename
dJson['check'] = fileCheck
dJson['mTime'] = mTimeIso
dJson['nmeaFilename'] = nmeaFilename

dRMCs = dict()
candidatVoulu = 'ZDA'

dPivots = dict()

dPivotsSorted = collections.OrderedDict()
"""
!AIVDM, !AIVDO, $AIALR, $AITXT
$GPAPB, $GPBOD, $GPGBS, $GPGGA, $GPGLL, $GPGSA, $GPGSV, $GPRMB, $GPRMC, $GPRTE, $GPTXT, $GPVTG, $GPWPL
$IIDBT, $IIDPT, $IIGLL, $IIHDG, $IIHDM, $IIMTA, $IIMTW, $IIMWD, $IIMWV, $IIVHW, $IIVLW, $IIVTG, $IIVWR, $IIVWT, $IIZDA
$PMGNS, $PSRT
"""

def getDictEpoch() :
    dPivot = dict()
    dPivot['ts'] = None #0.0
    # dPivot['lat'] = None #0.0
    # dPivot['lon'] = None #0.0
    # dPivot['d-1'] = None #0
    # dPivot['d+10'] = None #0
    # dPivot['d+60'] = None #0
    # dPivot['ZDAepoch'] = None #0
    dPivot['ECAPB'] = None
    dPivot['GPAPB'] = None
    dPivot['BOD'] = None
    dPivot['DBT'] = None #0.0
    # dPivot['DPT'] = None
    # dPivot['HDG'] = None #0.0
    dPivot['HDM'] = None #0.0
    # dPivot['GBS'] = None
    # dPivot['GGA'] = None
    # dPivot['GLL'] = None #""
    dPivot['GLLlatNum'] = None #0.0
    dPivot['GLLlonNum'] = None #0.0
    # dPivot['GSA'] = None
    # dPivot['GSV'] = None
    # dPivot['HDG'] = None #0.0
    dPivot['HDM'] = None #0.0
    dPivot['MTA'] = None #0.0
    dPivot['MTW'] = None #0.0
    dPivot['MWD'] = None
    dPivot['MWDtws'] = None #0.0
    dPivot['MWDtwd'] = None #0.0
    dPivot['MWV'] = None
    dPivot['ECRMB'] = None
    dPivot['GPRMB'] = None
    # dPivot['RMC'] = None
    dPivot['GPRMCts'] = None #0
    dPivot['GPRMClatlon'] = None #""
    dPivot['GPRMClatNum'] = None #0.0
    dPivot['GPRMClonNum'] = None #0.0
    dPivot['GPRMCsog'] = None #0.0
    dPivot['GPRMCtmg'] = None #0.0
    # dPivot['RTE'] = None
    # dPivot['TXT'] = None
    dPivot['VHW'] = None
    dPivot['VLW'] = None #0.0
    dPivot['VLWtotal'] = None #0.0
    dPivot['VTG'] = None
    dPivot['VWR'] = None
    dPivot['VWRrl'] = None #""
    dPivot['VWRawa'] = None #0.0
    dPivot['VWRaws'] = None #0.0
    dPivot['VWT'] = None
    dPivot['VWTrl'] = None #""
    dPivot['VWTtwa'] = None #0.0
    dPivot['VWTtws'] = None #0.0
    # dPivot['WPL'] = None
    dPivot['ZDA'] = None
    # dPivot[''] = None
    # dPivot[''] = None
    # dPivot[''] = None
    # dPivot[''] = None
    # dPivot[''] = None
    # dPivot[''] = None
    # dPivot[''] = None
    # dPivot[''] = None
    return dPivot

def dms2dd(d, m, s):
    """Convertit un angle "degrés minutes secondes" en "degrés décimaux"
    """
    return d + m/60 + s/3600
 
def dd2dms(dd):
    """Convertit un angle "degrés décimaux" en "degrés minutes secondes"
    """
    d = int(dd)
    x = (dd-d)*60
    m = int(x)
    s = (x-m)*60
    return d, m, s
 
def deg2rad(dd):
    """Convertit un angle "degrés décimaux" en "radians"
    """
    return dd/180*pi
 
def rad2deg(rd):
    """Convertit un angle "radians" en "degrés décimaux"
    """
    return rd/pi*180
 
def distanceGPS(latA, longA, latB, longB):
    """Retourne la distance en mètres entre les 2 points A et B connus grâce à
       leurs coordonnées GPS (en radians).
    """
    # Rayon de la terre en mètres (sphère IAG-GRS80) WGS84
    RT = 6378137
    # angle en radians entre les 2 points
    S = acos(sin(latA)*sin(latB) + cos(latA)*cos(latB)*cos(abs(longB-longA)))
    # distance entre les 2 points, comptée sur un arc de grand cercle
    return S * RT
 
def DMd2Dd(dmd) :
    # DDDMM.d --> DDD.d (S or W negative values)
    # 10601.6986 ---> 106+1.6986/60 = 106.02831 degrees
    # "GLL": "4730.189,N,223.183,W"
    # 0.001 represente 110m x 78m (lat 45°)
    # 0.0001 represente 11m x 7/8m
    dotPos = dmd.find(".")
    D = float(dmd[0:dotPos - 2])
    M = float(dmd[dotPos - 2:]) / 60
    return (round(D + M, 6))

def getDtFromNmeaLine(line) :
    global dt1970
    candidat = line[3:6]
    if (candidat == 'RMC') :
        lTmp = line.split(",")
        # $GPRMC,072648.00,A,4730.18648,N,00223.18287,W,0.049,46.36,010618,,,A*43
        ts = float("20" + lTmp[9][4:6] + lTmp[9][2:4] + lTmp[9][0:2] + lTmp[1][0:2] + lTmp[1][2:4] + lTmp[1][4:])
        dt = datetime.datetime(2000 + int(lTmp[9][4:6]), int(lTmp[9][2:4]), int(lTmp[9][0:2]), int(lTmp[1][0:2]), int(lTmp[1][2:4]), int(lTmp[1][4:6]), int(lTmp[1][7:]))
        ep = (dt - dt1970).total_seconds()
        # print("epoch : [", ep, "]", file=sys.stderr)
        return (ts, dt, ep)
    if (candidat == 'ZDA') :
        lTmp = line.split(",")
        # $IIZDA,121644,01,06,2018,,*57
        ts = float(lTmp[4] + lTmp[3] + lTmp[2] + lTmp[1][0:2] + lTmp[1][2:4] + lTmp[1][4:6])
        dt = datetime.datetime(int(lTmp[4]), int(lTmp[3]), int(lTmp[2]), int(lTmp[1][0:2]), int(lTmp[1][2:4]), int(lTmp[1][4:6]))
        ep = (dt - dt1970).total_seconds()
        # print("epoch : [", ep, "]", file=sys.stderr)
        return (ts, dt, ep)

def xtrInfos(candidat, line, dP) :
    lTmp = line.split(',')
    """
    !AIVDM, !AIVDO, $AIALR, $AITXT
    $GPAPB, $GPBOD, $GPGBS, $GPGGA, $GPGLL, $GPGSA, $GPGSV, $GPRMB, $GPRMC, $GPRTE, $GPTXT, $GPVTG, $GPWPL
    $IIDBT, $IIDPT, $IIGLL, $IIHDG, $IIHDM, $IIMTA, $IIMTW, $IIMWD, $IIMWV, $IIVHW, $IIVLW, $IIVTG, $IIVWR, $IIVWT, $IIZDA
    $PMGNS, $PSRT
    """
    # if () :
        # dp[candidat] =
        # return candidat + " = " +
    """   
    # $GPAPB,,,,,,,,,,,,,,*44    APB - Autopilot Sentence "B"
    Field Number:
        Status V = Loran-C Blink or SNR warning V = general warning flag or other navigation systems when a reliable fix is not available
        Status V = Loran-C Cycle Lock warning flag A = OK or not used
        Cross Track Error Magnitude
        Direction to steer, L or R
        Cross Track Units, N = Nautical Miles
        Status A = Arrival Circle Entered
        Status A = Perpendicular passed at waypoint
        Bearing origin to destination -->     
        M = Magnetic, T = True
        Destination Waypoint ID
        Bearing, present position to Destination -->    
        M = Magnetic, T = True 
        Heading to steer to destination waypoint -->    
        M = Magnetic, T = True
        Checksum
    Example: $GPAPB,A,A,0.10,R,N,V,V,011,M,DEST,011,M,011,M*82
    """
    
    # $GPBOD,,T,,M,ATT VILAIN,ATT-PALAIS*59     BOD - Bearing - Waypoint to Waypoint   ! is NOT updated dynamically! 
    
    # $GPGBS,072627.00,4.3,2.8,8.6,,,,*44    GBS - GPS Satellite Fault Detection
    
    # $GPGGA,072844.000,4714.3220,N,00131.5485,W,1,08,1.6,36.2,M,48.5,M,,0000*78    GGA - Global Positioning System Fix Data
    
    # $GPGSA,A,3,05,07,08,13,15,18,20,21,24,28,30,37,1.5,1.0,1.1*38    GSA - GPS DOP and active satellites
    
    # $GPGSV,3,2,12,22,59,065,38,01,53,117,46,17,51,276,,23,45,180,39*7F    GSV - Satellites in view
    
    """
    # $GPRMB,V,,,ATT-PAL,ATT VI,4730.3500,N,00231.7540,W,,,,V,N*62    RMB - Recommended Minimum Navigation Information
        Status, A= Active, V = Void
        Cross Track error - nautical miles
        Direction to Steer, Left or Right
        TO Waypoint ID
        FROM Waypoint ID
        Destination Waypoint Latitude
        N or S
        Destination Waypoint Longitude
        E or W
        Range to destination in nautical miles
        Bearing to destination in degrees True
        Destination closing velocity in knots
        Arrival Status, A = Arrival Circle Entered
        FAA mode indicator (NMEA 2.3 and later)
        Checksum
    Example: $GPRMB,A,0.66,L,003,004,4917.24,N,12309.57,W,001.3,052.5,000.5,V*0B
    """
    
    # $GPRTE,1,1,c,VIL LE PALAIS,ATT-PALAIS,ATT VILAIN*75    RTE - Routes
    
    # $GPWPL,4721.3270,N,00308.6350,W,ATT-PALAIS*3E
    
    # 
    if (candidat == 'ECAPB' and lTmp[1] == 'A' and lTmp[2] == 'A') :
        dp['ECAPB'] = line
        return candidat + " = " + line 
    if (candidat == 'GPAPB' and lTmp[1] == 'A' and lTmp[2] == 'A') :
        dp['GPAPB'] = line
        return candidat + " = " + line
    if (candidat == 'ECRMB' and lTmp[1] == 'A') :
        dp['ECRMB'] = line
        return candidat + " = " + line
    if (candidat == 'GPRMB' and lTmp[1] == 'A') :
        dp['GPRMB'] = line
        return candidat + " = " + line

    if (candidat == 'IIVHW') :
        dP['VHW'] = float(lTmp[5])
        return candidat + " = " + lTmp[5] + " dans " + line
    if (candidat == 'IIVLW') :
        dP['VLW'] = float(lTmp[3])
        dP['VLWtotal'] = float(lTmp[1])
        return candidat + " = " + lTmp[3] + " VLWtotal = " + lTmp[1] + " dans " + line
    if (candidat == 'IIDBT') :
        dP['DBT'] = float(lTmp[3])
        return candidat + " = " + lTmp[3] + " dans " + line
    if (candidat == 'IIMTW') :
        dP['MTW'] = float(lTmp[1])
        return candidat + " = " + lTmp[1] + " dans " + line
    if (candidat == 'IIVWR') :
        dP['VWRrl'] = lTmp[2]
        if (lTmp[2] == 'L') :
            dP['VWRawa'] = -float(lTmp[1])
        else :
            dP['VWRawa'] = float(lTmp[1])
        dP['VWRaws'] = float(lTmp[3])
        return candidat + " VWRawa = " + str(dP['VWRawa']) + " VWRrl = " + lTmp[2] + " VWRaws = " + lTmp[3] + " dans " + line
    if (candidat == 'IIMWD') :
        dP['MWDtwd'] = float(lTmp[3])
        dP['MWDtws'] = float(lTmp[5])
        return candidat + " MWDtwd = " + lTmp[3] + " MWDtws = " + lTmp[5] + " dans " + line
    if (candidat == 'IIVWT') :
        dP['VWTrl'] = lTmp[2]
        if (lTmp[2] == 'L') :
            dP['VWTtwa'] = -float(lTmp[1])
        else :
            dP['VWTtwa'] = float(lTmp[1])
        dP['VWTtws'] = float(lTmp[3])
        return candidat + " VWTtwa = " + str(dP['VWTtwa']) + " VWTrl = " + lTmp[2] + " VWTtws = " + lTmp[3] + " dans " + line
    if (candidat == 'IIMTA') :
        dP['MTA'] = float(lTmp[1])
        return candidat + " = " + lTmp[1] + " dans " + line
    if (candidat == 'IIHDM') :
        dP['HDM'] = float(lTmp[1])
        return candidat + " = " + lTmp[1] + " dans " + line
    if (candidat == 'IIGLL') :
        # $GPGLL,4740.2898,N,00321.2259,W,083718,A,A*50
        if (lTmp[6] == 'A') :
            dP[candidat] = str(float(lTmp[1])) + "," + lTmp[2] + "," + str(float(lTmp[3])) + "," + lTmp[4]
            if (lTmp[2] == 'S') :
                dP['GLLlatNum'] = DMd2Dd("-" + lTmp[1]) #float("-" + lTmp[1]) / 100.0
            else :
                dP['GLLlatNum'] = DMd2Dd(lTmp[1]) #float(lTmp[1]) / 100.0
            if (lTmp[4] == 'W') :
                dP['GLLlonNum'] = DMd2Dd("-" + lTmp[3]) #float("-" + lTmp[3]) / 100.0
            else :
                dP['GLLlonNum'] = DMd2Dd(lTmp[3]) #float(lTmp[3]) / 100.0
            return candidat + " = " +  dP[candidat] + " dans " + line
        else :
            return None
    if (candidat == 'IIMWV') :
        # $IIMWV,255,R,03.0,N,A*12
        return candidat + " = pas necessaire"
    if (candidat == 'IIHDG') :
        # $IIHDG,328.,,,,*70
        return candidat + " = pas necessaire car HDM present"
    if (candidat == 'IIVTG') :
        # $IIVTG,046.,T,,M,03.5,N,06.5,K,A*2D
        return candidat + " = pas necessaire"
    if (candidat == 'IIDPT') :
        # $IIDPT,0001.9,,*7A
        return candidat + " = pas necessaire"
    if (candidat == 'GPRMC' or candidat == 'ECRMC' or candidat == 'IIRMC') :
        # $GPRMC,091930.00,A,4728.86549,N,00232.55440,W,5.248,201.64,010618,,,D*73
        ##  Info de nav, vont dans le dict() general
        if (lTmp[7] != "") :
            dP['GPRMCsog'] = lTmp[7]
        if (lTmp[8] != "") :
            dP['GPRMCtmg'] = lTmp[8]#round(float(lTmp[8]), 0)
        # dPivot['GPRMCts'] = None #0
        # dPivot['GPRMClatlon'] = None #""
        # dPivot['GPRMClatNum'] = None #0.0
        # dPivot['GPRMClonNum'] = None #0.0

            
            
        return candidat + " = SOG et TMG"
    if (candidat == 'GPGBS') :
        # $GPGBS,091930.00,1.6,1.5,2.8,,,,*4A
        return candidat + " = pas necessaire"
    if (candidat == 'IIVTG') :
        # $IIVTG,046.,T,,M,03.5,N,06.5,K,A*2D
        return candidat + " = pas necessaire"
    return None

def getEpochFromGPRMC(line) :
    global dt1970
    lTmp = line.split(",")
    # $GPRMC,072648.00,A,4730.18648,N,00223.18287,W,0.049,46.36,010618,,,A*43
    ts = float("20" + lTmp[9][4:6] + lTmp[9][2:4] + lTmp[9][0:2] + lTmp[1][0:2] + lTmp[1][2:4] + lTmp[1][4:] + ".0")
    dt = datetime.datetime(2000 + int(lTmp[9][4:6]), int(lTmp[9][2:4]), int(lTmp[9][0:2]), int(lTmp[1][0:2]), int(lTmp[1][2:4]), int(lTmp[1][4:6]), int(lTmp[1][7:]))
    ep = (dt - dt1970).total_seconds() + 0.0
    # print("epoch : [", ep, "]", file=sys.stderr)
    return (ts, ep)

def getEpochFromECRMC(line) :
    return (getEpochFromGPRMC(line))

def getEpochFromIIZDA(line) :
    global dt1970
    lTmp = line.split(",")
    # $IIZDA,121644,01,06,2018,,*57
    ts = float(lTmp[4] + lTmp[3] + lTmp[2] + lTmp[1][0:2] + lTmp[1][2:4] + lTmp[1][4:6] + ".0")
    dt = datetime.datetime(int(lTmp[4]), int(lTmp[3]), int(lTmp[2]), int(lTmp[1][0:2]), int(lTmp[1][2:4]), int(lTmp[1][4:6]))
    ep = (dt - dt1970).total_seconds() + 0.0
    print("ZDA [", line, "] ts", ts, "    ep", ep, file=sys.stderr)
    return (ts, ep)
    
# dPivot = getDictEpoch()
nbrGll = nbrRmc = nbrRmcUsed = nbrGllAndRmc = 0
ts = ep = 0        
with open(nmeaFilename, 'r') as fNmea :
    nLineRaw = nLine = 0
    for line in fNmea.readlines() :
        candidat = ""
        nLineRaw += 1
        line = line.rstrip()
        if (line == "") :
            continue
        if (line[0:3] == "!AI") :
            # !AIVDO,1,1,,,B3HvFrP0;?u7vh6jtRVhkwi5wP06,0*03
            continue
        nLine += 1
        if (line[0:1] == "$") :
            candidat = line[1:6]
            # print("candidat ? [" + candidat + "]" + TAB + "[" + srcEpoch + "]")
            # print("ep", ep, "       line", line)
            if (candidat == srcEpoch) :
                ##  ? Reference de temps ?
                # print("candidat == srcEpoch")
                if   (candidat == "GPRMC") :
                    (ep, ts) = getEpochFromGPRMC(line)
                elif (candidat == "ECRMC") :
                    (ep, ts) = getEpochFromECRMC(line)
                elif (candidat == "IIZDA") :
                    (ep, ts) = getEpochFromIIZDA(line)
                else :
                    print("E;Reference de temps a partir de NMEA [" + srcEpoch + "] non geree", file=sys.stderr)
                    quit()
                # print("ep", ep, TAB, "ts", ts)
                if (not ep in dPivotsSorted and ep > 0) :
                    pass
                elif (not round(ep + 0.1, 1) in dPivotsSorted) :
                    ep = round(ep + 0.1, 1)
                    ts = round(ts + 0.1, 1)
                elif (not round(ep + 0.2, 1) in dPivotsSorted) :
                    ep = round(ep + 0.2, 1)
                    ts = round(ts + 0.2, 1)
                elif (not round(ep + 0.3, 1) in dPivotsSorted) :
                    ep = round(ep + 0.3, 1)
                    ts = round(ts + 0.3, 1)
                elif (not round(ep + 0.4, 1) in dPivotsSorted) :
                    ep = round(ep + 0.4, 1)
                    ts = round(ts + 0.4, 1)
                elif (not round(ep + 0.5, 1) in dPivotsSorted) :
                    ep = round(ep + 0.5, 1)
                    ts = round(ts + 0.5, 1)
                else :
                    # On n'a jamais vu ce truc...
                    pass
                ##  Fourniture d'un dictionnaire dont les clefs sont prérenseignées, et les valeurs a None
                dPivotsSorted[ep] = getDictEpoch()
                dPivotsSorted[ep]['ts'] = ts
            
            # print("!ep2", ep)
            ##  Extraire les infos de la ligne, pour les affecter au dictionnaire de la periode de temps en cours
            # Fonction generique de traitement du candidat
            if (ep != 0) :
                retCode = xtrInfos(candidat, line, dPivotsSorted[ep])
                if (retCode is None) :
                    pass
                    # print("Traitement non prevu pour candidat :", line, file=sys.stderr)
                    # TODO
                    
                    
                    
                else :
                    pass
                    print("retCode :", retCode, file=sys.stderr)
   








for k in dPivotsSorted :
    print(dPivotsSorted[k])
