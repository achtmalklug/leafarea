from PyQt5 import QtWidgets, QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
import matplotlib.dates as mdates
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time,math
from PyQt5.QtCore import QCoreApplication 

# Ensure using PyQt5 backend
matplotlib.use('QT5Agg')
pi=3.1416

class MplCanvas(FigureCanvas):
    def __init__(self, parent = None, width = 12, height = 9):
        self.parent=parent
        self.initialise()

    def hover(self, event):
        vis = self.annot.get_visible()
        self.event=event
        self.annot.set_visible(True)
        if event.inaxes == self.axes:
            cont, ind = self.axes.contains(event)
            pos=np.array([int(event.xdata),int(event.ydata)])

            self.cont=cont
            self.ind=ind

            if self.resultImg[pos[1],pos[0]]>0:
                self.updateAnnot(pos)
                self.annot.set_visible(True)
                self.figure.canvas.draw_idle()
            else:
                self.annot.set_visible(False)
                self.figure.canvas.draw_idle()

    def updateAnnot(self,pos):
        #print("-->update",pos)
        #print(self.image[int(round(pos[0])),int(round(pos[1]))]))
        self.annot.xy = pos
        
        if (pos[0] is None):
            print(pos,"return")
            return
        
        objId=int(self.parent.labelled[pos[1],pos[0]])-1
        text=self.parent.labeltext[objId]
