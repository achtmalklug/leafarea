import sys, os, glob, re

from PyQt5 import QtGui, uic, QtCore, QtWidgets
from PyQt5.QtCore import QDir,QDirIterator,QRectF,Qt,QCoreApplication

from PyQt5.QtWidgets import QFileSystemModel, QGraphicsScene 
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageQt
from PyQt5.QtGui import QIcon, QPixmap
from mplwidget import MplCanvas
import mplcursors,pywt,pywt._extensions._cwt

from scipy import ndimage
from skimage import data, img_as_float, io,restoration,morphology,color,transform,exposure,feature,filters,measure
from imageio import imread
from skimage.morphology import disk
from skimage.filters import rank
import math
import pandas as pd

pi=3.1416

def debugMsg(text):
    #sys.stderr.write("\n"+text)
    return

class parametersDlg(QtWidgets.QDialog):
    def __init__(self,parent):
        super(parametersDlg, self).__init__()
        uic.loadUi('optionsDialog.ui', self)
        self.parent=parent
        self.setModal(True)
        for k in self.parent.settings.keys():
            try:
                getattr(self,k).setValue(int(self.parent.settings[k]))
            except:
                pass
        self.show()

    def cancel(self):
        self.destroy()
        
    def ok(self):
        configfile = QtCore.QSettings("configfile.txt", QtCore.QSettings.IniFormat)
        debugMsg(self.parent)
        for k in self.parent.settings.keys():
            try:
                debugMsg("trying to write %{k}")
                configfile.setValue(k, getattr(self,k).value())
                debugMsg("success")
                debugMsg("trying to set it in app")
                self.parent.settings[k]=getattr(self,k).value()
                debugMsg("more success")
            except:
                debugMsg("fail")
        self.close()
        self.parent.selectImage()

class aboutDlg(QtWidgets.QDialog):
    def __init__(self):
        super(aboutDlg, self).__init__()
        self.setModal(True)
        uic.loadUi('aboutDialog.ui', self)
        self.show()
    def exit(self):
        self.close()
        #self.destroy()
        

