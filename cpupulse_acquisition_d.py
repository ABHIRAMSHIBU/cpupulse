import time
from datetime import datetime
from threading import Thread
from collections import deque
import json
import sys

printing=False # Binary semaphore. (mutex)

def parseCPUINFO():
    f = open("/proc/cpuinfo")
    data = f.read().split("\n\n")
    data.pop()
    data = [i.split("\n") for i in data]
    output =[]
    for i in data:
        d={}
        for j in i:
            k = [x.strip() for x in j.split(":")]
            d[k[0]]=k[1]
        output.append(d)
    f.close()
    return output

def sliderToPointsAndSleep(pollsPerSec):
    # 2 hrs
    t = 2*60*60*pollsPerSec
    sleepTime= 1/pollsPerSec
    return t,sleepTime

# Parameters
samples,delay = sliderToPointsAndSleep(1)

def watchdog():
    #Thread -2 Code
    
    while(run):
        timestarted = datetime.now()
        # data aquisition...
        # Spool the data
        # DATA Processing
        timestamp=datetime.now()
        cpudata = parseCPUINFO()
        timestamp_1 = datetime.now()-timestamp
        timestamp_1/=2
        timestamp=timestamp+timestamp_1
        mhz_dict = {"time":timestamp.__str__()[10:],0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
        for i in cpudata:
            mhz_dict[int(i['processor'])] = float(i["cpu MHz"])
        mhz_lst = list(mhz_dict.values())
        while(printing):
            time.sleep(0.0001)
        qdata.append(mhz_lst)
        timedelta = (datetime.now() - timestarted)
        sleeptime = delay - (timedelta.seconds + timedelta.microseconds/10**6)
        if(sleeptime<=0):
            pass
            sys.stderr.write("ERROR\n")
        else:
            time.sleep(sleeptime)

cpudata_og = cpudata_og = parseCPUINFO()
qdata = deque([[0 for i in range(len(cpudata_og)+1)] for j in range(samples)],maxlen=samples)
mhz_lst=[]
run = True
#Thread -2 
t = Thread(target=watchdog)
t.start()

try:
    #Thread -1
    while(True):
        line = input()
        if(line.strip() == "data"):
            #print the data
            try:
                printing=True
                for i in qdata:
                    print(str(i)[1:-1])
                printing=False
            except:
                sys.stderr.write("qdata Mutated")
                sys.stderr.flush()
        elif(line.strip().startswith("pol")):
            line = int(line.strip().replace("pol=",""))
            samples_persec,delay = sliderToPointsAndSleep(line)
            
            if samples_persec>len(qdata):
                # We have increase the size of deq
                qdata = deque([[0 for i in range(len(cpudata_og)+1)] for j in range(samples_persec - len(qdata))]+list(qdata),maxlen=samples_persec)
                print("Increased:",len(qdata))
            elif(samples_persec<len(qdata)):
                # We have to decrease size
                qdata = deque(list(qdata)[-samples_persec:],maxlen=samples_persec)
                print("Decreased:",len(qdata))
except KeyboardInterrupt:
    print("Bye...")
    run=False
    