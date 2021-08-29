import time
from datetime import datetime
from threading import Thread
from collections import deque
import json
import sys
import socketserver

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

# def acceptThread():


class socketHander(socketserver.BaseRequestHandler):
    def handle(self):
        global qdata
        while(True):
            self.data = self.request.recv(1024).strip()
            if(self.data.decode()==""):
                break
            line = self.data.decode()
            if(line.strip() == "data"):
                #print the data
                try:
                    printing=True
                    tosend = qdata.copy()
                    for i in tosend:
                        self.request.sendall((str(i)[1:-1]).encode()+b"\n")
                    printing=False
                except:
                    sys.stderr.write("qdata Mutated\n")
                    sys.stderr.flush()
            elif(line.strip().startswith("pol")):
                try:
                    line = int(line.strip().replace("pol=",""))
                    samples_persec,delay = sliderToPointsAndSleep(line)
                    if samples_persec>len(qdata):
                        # We have increase the size of deq
                        qdata = deque([[0 for i in range(len(cpudata_og)+1)] for j in range(samples_persec - len(qdata))]+list(qdata),maxlen=samples_persec)
                        sys.stderr.write("Increased:"+str(len(qdata))+"\n")
                    elif(samples_persec<len(qdata)):
                        # We have to decrease size
                        qdata = deque(list(qdata)[-samples_persec:],maxlen=samples_persec)
                        sys.stderr.write("Decreased:"+str(len(qdata))+"\n")
                except:
                    sys.stderr.write("Malformed pol\n")
                    sys.stderr.flush()

def socketThread():
    HOST, PORT = "localhost", 9999
    with socketserver.ThreadingTCPServer((HOST, PORT), socketHander) as server:
        print("Listening on "+str(HOST)+" with port "+str(PORT))
        server.serve_forever()

cpudata_og = cpudata_og = parseCPUINFO()
qdata = deque([[0 for i in range(len(cpudata_og)+1)] for j in range(samples)],maxlen=samples)
mhz_lst=[]
run = True
#Thread -2 
t = Thread(target=watchdog)
t.start()

try:
    socketThread()
except KeyboardInterrupt:
    print("Bye...")
    run=False
    