class MyWindow(QtWidgets.QMainWindow):
    
    def readSettings(self):
        settings = QtCore.QSettings("configfile.txt", QtCore.QSettings.IniFormat)
        self.settings={}
        for k in settings.allKeys():
            self.settings[k]=settings.value(k)
        
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('mainWindow.ui', self)
        self.currentFolder=os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QtGui.QIcon('icon.png'))

        self.readSettings()
        self.showRecursive=False
        self.populateTreeView()
        self.mplcanvas=MplCanvas(self)
        self.currentFile=None
        self.rawPhotoView=MplCanvas(self)
        self.rawPhotoView.hideAxes()
        self.setWindowTitle("Leafarea")
        self.props=None
        
        areacombolabel=QtWidgets.QLabel("Reference area in mm²/Reference perimeter in mm")
        self.Areacombo = QtWidgets.QComboBox(self)
        self.Areacombo.addItem("62370mm²/1014mm (ISO A4)",1)
        self.Areacombo.addItem("124740mm²/1434mm (ISO A3)",2)
        self.Areacombo.addItem("not specified",3)
        
        self.Areacombo.currentIndexChanged.connect(self.setRefarea) 
        self.Areacombo.currentTextChanged.connect(self.setRefarea) 
        self.Areacombo.setEditable(True)
        self.setRefarea()
        
        self.splitter.addWidget(self.rawPhotoView)
        self.splitter.addWidget(self.mplcanvas)
        self.splitter.addWidget(areacombolabel)
        self.splitter.addWidget(self.Areacombo)
        #self.statusbar=QtWidgets.QStatusBar()
        self.initialPlot()
                
        settings = QtCore.QSettings('configfile.txt', QtCore.QSettings.IniFormat)
        
        self.actionExit.triggered.connect(self.exitPrg)
        self.actionParameters.triggered.connect(self.showParameterDlg)
        self.actionAbout.triggered.connect(self.showAboutDlg)
        
        #other = QtCore.QSettings("configfile.txt", QtCore.QSettings.IniFormat)
        #for k, v in settings.iteritems():
        #    other.setValue(k, v)
        self.summary=QtWidgets.QLabel("")
        self.summary.setText("blubb")
        self.summary.setVisible(False)
        self.splitter.addWidget(self.summary)
		
        self.setRefarea()
        self.show()

    def generateAnnot(self):
        statsStr=[]
        stats=[]
        self.labeltext=[]
        props=self.props
        
        if isinstance(props,int):
            self.labeltext=[""]
            return
        
        for i in range(len(props)):
            refarea=self.refarea_px
            refperim=self.refperim_px #props[0].perimeter
            
            #print("--------------- refperim",refperim)
            #print("--------------- refperim",refperim)
            #print(props[i].perimeter)
            
            si=round(props[i].perimeter/(props[i].equivalent_diameter*pi),3)
            eqdiam_px=round(props[i].equivalent_diameter)
            #eqdiam_rel=round(props[i].perimeter/props[i].equivalent_diameter)
            
            perim_px=round(props[i].perimeter)
            perim_rel=round(props[i].perimeter/refperim,2)
            
            area_px=round(props[i].area,3)
            area_rel=round(props[i].area/refarea,3)
            
            #perim_px=round(props[i].perimeter)
            #perim_rel=round(props[i].perimeter)
            
            #eqr=math.sqrt(props[0].area/pi)
            si_str="{}".format(si)
            eqdiam_str="{}{}".format(eqdiam_px, self.perimUnit)
            perim_str="{}{} ({})".format(perim_px,self.perimUnit,perim_rel)
            area_str="{}{} ({})".format(area_px,self.areaUnit,area_rel)
            
            stats.append({"i":i,
                          "area_rel":area_rel,
                          "area_px":area_px,
                          "perim_px":perim_px,
                          "perim_rel":perim_rel,
                          "si":si,
                          "eqdiam_px":eqdiam_px})
            statsStr.append({"area":area_str,"perim":perim_str,"si":si_str,"eqdiam":eqdiam_str})
            
            areaUnit="px" if self.refarea==1 else self.areaUnit
            perimUnit="px" if self.refperim==1 else self.perimUnit
            
            #print("i ",i," refarea ",refarea," areaUnit ",areaUnit," area_rel ",area_rel," refperim ",refperim," perim_rel ",perim_rel," perimUnit ",perimUnit)
            
            if i==0:
                self.labeltext.append("reference area\nArea: {}{} ({})\nperimeter: {}{} ({})".format(
                        round(self.refarea_px,0) if self.areaUnit=="px" else round(self.refarea),areaUnit,1,
                        round(self.refperim_px,0) if self.perimUnit=="px" else round(self.refperim),perimUnit,1))
            else:
                #print("self.refarea>>:",self.refarea)
                #print("self.refperim>>:",self.refperim)
                #print("refarea>>:",refarea)
                #print("refperim>>:",refperim)
                #
                self.labeltext.append("Object {}\n Area: {}{} ({})\nPerimeter: {}{} ({})\nShape index: {}".format(
                        i,
                        str(round(area_px/(1 if self.areaUnit=="px" else refarea)*self.refarea)),self.areaUnit, round(area_px/refarea,4),
                        str(round(perim_px/(1 if self.perimUnit=="px" else refperim)*self.refperim)),self.perimUnit, round(perim_px/refperim,4),
                        si))
        
    def setRefarea(self):
        debugMsg("refarea")
        debugMsg(str(self.Areacombo.currentData()))
        debugMsg(str(self.Areacombo.currentText()))
        debugMsg(str(self.Areacombo.currentIndex()))
        debugMsg(str(re.sub('(\d*\.?\d+).*','\\1',self.Areacombo.currentText())))
        

        substrs=self.Areacombo.currentText().split("/")[0:2]
        p=re.compile("(\d*\.?\d+)(.*?)[\(|/]")
        
        if len(substrs)<2:
            perimStr=""
        else:
            perimStr=substrs[1]
        
        perimSearch=p.search(perimStr+"/")
        if perimSearch is None:
            self.refperim=1
            self.perimUnit="px"
        else:
            self.refperim=float(perimSearch.group(1))
            self.perimUnit=perimSearch.group(2)

        areaSearch=p.search(substrs[0]+"/")
        if areaSearch is None:
            self.refarea=1
            self.areaUnit="px"
        else:
            self.refarea=float(areaSearch.group(1))
            self.areaUnit=areaSearch.group(2)
        
        #print("ref: ",self.refarea," ",self.refperim," ",self.perimUnit," ",self.areaUnit)
        if self.props is not None:
            self.generateAnnot()
            self.generateSummary()
			
        return
    
    def exitPrg(self):
        sys.exit()
    
    def showParameterDlg(self):
        debugMsg("showParDlg")
        dialog=parametersDlg(self)
        dialog.exec_()
        dialog.show()

    
    def showAboutDlg(self):
        debugMsg("show About")
        dialog=aboutDlg()
        dialog.exec_()
        dialog.show()
        dialog.show()

        
    def initialPlot(self):
        debugMsg("initialPlot")
        self.image=imread("blank.jpg",as_gray=False)
        self.mplcanvas.plotImage(self.image)
        self.mplcanvas.hideAxes()
        
        #self.cursor=self.mplcanvas.figure.canvas.mpl_connect("motion_notify_event", self.mplcanvas.hover)
        
        QCoreApplication.processEvents()
        return
    
    def blankMpl(self):
        debugMsg("blankMpl")
        self.cursor=self.mplcanvas.figure.canvas.mpl_disconnect("motion_notify_event")
        self.image=imread("blank.jpg",as_gray=False)
        self.mplcanvas.annot.set_visible(False)
        self.mplcanvas.plotImage(self.image)
        self.mplcanvas.hideAxes()
        
    def updateFig(self,img):
        debugMsg("UpdateFig")
        self.mplcanvas.plotImage(img)
        
        self.mplcanvas.hideAxes()
        self.mplcanvas.draw()
                
        QCoreApplication.processEvents()
        return
    
    def populateTreeView(self):
        self.filesystemmodel = QtWidgets.QFileSystemModel(self)

        self.filesystemmodel.setRootPath("")
        self.filesystemmodel.setNameFilters(["*.jpg"])
        self.filesystemmodel.setNameFilterDisables(False)
        self.treeView.setModel(self.filesystemmodel)
        
        self.treeView.setRootIndex(self.filesystemmodel.index(""))
        path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"examples")
        #print("PATH=",path)
        path=self.filesystemmodel.index(path)
        self.treeView.setCurrentIndex(path)
        self.treeView.scrollTo(path)
		#self.treeView.scrollTo(self.filesystemmodel.index("/home/marian/programming/leafarea/examples"))
        
        self.treeView.hideColumn(1)
        self.treeView.hideColumn(2)
        self.treeView.hideColumn(3)
        
        self.treeView.setWindowTitle("Dir View")
        self.selectFolder()

        #self.treeView.setCurrentIndex(QtWidgets.QFileSystemModel.index())
        return
    
    def selectFolder(self,folder=None):
        debugMsg("SelectFolder")
        if folder is None:
            folder =self.treeView.currentIndex()
        self.listWidget.clear()

        self.currentFolder=self.filesystemmodel.filePath(self.treeView.currentIndex())
        print("current folder: ",self.currentFolder)
		
        if (self.showRecursive):
            flag=QDirIterator.Subdirectories
        else:
            flag=QDirIterator.NoIteratorFlags
        
        file_it = QDirIterator(self.currentFolder,["*.jpg","*.jpeg","*.tiff","*.png","*.JPG","*.JPEG",".PNG","*.TIFF"],QDir.Files, flag)
        self._current_files = []
        while file_it.hasNext():
            filename=file_it.next()
            #print ("filename: ",filename)
            #print ("  - replacing", self.currentFolder+os.path.sep)
            item=filename.replace(self.currentFolder,".")
            #print ("  -->item: ",item)
            self._current_files.append(item)
            self.listWidget.addItem(item)
        self.listWidget.clear()
        self._current_files.sort()
        self.listWidget.addItems(self._current_files)

        return
    
    def toggleRecursive(self):
        debugMsg("toggleRecursive")
        self.showRecursive=not self.showRecursive
        self.selectFolder()
        return
		
    def generateSummary(self):
        means=self.statsdf.mean()
        sums=self.statsdf.sum()
        refarea=self.refarea_px
        refperim=self.refperim_px #props[0].perimeter
			
        summarytext=""
        summarytext="Reference area: {}{}\nObjects found: {}\n Mean area: {}{} mean SI: {} Mean perimeter: {}{} \nTotal area: {}{} Total perimeter: {}{}".format(
                self.refarea_px if self.areaUnit=="px" else self.refarea,self.areaUnit,
                len(self.statsdf),
                round(means["area_px"]/(1 if self.areaUnit=="px" else refarea)*self.refarea),self.areaUnit,
                round(means["si"],3),
                round(means["perim_px"]/(1 if self.perimUnit=="px" else refperim)*self.refperim),self.perimUnit,
                round(sums["area_px"]/(1 if self.areaUnit=="px" else refarea)*self.refarea),self.areaUnit,
                round(sums["perim_px"]/(1 if self.perimUnit=="px" else refperim)*self.refperim),self.perimUnit)

        self.summary.setText(summarytext)
        self.summary.setVisible(True)

    def selectImage(self):
        debugMsg("selectImage")

        self.summary.setVisible(False)
        self.blankMpl()
        
        imgpath=os.path.join(self.filesystemmodel.filePath(self.treeView.currentIndex()),self.listWidget.currentItem().text())
        self.currentFile=imgpath
        debugMsg("PATH=%{imgpath}")
        
        self.rawPhotoView.plotImage(imread(imgpath,as_gray=False))
        self.rawPhotoView.hideAxes()
        QCoreApplication.processEvents()        
                
        if (not os. path. isfile(imgpath)):
            debugMsg ("bad file")
            return
        
        #show original photo
        #img=Image.open(imgpath)

        #analyse image
        self.statusBar().showMessage('Analysing {}...'.format(imgpath) )
        self.leafarea,self.debugimage,self.labelled,self.props,self.statsStr,self.statsdf,self.refarea_px,self.refperim_px,self.labeltext=self.analyseImage(imgpath)
        
        
        if isinstance(self.props,int):
            return
        self.generateAnnot()
        self.updateFig(self.debugimage)
        self.generateSummary()
                
        self.statusBar().showMessage(imgpath)
        self.updateFig(self.debugimage)
        self.setRefarea()

        self.cursor=self.mplcanvas.figure.canvas.mpl_connect("motion_notify_event", self.mplcanvas.hover)
        QCoreApplication.processEvents()
        return
    
    #def drawLabels(self,img,coords,labels):
        #im=Image.fromarray((exposure.equalize_hist(img)*250).astype(np.int8),mode="L").convert('RGBA')
        #fnt = ImageFont.truetype('Gentium-I.ttf', 40)
        #d = ImageDraw.Draw(im)
        #for i in range(len(coords)):
        #    d.text(coords[i][::-1], str(labels[i]), font=fnt, fill=(0,0,0,255))
        #    return (np.array(im))
        
    def analyseAll(self):
        debugMsg("Analyse all")
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            debugMsg("filename: %{fileName}")
            outdf=[]
            for f in self._current_files:
                debugMsg("analysing {}".format(f))
                leafarea,debugimage,labelled,props,statsStr,df=self.analyseImage(os.path.join(self.currentFolder,f))
                outdf.append(df)
                self.statusBar().showMessage('Analysing {} ({}/{})'.format(f,len(outdf),len(self._current_files)))
            debugMsg("writing to {}".format(fileName))
            outdf=pd.concat(outdf)
            outdf.to_csv(fileName, header=True, index=False, sep='\t', mode='a')
        else:
            debugMsg("no filename provided")
        QtWidgets.QMessageBox.information(self, "Info","Analysis complete. Results written to {}".format(fileName))
        if self.currentFile is None:
            self.statusBar().showMessage("")
        else:
           self.statusBar().showMessage(self.currentFile)
        return
        

    def analyseImage (self,imgpath):
        image=imread(imgpath,as_gray=False)
        if len(image.shape)!=3 : 
            debugMsg("skipping greyscale image %s" % imgpath)
            return (0,0,0,0,0,0,0,0,0)
            
        scale=image.shape[1]/int(self.settings["resizeImg"])
        
        #add passepartout (for the case when the whole image is the reference area (scans))

        if scale > 1:
            image=transform.pyramid_reduce(image, downscale=scale, sigma=None, order=1, mode='reflect',multichannel=True)
            
        canvassize=list(image.shape)
        originalsize=list(image.shape)
        
        canvassize[0]=canvassize[0]+50
        canvassize[1]=canvassize[1]+50
        canvas=np.zeros(canvassize)
        canvas[25:(image.shape[0]+25),25:(image.shape[1]+25),:]=image
        
        image=canvas
        
        edges_r = feature.canny(image[:,:,0])
        edges_g = feature.canny(image[:,:,1])
        edges_b = feature.canny(image[:,:,2])
        edges=edges_r|edges_g|edges_b
    
        ref=morphology.remove_small_objects(ndimage.morphology.binary_fill_holes(edges),min_size=int(self.settings["minRefSize"]))
        refarea=ref.sum()
        if refarea==0:
            return (0,0,0,0,0,0,0,0,0)
        refarea=measure.regionprops(measure.label(ref))[0].area
        refperim=measure.regionprops(measure.label(ref))[0].perimeter
    
        f=morphology.binary_dilation(np.invert(ref),disk(1)).astype(bool)
        edges=morphology.binary_closing(edges,disk(1)).astype(bool)
        e=(edges*np.invert(f))
        
        leaves=morphology.remove_small_objects(ndimage.morphology.binary_fill_holes(e),min_size=int(self.settings["minObjSize"])    )
        leavespixels=leaves.sum()
    
        leafarea=leavespixels/float(refarea)
        debugimage=(ref*1.0)+(leaves*1.0)
    
        leafarea=leavespixels/float(refarea)
        debugimage=(ref*1.0)+(leaves*1.0)
        
        labelled=measure.label(debugimage)
        props=measure.regionprops(labelled)

        #per object stats as strings
        
        
        statsStr=[]
        stats=[]
        labeltext=[]