#        if objId==0:
#            if self.parent.refarea==1:
#                area=self.parent.props[0].filled_area 
#            else:
#                area=self.parent.refarea
#                
#            if self.parent.refperim==1:
#                perim=self.parent.props[0].perimeter
#            else:
#                perim=self.parent.refperim
#                    
#            text="reference object\narea: {}{}\nperimeter: {}{}".format(
#                    area,self.parent.areaUnit,
#                    self.parent.props[0].perimeter/self.parent.refperim,self.parent.perimUnit)
#            
#            text="Object {}:\n Area: {}\n Perimeter: {}\n Shape index: {}\n equivalent Diam. {}: ".format(objId,
#                         self.parent.statsStr[objId]["area"],
#                         self.parent.statsStr[objId]["perim"],
#                         self.parent.statsStr[objId]["si"],
#                         self.parent.statsStr[objId]["eqdiam"])
#            #text="ObjId {}".format(objId)
#        else:
#            #print("---->",objId)
#            #print(self.parent.props)
#            #print("eqArea=",pi*(self.parent.props[objId].equivalent_diameter**2)/4)
#            #print("SI=",(self.parent.props[objId].perimeter)/(self.parent.props[objId].equivalent_diameter*pi))
#            #print(self.parent.statsStr[objId],"<----")
#            
#            text="Object {}:\n Area: {}\n Perimeter: {}\n Shape index: {}\n equivalent Diam. {}: ".format(objId,
#                         self.parent.statsStr[objId]["area"],
#                         self.parent.statsStr[objId]["perim"],
#                         self.parent.statsStr[objId]["si"],
#                         self.parent.statsStr[objId]["eqdiam"])
#            text=self.parent.labeltext[objId]

                 #round(pos[0],1),
                 # round(pos[1],1),
                 # self.resultImg[int(round(pos[1])),int(round(pos[0]))]
            
        try:
            self.annot.set_text(text)
        except:
            #print("geht nich")
            #print ("pos:",pos)
            #print ("type:",type(pos))
            pass
        
        #self.annot.get_bbox_patch().set_facecolor(cmap(norm(c[ind["ind"][0]])))
        self.annot.get_bbox_patch().set_alpha(0.4)
        
    def hideAxes(self):
        xax=self.axes.get_xaxis()
        yax=self.axes.get_yaxis()
        xax.set_visible(False)
        yax.set_visible(False)
        
        self.axes.spines["top"].set_visible(False)
        self.axes.spines["right"].set_visible(False)
        self.axes.spines["bottom"].set_visible(False)
        self.axes.spines["left"].set_visible(False)
    
        self.draw()
        
    def showAxes(self):
        xax=self.axes.get_xaxis()
        yax=self.axes.get_yaxis()
        xax.set_visible(True)
        yax.set_visible(True)
        self.draw()
    
    def initialise(self):
        self.fig = Figure(figsize = (12, 9))
        self.axes = self.fig.add_subplot(111)
        self.annot = self.axes.annotate("", xy=(0,0), xytext=(10,10),textcoords="offset points",size=7,bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        
        FigureCanvas.__init__(self, self.fig)

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
    
        return
    
    def reset(self):
        self.fig = Figure(figsize = (12, 9))
        self.axes = self.fig.add_subplot(111)
        
        FigureCanvas.__init__(self, self.fig)

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.draw()

    
    def clear(self):
        print("canvasClear")
        self.fig=Figure()
        self.draw()
        return
        
    def plotImage(self,image):
        #if type(image)=="<class 'int'>int": return
        #print("Size:", image.size)
        self.resultImg=image
        self.axes.imshow(image)
        self.draw()  

#class MplCanvas(FigureCanvas):
    #def __init__(self):
        ##self.initialplot()
        #self.fig = Figure()
        #FigureCanvas.__init__(self, self.fig)
        #FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)
    
    #def initialplot(self):
        #self.fig = Figure()
        #self.ax1 = self.fig.add_subplot(211)
        #self.ax2 = self.fig.add_subplot(212)
        #self.ax3 = self.ax2.twinx()
         
        #self.ax1.set_position([0.05, 0.8, 0.65, 0.17])
        #self.ax2.set_position([0.05, 0.6, 0.65, 0.17])
        #self.ax3.set_position([0.05, 0.61, 0.65, 0.17])
               
        
    #def change(self):
        #print("Change fig")
        #self.initialplot()
        #self.fig.clf()
        #self.fig = Figure()
        
        #self.ax1 = self.fig.add_subplot(211)
        #self.ax2 = self.fig.add_subplot(212)
        #self.ax3 = self.ax2.twinx()
         
        #self.ax1.set_position([0.5, 0.8, 0.65, 0.17])
        #self.ax2.set_position([0.5, 0.6, 0.65, 0.17])
        #self.ax3.set_position([0.05, 0.61, 0.65, 0.17])
                
        #FigureCanvas.__init__(self, self.fig)
        #FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)
        #QCoreApplication.processEvents()

## Matplotlib widget
#class MplWidget(QtWidgets.QWidget):
    #def __init__(self, parent=None):
        #QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        #self.canvas = MplCanvas()                  # Create canvas object
        #self.vbl = QtWidgets.QVBoxLayout()         # Set box for plotting
        #self.vbl.addWidget(self.canvas)
        #self.setLayout(self.vbl)
        
    #def updateCanvas(self):
        #print("updateCanvas")
        #self.canvas.change()
        
        

## Matplotlib canvas class to create figure
#class MplCanvas(FigureCanvas):
    #def __init__(self):

        #self.fig = Figure()
        
        #self.ax1 = self.fig.add_subplot(211)
        #self.ax2 = self.fig.add_subplot(212)
        ##self.ax3 = self.ax2.twinx()
         
        #self.ax1.set_position([0.5, 0.8, 0.65, 0.17])
        #self.ax2.set_position([0.05, 0.6, 0.65, 0.17])
        ##self.ax3.set_position([0.05, 0.61, 0.65, 0.17])
                
        #FigureCanvas.__init__(self, self.fig)
        #FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)
        #self.update_fig()
        
    #def update_fig(self):
        #print("update_fig")
        #self.fig = Figure()
        
        #self.ax1 = self.fig.add_subplot(211)
        #self.ax2 = self.fig.add_subplot(212)
        #self.ax3 = self.ax2.twinx()
         
        #self.ax1.set_position([0.05, 0.8, 0.65, 0.17])
        #self.ax2.set_position([0.05, 0.6, 0.65, 0.17])
        #self.ax3.set_position([0.05, 0.61, 0.65, 0.17])
                
        #FigureCanvas.__init__(self, self.fig)
        #FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #FigureCanvas.updateGeometry(self)
        ##self.fig.canvas.draw()
        ###fig,ax = plt.subplots(ncols=1)
        ###ax.imshow(image)
        ###plt.show(block=False)

## Matplotlib widget
#class MplWidget(QtWidgets.QWidget):
    #def __init__(self, parent=None):
        #print("Mpl Init")
        #QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        #self.canvas = MplCanvas()                  # Create canvas object
        #self.vbl = QtWidgets.QVBoxLayout()         # Set box for plotting
        
        ##self.setLayout(self.vbl)
        ##self.fig=Figure()
        ##self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        ##self.ax = self.canvas.figure.subplots()
        ##t = np.linspace(0, 10, 501)
        ##self.ax.plot(t, np.sin(t ))
        ##self.ax.figure.canvas.draw()
        #dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        #self.vbl.addWidget(dynamic_canvas)
        #self._dynamic_ax = dynamic_canvas.figure.subplots()
        #self._timer = dynamic_canvas.new_timer(
            #100, [(self._update_canvas, (), {})])
        #self._timer.start()

    #def _update_canvas(self):
        #self._dynamic_ax.clear()
        #t = np.linspace(0, 10, 101)
        ## Shift the sinusoid as a function of time.
        #self._dynamic_ax.plot(t, np.sin(t + time.time()))
        #self._dynamic_ax.figure.canvas.draw()
        
    #def update_fig(self, image):
        
        #return
