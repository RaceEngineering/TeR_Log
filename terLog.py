#!/usr/bin/env python3

import re 
import cantools
import numpy as np
import copy
from scipy.interpolate import interp1d
from scipy.integrate import cumulative_simpson as cumtrapz
import matplotlib.pyplot as plt



# Log message regex with Groupnames
FRAMERGX = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})#(?P<data>[0-9A-F]{2,16})'
frameRegex = re.compile(FRAMERGX) 


# Signal data type
sigType = [('timestamps', 'float'), ('values', 'float')]


class canSignal():

    def __init__(self,name : str,):
        self.name = name
        self.data = None

        #Overload tricks

    def plot(self,multiPlot = False):
        if multiPlot: # Multiplot add our data
            plt.plot(self.data["timestamps"], self.data["values"], linestyle='-',label=self.name)
        else: # Own plot just
            fig = plt.figure(figsize=(10, 5))
            plt.plot(self.data["timestamps"], self.data["values"], linestyle='-', color='b',label=self.name)
            plt.title(self.name)
            plt.xlabel('Time (s)')
            plt.ylabel('Value')
            plt.legend()
            plt.show()

    def integrate(self):
        iSig = canSignal(f"Integral of {self.name}")
        iSig.data = np.array(cumtrapz(self.data["values"]),self.data["timestamps"],dtype = sigType)
        return iSig

    # Sobrecargas
    def __add__(self,sig):
        if isinstance(sig,canSignal):
            sumSig = canSignal(f"{self.name} + {sig.name}")
            #Get Minimum and maximun timestamps of signals and generate new time base for signal
            cTimestamp =  np.linspace(min(self.data["timestamps"].min(), sig.data["timestamps"].min()), 
                                    max(self.data["timestamps"].max(), sig.data["timestamps"].max()), 
                                    num=100)
            # Interpolamos 
            inter1 = interp1d(self.data["timestamps"], self.data["values"], bounds_error=False, fill_value="extrapolate")
            inter2 = interp1d(sig.data["timestamps"], sig.data["values"], bounds_error=False, fill_value="extrapolate")
            # Realizamos la suma
            sValues = inter1(cTimestamp) + inter2(cTimestamp)
            # Metemos al array
            sumSig.data = np.array(list(zip(cTimestamp, sValues)), dtype=sigType)
            return sumSig
        else:
            sumSig = copy.copy(self)
            sumSig.data["values"]+= sig
            return sumSig

    def __sub__(self,sig):
        if isinstance(sig,canSignal):
            subSig = canSignal(f"{self.name} - {sig.name}")
            #Get Minimum and maximun timestamps of signals and generate new time base for signal
            cTimestamp =  np.linspace(min(self.data["timestamps"].min(), sig.data["timestamps"].min()), 
                                    max(self.data["timestamps"].max(), sig.data["timestamps"].max()), 
                                    num=100)
            # Interpolamos 
            inter1 = interp1d(self.data["timestamps"], self.data["values"], bounds_error=False, fill_value="extrapolate")
            inter2 = interp1d(sig.data["timestamps"], sig.data["values"], bounds_error=False, fill_value="extrapolate")
            # Realizamos la suma
            sValues = inter1(cTimestamp) - inter2(cTimestamp)
            # Metemos al array
            subSig.data = np.array(list(zip(cTimestamp, sValues)), dtype=sigType)
            return subSig
        else:
            subSig = copy.copy(self)
            subSig.data["values"]-= sig
            return subSig

    def __mul__(self,sig):
        if isinstance(sig,canSignal):
            mulSig = canSignal(f"{self.name} * {sig.name}")
            #Get Minimum and maximun timestamps of signals and generate new time base for signal
            cTimestamp =  np.linspace(min(self.data["timestamps"].min(), sig.data["timestamps"].min()), 
                                    max(self.data["timestamps"].max(), sig.data["timestamps"].max()), 
                                    num=100)
            # Interpolamos en el eje común y operamos
            inter1 = interp1d(self.data["timestamps"], self.data["values"], bounds_error=False, fill_value="extrapolate")
            inter2 = interp1d(sig.data["timestamps"], sig.data["values"], bounds_error=False, fill_value="extrapolate")
            # Realizamos la multiplicacion
            mValues = inter1(cTimestamp) * inter2(cTimestamp)

            # Metemos al array
            mulSig.data = np.array(list(zip(cTimestamp, mValues)), dtype=sigType)
            return mulSig
        else:
            mulSig = copy.copy(self)
            mulSig.data["values"]*= sig
            return mulSig

        

    def __repr__(self):
        return self.name    


class canLog():

    def __init__(self,dbcPath : str,logPath : str):
        self.dbc = cantools.db.load_file(dbcPath)
        logFile = open(logPath,'r') # Abrimos archivo

        #Almacen de frames
        log = logFile.read()#Leemos el log
        logFile.close() # Cerramos el archivo
        self.frames = list(frameRegex.finditer(log))
        #Almacen mensajes
        self.signals = self.getSignals() # Contiene todos los mensajes encontrados en el log


    def getSignals(self):
        signals = []
        for dbMsg in self.dbc.messages:# For each message we create a message object containing its respective matches
            dcFrames = [(float(msgFrame["timestamp"]),dbMsg.decode(bytes.fromhex(msgFrame["data"]),decode_choices=False)) for msgFrame in self.frames if int(msgFrame['id'], 16) == dbMsg.frame_id] #Decoded frame dicts
            if not dcFrames: # Skip non existent messages
                continue
            for dbSig in dbMsg.signals: # Por cada señal de cada mensaje
                sig = canSignal(name = dbSig.name)
                # Populate the function, numpy data
                try:
                    sig.data = np.array([(f[0],float(f[1][dbSig.name])) for f in dcFrames], dtype=sigType) # Extract signal value from frame in dictionary and convert it to signal element
                except:
                    pass
                signals.append(sig)
        return signals


    def getSignal(self, sigName : str):
        for sig in self.signals:
            if sig.name == sigName:
                return sig
        return None

    def plot(self,sigList):
        plt.figure(figsize=(10, 6))
        #Append each signal
        for pSig in sigList:
            for sig in self.signals:
                if sig.name == pSig:
                    sig.plot(multiPlot=True)

        plt.title(sigList)
        plt.xlabel('Time (s)')
        plt.ylabel('Value')
        plt.legend()
        plt.grid()
        plt.tight_layout()           
        plt.show()

if __name__ == '__main__': 
    log = canLog("TER.dbc","RUN2.log")
    apps = log.getSignal("APPS_1")
    bpps = log.getSignal("APPS_2")

    suma = apps * 2
    suma.plot()
    log.plot(["rrRPM","rlRPM","APPS_AV","ANGLE"])