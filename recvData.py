import subprocess as sp
from pprint import pprint
import time
import numpy as np
from threading import Thread
import streamlit as st
import plotly.express as px

process = None
thread = None

st.set_page_config(page_title="CPU Pulse", page_icon=None, layout='wide', initial_sidebar_state='collapsed')
pollRate=1
q=[]
run=True
def sliderToPointsAndSleep(pollsPerSec):
    # 2 hrs
    t = 2*60*60*pollsPerSec
    sleepTime= 1/pollsPerSec
    return t,sleepTime

def readProcessDataAndQ():
    while(run):
        q.append(process.stdout.readline())

def askData():
    global process
    q.clear()
    process.stdin.write(b"data\n")
    process.stdin.flush()
    l=[]
    counter=1
    while(True):
        if(len(q)==sliderToPointsAndSleep(pollRate)[0]):
            for i in q:
                l.append([j.strip() for j in i.decode().split(",")])
            q.clear()
            break
        else:
            counter+=1
            if(counter>10):
                q.clear()
                break
            else:
                time.sleep(0.01)
    if(len(l)!=0):
        data=[]
        timestamp=[]
        for i in l:
            data.append(i[1:])
            timestamp.append(i[0])
        return (np.asarray(data,dtype=np.float64),np.array(timestamp))
    else:
        return None

def setPoll(polling):
    global pollRate
    pollRate = polling
    process.stdin.write(b"pol="+str(polling).encode()+b"\n")


def cacher():
    global process
    global thread
    process = sp.Popen("python3 cpupulse_acquisition_d.py",stdin=sp.PIPE,stdout=sp.PIPE,shell=True)
    thread = Thread(target=readProcessDataAndQ)
    thread.start()
#time.sleep(1)
cacher()
# time.sleep(30)
poll = st.select_slider("Sample Rate",[i for i in range(1,61)])
zoom_level = st.select_slider("Display Zoomout  ",[i for i in range(1,101,2)]) # Zoom Slider
data,timestamp = askData()
cpu = st.select_slider("CPU",[i for i in range(0,len(data[0])+1)])          # CPU Selection
chart=st.empty()
samples_persec = sliderToPointsAndSleep(poll)[0]
# count=0
try:
     setPoll(poll)
     while(True):
            # try:
        out = askData()
        if(out==None):
            process.stdout.flush()
            continue
        data,timestamp = out
        fig = px.line(data[(samples_persec - int(samples_persec*(zoom_level/100))):,:])
        print(zoom_level)
        chart.plotly_chart(fig,use_container_width=True)

        # except:
        #     process.stdout.flush()
        time.sleep(1)
        # count+=1
        # if(count==10):
        #     setPoll(pollRate+1)
except KeyboardInterrupt:
    run=False
    process.stdin.write(b"data\n")
    process.stdin.flush()
except:
    print("RAN")
    process.kill()
    raise
#time.sleep(1000)