#        for i in range(len(props)):
#            si=round(props[i].perimeter/(props[i].equivalent_diameter*pi),3)
#            eqdiam_px=round(props[i].equivalent_diameter)
#            #eqdiam_rel=round(props[i].perimeter/props[i].equivalent_diameter)
#            
#            perim_px=round(props[i].perimeter)
#            perim_rel=round(props[i].perimeter/refperim,2)
#            
#            area_px=round(props[i].area,3)
#            area_rel=round(props[i].area/refarea,3)
#            
#            #perim_px=round(props[i].perimeter)
#            #perim_rel=round(props[i].perimeter)
#            
#            #eqr=math.sqrt(props[0].area/pi)
#            si_str="{}".format(si)
#            eqdiam_str="{}{}".format(eqdiam_px, self.perimUnit)
#            perim_str="{}{} ({})".format(perim_px,self.perimUnit,perim_rel)
#            area_str="{}{} ({})".format(area_px,self.areaUnit,area_rel)
#            
#            
#            stats.append({"i":i,
#                          "area_rel":area_rel,
#                          "area_px":area_px,
#                          "perim_px":perim_px,
#                          "perim_rel":perim_rel,
#                          "si":si,
#                          "eqdiam_px":eqdiam_px})
#            statsStr.append({"area":area_str,"perim":perim_str,"si":si_str,"eqdiam":eqdiam_str})
#            
#            areaUnit="px" if self.refarea==1 else self.areaUnit
#            perimUnit="px" if self.refperim==1 else self.perimUnit
#            
#            #print("i ",i," refarea ",refarea," areaUnit ",areaUnit," area_rel ",area_rel," refperim ",refperim," perim_rel ",perim_rel," perimUnit ",perimUnit)
#            
#            if i==0:
#                labeltext.append("reference area\nArea: {}{} ({})\nperimeter: {}{} ({})".format(
#                        round(refarea),areaUnit,1,
#                        round(refperim),perimUnit,1))
#            else:
#                #print("refarea>>:",self.refarea)
#                #print("refperim>>:",self.refperim)
#                #print("blabl",round(area_px/refarea,2))
#                #print("type1",type(area_px/refarea))
#                #print("blabl",self.refperim)
#                #print("type2",type(self.refperim))
#                
#                labeltext.append("Object {}\n Area: {}{} ({})\nPerimeter: -{}{} ({})\nShape index: {}".format(
#                        i,
#                        str(round(area_px/(1 if self.refarea==1 else refarea),2)*self.refarea),self.areaUnit, round(area_px/refarea,4),
#                        str(round(perim_px/(1 if self.refperim==1 else refperim)*self.refperim)),self.perimUnit, round(perim_px/refperim,4),
#                        si))
#                

            
        #meanarea=np.mean([x["area_px"] for x in stats])
        
        df=pd.DataFrame({
                "si":[round(p.perimeter/(p.equivalent_diameter*pi),3) for p in props],
                "area_rel":[round(p.area/refarea,3) for p in props],
                "area_px":[round(p.area,3) for p in props],
                "eqdiam_px":[round(p.equivalent_diameter) for p in props],
                "perim_px":[round(p.perimeter) for p in props],
                "perim_rel":[round(p.perimeter/refperim,2) for p in props],
                "path":imgpath
                })

        debugimage=debugimage[25:(originalsize[0]+25),25:(originalsize[1]+25)]
        labelled=labelled[25:(originalsize[0]+25),25:(originalsize[1]+25)]
                
        return (leafarea,debugimage,labelled,props,statsStr,df.drop(0),refarea,refperim,labeltext)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())
