from pprint import pprint
import time
import numpy as np
from threading import Thread
import streamlit as st
import plotly.express as px
import socket
from datetime import datetime
import pandas as pd
import base64
import streamlit.components.v1 as components

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

def askData(host,port):
    timenow = datetime.now()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.05) # Hope optimal time
        s.connect((host, port))
        s.send((f"data\n").encode())
        data=b""
        while True:
            try:
                data += s.recv(1024)
            except socket.timeout:
                break
            if(data==""):
                break
        data = data.decode()

        # previndex=0
        # timestamp=[]
        # datal=[]
        # while(True):
        #     index = data.find("\n",previndex)
        #     if(index==-1):
        #         break
        #     udata = data[previndex:index]
        #     previndex = index+1
        #     val = [ j.strip() for j in udata.split(",") ]
        #     timestamp.append(val[0])
        #     datal.append(val[1:])

        data = data.strip().split("\n")
        timestamp=[]
        datal=[]
        for i in data:
            val = [ j.strip() for j in i.split(",") ]
            timestamp.append(val[0])
            datal.append(val[1:])

        timeelapsed = datetime.now() - timenow
        #pprint(data)
        # pprint(timeelapsed)
        # pprint(len(data))
        s.close()
        return (np.asarray(datal,dtype=np.float64),np.asarray(timestamp,dtype=np.float64))

def setPoll(polling,host,port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.01) # Hope optimal time
        s.connect((host, port))
        s.send((f"pol={polling}\n").encode())
        s.close()

def ts_to_time(ts):
    if(ts==0):
        return np.nan
    return str(datetime.fromtimestamp(float(ts)))

# def cacher():
#     global process
#     global thread
#     thread = Thread(target=readProcessDataAndQ)
#     thread.start()
# #time.sleep(1)
# cacher()
# # time.sleep(30)
poll = st.select_slider("Sample Rate",[i for i in range(1,61)])
zoom_level = (st.select_slider("Display Zoomout  ",[i for i in range(1,1001,2)])/1000) # Zoom Slider
data,timestamp = askData("localhost",9999)
cpu = st.select_slider("CPU",[i for i in range(0,len(data[0])+1)])          # CPU Selection
col1, col2 = st.columns(2)
with col1:
    plot_bool = st.checkbox("Enable Plot",value=True)

with col2:
    save_btn = st.button("Save")

chart=st.empty()
chart_1=st.empty()
samples_persec = sliderToPointsAndSleep(poll)[0]
kill_count = 0
try:
    setPoll(poll,"localhost",9999)
    while(True):
        out = askData("localhost",9999)
        data,timestamp = out
        if data.shape[0]!=samples_persec:
            kill_count+=1
            print("Something went wrong with SOCKetS!")
            print(data.shape)
            if kill_count<=10:
                continue
        kill_count=0
        if(save_btn):
            save_df = pd.DataFrame(data,index=[ ts_to_time(i) for i in timestamp ])
            save_df["unixtime"] = timestamp
            save_df.to_csv("save_data.csv")
            csv = save_df.to_csv()
            b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
            href = f'<a download=data.csv href="data:file/csv;base64,{b64}">Download csv file</a>'
            components.html(href)

        if(not plot_bool):
            break
        #print(timestamp[(samples_persec - int(samples_persec*(zoom_level/100))):])
        y=data[(samples_persec - int(samples_persec*(zoom_level))):,:]
        x=([ ts_to_time(i) for i in timestamp[(samples_persec - int(samples_persec*(zoom_level))):]])
        y_1=pd.DataFrame(y,index=x)
        y=pd.DataFrame(y,index=range(len(x))[::-1])
        fig = px.line(y_1)
        fig_1 = px.line(y)
        print(poll)
        chart.plotly_chart(fig,use_container_width=True)
        chart_1.plotly_chart(fig_1,use_container_width=True)
        time.sleep(0.5)
except KeyboardInterrupt:
    run=False