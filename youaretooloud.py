import pyaudio
import time
import pylab
import numpy as np
import pyttsx3
import math
import os
pid = 1

class SWHear(object):
    """
    The SWHear class is made to provide access to continuously recorded
    (and mathematically processed) microphone data.
    """

    def __init__(self,device=None,startStreaming=True):
        """fire up the SWHear class."""
        print(" -- initializing SWHear")

        self.chunk = 4096 # number of data points to read at a time
        self.rate = 44100 # time resolution of the recording device (Hz)

        # for tape recording (continuous "tape" of recent audio)
        self.tapeLength=2 #seconds
        self.tape=np.empty(self.rate*self.tapeLength)*np.nan

        self.p=pyaudio.PyAudio() # start the PyAudio class
        if startStreaming:
            self.stream_start()

    ### LOWEST LEVEL AUDIO ACCESS
    # pure access to microphone and stream operations
    # keep math, plotting, FFT, etc out of here.

    def stream_read(self):
        """return values for a single chunk"""
        data = np.fromstring(self.stream.read(self.chunk),dtype=np.int16)
        #print(data)
        return data

    def stream_start(self):
        """connect to the audio device and start a stream"""
        print(" -- stream started")
        self.stream=self.p.open(format=pyaudio.paInt16,channels=1,
                                rate=self.rate,input=True,
                                frames_per_buffer=self.chunk)

    def stream_stop(self):
        """close the stream but keep the PyAudio instance alive."""
        if 'stream' in locals():
            self.stream.stop_stream()
            self.stream.close()
        print(" -- stream CLOSED")

    def close(self):
        """gently detach from things."""
        self.stream_stop()
        self.p.terminate()

    ### TAPE METHODS
    # tape is like a circular magnetic ribbon of tape that's continously
    # recorded and recorded over in a loop. self.tape contains this data.
    # the newest data is always at the end. Don't modify data on the type,
    # but rather do math on it (like FFT) as you read from it.

    def tape_add(self):
        """add a single chunk to the tape."""
        self.tape[:-self.chunk]=self.tape[self.chunk:]
        self.tape[-self.chunk:]=self.stream_read()

    def tape_flush(self):
        """completely fill tape with new data."""
        readsInTape=int(self.rate*self.tapeLength/self.chunk)
        print(" -- flushing %d s tape with %dx%.2f ms reads"%\
                  (self.tapeLength,readsInTape,self.chunk/self.rate))
        for i in range(readsInTape):
            self.tape_add()

    def tape_forever(self,plotSec=.25):
        t1=0
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate',125)
            engine.setProperty('voice','HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
            while True:
                self.tape_add()
                if (time.time()-t1)>plotSec:
                    t1=time.time()
                    if pid:
                        self.tape_plot()
                    else:
                        volume = 20*math.log10(max(np.absolute(self.tape)))
                        print(volume)
                        if volume > 80:
                            engine.say('Please be quiet')
                            engine.runAndWait()
                            time.sleep(5)
                            self.tape=np.empty(self.rate*self.tapeLength)*np.nan
        except:
            print(" ~~ exception (keyboard?)")
            return

    def tape_plot(self,saveAs="03.png"):
        """dB real time plot."""
        plotColor = 'green'
        volume = 20*math.log10(max(np.absolute(self.tape)))
        if volume > 82.5:
            plotColor = 'red'

        pylab.plot(np.arange(len(self.tape))/self.rate,self.tape,color = plotColor)
        pylab.axis([0,self.tapeLength,-2**16/2,2**16/2])
        if saveAs:
            t1=time.time()
            pylab.savefig(saveAs,dpi=50)
            #print("plotting saving took %.02f ms"%((time.time()-t1)*1000))
        else:
            pylab.show()
            print() #good for IPython
        pylab.close('all')

if __name__=="__main__":
    pid = os.fork()
    if pid == 0:
        print("talking process starting\n")
    else:
        print("waveform process starting\n")
    ear=SWHear()
    ear.tape_forever()
    ear.close()
    if pid == 0:
        print("talking process is done")
    else:
        print("waveform process is done")
        os.waitpid(pid,0)
