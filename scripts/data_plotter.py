# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 18:25:56 2019

@author: jcron
"""

import csv
import matplotlib.pyplot as plt
from datetime import datetime

columns = ["red", 'green', 'blue', 'clear', 'ct', 'ct_alt', 'timestamp']

data = {
        "ct": [],
        "timestamp": []
    }

count = 0

with open('Y:/raw.csv', newline='\n') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        data['ct'].append(row[5])
        ts = datetime.strptime(row[6].split('.')[0],"%Y-%m-%dT%H:%M:%S")
        data['timestamp'].append(ts)
        count += 1
        if count > 10:
            break

print("data arrays created")

plt.figure(1)
plt.plot(range(0,len(data['ct'])), data['ct'])
plt.show()