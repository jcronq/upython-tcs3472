# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 13:43:11 2019

@author: jcron
"""
from scipy.interpolate import interp1d
import csv
import numpy as np
from matplotlib import pyplot as plt
from scipy.integrate import simps
from operator import add

delta = 10

inputData = {
        'wavelength': [],
        'r': [],
        'g': [],
        'b': [],
        'c': []
    }

with open('TCS3472ColorSensitivity.csv', newline='\n') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    for row in reader:
        inputData['wavelength'].append(float(row['WaveLength']))
        inputData['r'].append(float(row['R']))
        inputData['g'].append(float(row['G']))
        inputData['b'].append(float(row['B']))
        inputData['c'].append(float(row['C']))

interpKind = 'cubic'

rInterp = interp1d(inputData['wavelength'], inputData['r'], kind=interpKind)
gInterp = interp1d(inputData['wavelength'], inputData['g'], kind=interpKind)
bInterp = interp1d(inputData['wavelength'], inputData['b'], kind=interpKind)
cInterp = interp1d(inputData['wavelength'], inputData['c'], kind=interpKind)

interpXData =np.linspace(300, 1100, num=int((1100-300)/delta)+1, endpoint=True)

sunWave = [ 275, 375, 500, 700, 750, 1000, 1250, 1500 ]
sunPower = [  0, 0.5,1.35, 1.3,   1, 0.75, 0.48, .035 ]

red  = list(range(570, 690, delta))
green= list(range(490, 570, delta))
blue = list(range(300, 490, delta))
ir = list(range(690, 1110, delta))

sunInterpX = np.linspace( 275, 1500, num=int((1500-275)/delta), endpoint = True)
sunInterp = interp1d(sunWave, sunPower, kind='cubic')

plt.plot( sunWave, sunPower, 'o', sunInterpX, sunInterp(sunInterpX) )
plt.show()

r = rInterp(interpXData)
g = gInterp(interpXData)
b = bInterp(interpXData)
c = cInterp(interpXData)

def maxZero(x):
    return max(x, 0)

len(interpXData)

r = list(map(maxZero, r))
g = list(map(maxZero, g))
b = list(map(maxZero, b))
c = list(map(maxZero, c))

rgb = list(map(add, b, list(map(add,r,g))))

plt.plot( interpXData, r, 
         interpXData, g, 
         interpXData, b,
         interpXData, rgb,
         interpXData, c)
plt.legend(['r', 'g', 'b', 'r+g+b', 'c'])
plt.show()

rArea = simps(r, dx=delta)
gArea = simps(g, dx=delta)
bArea = simps(b, dx=delta)
cArea = simps(c, dx=delta)

rRangeR = list(map(maxZero, rInterp(red)))
rRangeG = list(map(maxZero, gInterp(red)))
rRangeB = list(map(maxZero, bInterp(red)))
rRangeC = list(map(maxZero, cInterp(red)))

gRangeR = list(map(maxZero, rInterp(green)))
gRangeG = list(map(maxZero, gInterp(green)))
gRangeB = list(map(maxZero, bInterp(green)))
gRangeC = list(map(maxZero, cInterp(green)))

bRangeR = list(map(maxZero, rInterp(blue)))
bRangeG = list(map(maxZero, gInterp(blue)))
bRangeB = list(map(maxZero, bInterp(blue)))
bRangeC = list(map(maxZero, cInterp(blue)))

irRangeR = list(map(maxZero, rInterp(ir)))
irRangeG = list(map(maxZero, gInterp(ir)))
irRangeB = list(map(maxZero, bInterp(ir)))
irRangeC = list(map(maxZero, cInterp(ir)))

rAreaRInfluence = simps(rRangeR, dx=delta)
rAreaGInfluence = simps(rRangeG, dx=delta)
rAreaBInfluence = simps(rRangeB, dx=delta)
rAreaCInfluence = simps(rRangeC, dx=delta)

gAreaRInfluence = simps(gRangeR, dx=delta)
gAreaGInfluence = simps(gRangeG, dx=delta)
gAreaBInfluence = simps(gRangeB, dx=delta)
gAreaCInfluence = simps(gRangeC, dx=delta)

bAreaRInfluence = simps(bRangeR, dx=delta)
bAreaGInfluence = simps(bRangeG, dx=delta)
bAreaBInfluence = simps(bRangeB, dx=delta)
bAreaCInfluence = simps(bRangeC, dx=delta)

irAreaRInfluence = simps(irRangeR, dx=delta)
irAreaGInfluence = simps(irRangeG, dx=delta)
irAreaBInfluence = simps(irRangeB, dx=delta)
irAreaCInfluence = simps(irRangeC, dx=delta)

rAreaSum = rAreaRInfluence + rAreaGInfluence + rAreaBInfluence + rAreaCInfluence
gAreaSum = gAreaRInfluence + gAreaGInfluence + gAreaBInfluence 
bAreaSum = bAreaRInfluence + bAreaGInfluence + bAreaBInfluence 
irAreaSum = irAreaRInfluence + irAreaGInfluence + irAreaBInfluence 

cSum = rAreaCInfluence + gAreaCInfluence + bAreaCInfluence + irAreaCInfluence

redWeight = { 
        "r": rAreaRInfluence / rAreaSum, 
        "g": rAreaGInfluence / rAreaSum, 
        "b": rAreaBInfluence / rAreaSum 
    }

greenWeight = { 
        "r": gAreaRInfluence / gAreaSum, 
        "g": gAreaGInfluence / gAreaSum, 
        "b": gAreaBInfluence / gAreaSum 
    }

blueWeight = {
        "r": bAreaRInfluence / bAreaSum, 
        "g": bAreaGInfluence / bAreaSum, 
        "b": bAreaBInfluence / bAreaSum        
    }

irWeight = {
        "r": irAreaRInfluence / irAreaSum, 
        "g": irAreaGInfluence / irAreaSum, 
        "b": irAreaBInfluence / irAreaSum        
    }

cSensitivity = {
        "r":  rAreaCInfluence / cSum,
        "g":  gAreaCInfluence / cSum,
        "b":  bAreaCInfluence / cSum,
        "ir": irAreaCInfluence / cSum,
    }

rgbArea = rArea + gArea + bArea 

p = (rgbArea - cArea)/ cArea
print(p)

print(rArea, gArea, bArea)

