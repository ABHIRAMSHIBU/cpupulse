#!/usr/bin/env python
import streamlit as st
import os, time
import sys
from datetime import datetime
from pprint import pprint
import pandas as pd
from collections import deque
from time import sleep
import plotly.express as px
import numpy as np
from matplotlib import pyplot as plt
import matplotlib

# PLTBACKEND="MATPLOTLIB"
PLTBACKEND="PLOTLY"
# PLTBACKEND="INTERNAL"
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


matplotlib.use('agg')
cpudata_og = parseCPUINFO()
st.set_page_config(page_title="CPU Pulse", page_icon=None, layout='wide', initial_sidebar_state='collapsed')
past_data,sleepTime = sliderToPointsAndSleep(st.select_slider("Sample Rate",[i for i in range(1,61)]))
zoom_level = st.select_slider("Display Zoomout  ",[i for i in range(1,101,2)])
cpu = st.select_slider("CPU",[i for i in range(0,len(cpudata_og)+1)])
qdata = deque([[0 for i in range(len(cpudata_og)+1)] for j in range(past_data)],maxlen=past_data)
chart = st.empty()
f=open("/tmp/cpupulsed.log","w")
while(True):
    # CPU DATA
    timenow = datetime.now()
    timestamp=datetime.now()
    cpudata = parseCPUINFO()
    timestamp_1 = datetime.now()-timestamp
    timestamp_1/=2
    timestamp=timestamp+timestamp_1
    tcd = datetime.now() - timenow

    # DATA Processing
    mhz_dict = {"time":timestamp.__str__()[10:],0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
    for i in cpudata:
        mhz_dict[int(i['processor'])] = float(i["cpu MHz"])
    mhz_lst = list(mhz_dict.values())
    qdata.append(mhz_lst)
    # mhz_df = pd.DataFrame(qdata[:][1:],[i for i in range(len(mhz_dict)-1)])
    # mhz_df = mhz_df.iloc[past_data - int(past_data*(zoom_level/100)):past_data]
    # mhz_df.index=[i for i in range(len(mhz_df))][::-1]
    # fig = px.line(mhz_df)
    # fig.layout = dict(title=f"CPU MHz", xaxis = dict(title="Time"), yaxis = dict(title="MHz"))
    # fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightYellow')
    # fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightYellow')  
    # fig.update_layout(width=1700,height=700)
    # chart.plotly_chart(fig,use_container_width=True)
    # chart.line_chart(mhz_df)
    qdata_np = np.array(qdata)
    qdata_np = qdata_np[(past_data - int(past_data*(zoom_level/100))):,:]
    if(cpu>0):
        qdata_np = qdata_np[cpu]
    tpd = datetime.now() - tcd - timenow

    # Plotting
    # MatplotLIB
    if(PLTBACKEND=="MATPLOTLIB"):
        fig = plt.figure(figsize=[10,3])
        for i in range(len(qdata[0])-1):
            plt.plot([j for j in range(len(qdata_np))],np.asarray(qdata_np[:,i+1], dtype=np.float64),label = str(i))
        plt.legend()
    # Plotly
    elif(PLTBACKEND=="PLOTLY"):
        y = np.asarray(qdata_np[:,1:], dtype=np.float64)
        fig = px.line(y)
    # Internal
    elif(PLTBACKEND=="INTERNAL"):
        y = np.asarray(qdata_np[:,1:], dtype=np.float64)
        # x = np.array([i for i in range(len(qdata_np))]).reshape(-1,1)
        # print(y.shape)
        # y=np.hstack((x,y))
        
    
    # Update UI
    tpl = datetime.now() - tpd - tcd - timenow  
    # MatplotLIB
    if(PLTBACKEND=="MATPLOTLIB"):
        chart.pyplot(fig)
        plt.close(fig)
    # Plotly
    elif(PLTBACKEND=="PLOTLY"):
        chart.plotly_chart(fig,use_container_width=True)
    elif(PLTBACKEND=="INTERNAL"):
        chart.line_chart(y)
    tst = datetime.now() - tpd - tcd - tpl - timenow

    # Logging
    tl = datetime.now() - timenow
    f.write("----------------------------------\n")
    f.write(f"tl ={tl}\n")
    f.write(f"tcd={tcd}\n")
    f.write(f"tpd={tpd}\n")
    f.write(f"tpl={tpl}\n")
    f.write(f"tst={tst}\n")
    f.write(f"tps={tpl+tst}\n") 
    f.flush()

    # Sample lock
    try:
        timeelapsed = datetime.now() - timenow
        seconds = timeelapsed.seconds + timeelapsed.microseconds/10**6
        if((sleepTime-seconds)>0):
            f.write(f"ts ={sleepTime-seconds}\n")
            f.flush()
            sleep(sleepTime-seconds)
        else:
            f.write("ERROR:Time Passed!\n")
            f.flush()
    except KeyboardInterrupt:
        print("Bye")
        exit(0)

# timenow = datetime.now()
# for i in range(10000):
#     parseCPUINFO()
# timeelapsed = datetime.now() - timenow
# print((timeelapsed.seconds+timeelapsed.microseconds/10**6)/10**4)
# print(parseCPUINFO)#,selen(parseCPUINFO()))