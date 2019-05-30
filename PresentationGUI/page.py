import tkinter as tk
from tkinter import StringVar
from tkinter import IntVar
from tkinter import ttk
from tkinter import Canvas
from tkinter import filedialog
from tkinter import messagebox
from tkinter import HORIZONTAL
from tkinter.ttk import Progressbar
import math
from pprint import pprint
from pprint import pformat
import OpenCVFunctions as imFunc
import jsonFunctions as jFunc
import custExceptions as cex
import statistics
import threading
import checkFunctions as chk

# TrafficApp is the main frame that appears on program start
# It will contain the pages in the "mainFrame" frame and those pages will be int he form of classes e.g. "MainPage"
class trafficApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.setupFrameContainer()
    
    def setupFrameContainer(self):
        mainFrame = tk.Frame(self)
        mainFrame.pack(side="top", fill="both", expand = True)
        mainFrame.grid_rowconfigure(0, weight=1)
        mainFrame.grid_columnconfigure(0, weight=1)

        self.frames = {}
        frame = MainPage(mainFrame, self)
        self.frames[MainPage] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.showFrame(MainPage)

    def showFrame(self, frame):
        frame = self.frames[frame]
        frame.tkraise()

# This class contains pretty much the entire app
# It does not contain the extra Toplevel stuff, those are in their own classes below
class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.initiateVars()
        self.createPage()

    # These will be the conduits for the jsonFunctions and image stuff
    def initiateVars(self):
        self.jsonData = []
        self.jsonPath = "D:/OpenCVGUI/json/"
        self.jsonLocList = []
        self.imgPath = "D:/OpenCVGUI/img/"
        self.imgLocList = []
        self.currentImgPath = ""
        self.moddedJsonData = []
        self.size = 0
        self.frameTrack = 0
        self.finalCountData = {}
        self.finalSpeedData = {}
        self.searchOption = 1
        self.frameChoice = 1        
        # Tolerance is the score variable
        # dThreshold is the max distance before it stops tracking entities around it
        # sThreshold is the minimum distance before object is considered stationary
        self.tolerance, self.dThreshold, self.sThreshold = 0.98, 10, 2.5
        self.boundingBoxArea = 0

    def createPage(self):
        # All frames needed for entire page
        masterFrame = tk.Frame(self)
        imageFrame = tk.Frame(masterFrame, background='gray')
        userFrame = tk.Frame(masterFrame)

        self.display = Canvas(imageFrame, bd=0, highlightthickness=0)
        self.display.create_image(0, 0, image=None, anchor="nw", tags="IMG")
        self.display.pack(side="bottom", fill="both", expand=True)
        self.directoryLocator()

        # Denotations: IV = IntVar | SV = StringVar
        # All Vars for userFrame
        self.frameEntryIV = tk.IntVar()
        self.ofFramesLabelSV = tk.StringVar()
        self.searchOpIV = tk.IntVar()
        self.searchOpIV.set(1)
        self.frameSelectIV = tk.IntVar()
        self.frameSelectIV.set(1)
        self.statusLabelSV = tk.StringVar()
        self.bikeCount = tk.StringVar()
        self.carCount = tk.StringVar()
        self.peopleCount = tk.StringVar()

        # Format all frames for entire page
        masterFrame.pack(side="top", fill="both", expand=True)
        masterFrame.grid_rowconfigure(0, weight=1)
        masterFrame.grid_columnconfigure(0, weight=1)
        imageFrame.grid(row=0, column=0, sticky="nsew")
        userFrame.grid(row=0, column=1, sticky="nsew", columnspan=3)

        # All frames needed for userFrame formatting
        traversalFrame = tk.Frame(userFrame)
        searchOpFrame = tk.Frame(userFrame)
        searchEntryFrame = tk.Frame(userFrame)
        frameRBFrame = tk.Frame(userFrame)
        self.specificFrame = tk.Frame(userFrame)
        entityCBFrame = tk.Frame(userFrame)
        self.countResultsFrame = tk.Frame(userFrame)
        self.regionResultsFrame = tk.Frame(userFrame)
        self.congestionResultsFrame = tk.Frame(userFrame)
        footerFrame = tk.Frame(userFrame)

        # Format all frames for userFrame
        ## userFrame title row=0
        traversalFrame.grid(row=1, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)
        traversalFrame.grid_columnconfigure(1, weight=1)

        ## Search Options title row=2

        searchOpFrame.grid(row=3, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)

        searchEntryFrame.grid(row=4, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)
        # Frame Select title row=5

        frameRBFrame.grid(row=6, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)
        frameRBFrame.grid_columnconfigure(0, weight=1)
        frameRBFrame.grid_rowconfigure(0, weight=1)

        self.specificFrame.grid(row=7, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)
        self.specificFrame.grid_rowconfigure(0, weight=1)

        # Entity Filter title row=8

        entityCBFrame.grid(row=9, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)
        entityCBFrame.grid_rowconfigure(0, weight=1)

        self.countResultsFrame.grid(row=10, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)

        self.regionResultsFrame.grid(row=11, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)

        self.congestionResultsFrame.grid(row=12, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)

        footerFrame.grid(row=99, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
        footerFrame.grid_columnconfigure(0, weight=1)
        footerFrame.grid_columnconfigure(1, weight=1)
        footerFrame.grid_rowconfigure(2, weight=1)

        # Checkboxes for filters | values will be 0 or 1 depending on whether it is filtered or not
        self.bikeCB = tk.IntVar()
        self.carCB = tk.IntVar()
        self.peopleCB = tk.IntVar()

        # Populate userFrame
        titleLabel = tk.Label(userFrame, text="Traffic Analysis", font=("Calibri", 14))
        settingsButton = tk.Button(userFrame, text="Settings", command=self.settingsOpen)

        # Populate traversalFrame
        prevButton = tk.Button(traversalFrame, text="<<", command=lambda: self.imageValueControl("back"))
        self.frameEntry = tk.Entry(traversalFrame, textvariable=self.frameEntryIV)
        ofFramesLabel = tk.Label(traversalFrame, textvariable=self.ofFramesLabelSV)
        nextButton = tk.Button(traversalFrame, text=">>", command=lambda: self.imageValueControl("forth"))

        # Populate searchOpFrame
        searchOpLabel = tk.Label(searchOpFrame, text="Search Options", font=("Calibri", 12))
        countRB = tk.Radiobutton(searchOpFrame, text="Count", value=1, variable=self.searchOpIV, command=lambda: self.searchOpRBChange(1))
        regionRB = tk.Radiobutton(searchOpFrame, text="Speed", value=2, variable=self.searchOpIV, command=lambda: self.searchOpRBChange(2))

        # Populate searchEntryFrame
        ## Frame Replace Content - Count
        self.countFrame = tk.Frame(searchEntryFrame)
        countTitle = tk.Label(self.countFrame, text="Count Between", font=("Calibri", 12))
        startLineLabel = tk.Label(self.countFrame, text="Line 1: ")
        self.startLineEntry = tk.Entry(self.countFrame)
        endLineLabel = tk.Label(self.countFrame, text="Line 2: ")
        self.endLineEntry = tk.Entry(self.countFrame)
        countSetButton = tk.Button(self.countFrame, text="Set", command = self.countSetButtonFunc)

        ## Frame Replace Content = Region
        self.regionFrame = tk.Frame(searchEntryFrame)
        regionTitle = tk.Label(self.regionFrame, text="Region Define", font=("Calibri", 12))
        x1Label = tk.Label(self.regionFrame, text="X1:")
        self.x1Entry = tk.Entry(self.regionFrame, width=4)
        x2Label = tk.Label(self.regionFrame, text="X2:")
        self.x2Entry = tk.Entry(self.regionFrame, width=4)
        y1Label = tk.Label(self.regionFrame, text="Y1:")
        self.y1Entry = tk.Entry(self.regionFrame, width=4)
        y2Label = tk.Label(self.regionFrame, text="Y2:")
        self.y2Entry = tk.Entry(self.regionFrame, width=4)
        regionSetButton = tk.Button(self.regionFrame, text="Set", command=self.regionSetButtonFunc)

        # Populate frameRBFrame
        frameSelectTitle = tk.Label(frameRBFrame, text="Frame Select", font=("Calibri", 12))
        allRB = tk.Radiobutton(frameRBFrame, text="All", variable=self.frameSelectIV, val=1, command = lambda: self.frameOpRBChange(1))
        currentRB = tk.Radiobutton(frameRBFrame, text="Current", variable=self.frameSelectIV, val=2, command = lambda: self.frameOpRBChange(2))
        specificRB = tk.Radiobutton(frameRBFrame, text="Specific", variable=self.frameSelectIV, val=3, command = lambda: self.frameOpRBChange(3))

        # Populate specificFrame
        specFromLabel = tk.Label(self.specificFrame, text="Specific:")
        self.fromEntry = tk.Entry(self.specificFrame)
        specToLabel = tk.Label(self.specificFrame, text="To:")
        self.toEntry = tk.Entry(self.specificFrame)

        # Populate entityCBFrame
        entityCBTitle = tk.Label(entityCBFrame, text="Entity Select", font=("Calibri", 12))
        bikeCB = tk.Checkbutton(entityCBFrame, text="Bike", variable=self.bikeCB)
        carCB = tk.Checkbutton(entityCBFrame, text="Car", variable=self.carCB)
        peopleCB = tk.Checkbutton(entityCBFrame, text="People", variable=self.peopleCB)

        # Populate countResultsFrame
        countTitle = tk.Label(self.countResultsFrame, text="Count Results", font=("Calibri", 12))
        bikeCount = tk.Label(self.countResultsFrame, textvariable=self.bikeCount)
        carCount = tk.Label(self.countResultsFrame, textvariable=self.carCount)
        peopleCount = tk.Label(self.countResultsFrame, textvariable=self.peopleCount)

        # Populate regionResultsFrame
        regionResultsTitle = tk.Label(self.regionResultsFrame, text="Region Results", font=("Calibri", 12))
        minLbl = tk.Label(self.regionResultsFrame, text="Min")
        avgLbl = tk.Label(self.regionResultsFrame, text="Avg")
        maxLbl = tk.Label(self.regionResultsFrame, text="Max")
        bikeLbl = tk.Label(self.regionResultsFrame, text="Bikes: ")
        carLbl = tk.Label(self.regionResultsFrame, text="Cars: ")
        peopleLbl = tk.Label(self.regionResultsFrame, text="People: ")
        self.bikeMin = tk.Label(self.regionResultsFrame, text="")
        self.bikeAvg = tk.Label(self.regionResultsFrame, text="")
        self.bikeMax = tk.Label(self.regionResultsFrame, text="")
        self.carMin = tk.Label(self.regionResultsFrame, text="")
        self.carAvg = tk.Label(self.regionResultsFrame, text="")
        self.carMax = tk.Label(self.regionResultsFrame, text="")
        self.peopleMin = tk.Label(self.regionResultsFrame, text="")
        self.peopleAvg = tk.Label(self.regionResultsFrame, text="")
        self.peopleMax = tk.Label(self.regionResultsFrame, text="")

        # Populate congestionResultsFrame
        congestionResultsTitle = tk.Label(self.congestionResultsFrame, text="Congestion Results", font=("Calibri", 12))
        congestionScore = tk.Label(self.congestionResultsFrame, text="")
        vehicleMax = tk.Label(self.congestionResultsFrame, text="")

        # Populate userFrame BOTTOM ONLY (StatusLabel, PrevResults, Search)
        clearResultsButton = tk.Button(footerFrame, text="Clear Results", command=self.clearResults)
        searchButton = tk.Button(footerFrame, text="Search", command=self.searchForResults)
        statusLabel = tk.Label(footerFrame, text="Status Label Positioning", textvariable=self.statusLabelSV)
        self.progressBar = Progressbar(footerFrame, orient=HORIZONTAL, length=200, mode='indeterminate')

        # Place all items into the app
        ## Title Contents
        titleLabel.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        settingsButton.grid(row=0, column=2, sticky="e", padx=5, pady=5)

        ## traversalFrame Contents
        prevButton.grid(row=0, column=0, sticky="nsew")
        self.frameEntry.grid(row=0, column=1, sticky="nsew")
        ofFramesLabel.grid(row=0, column=2, sticky="nsew")
        nextButton.grid(row=0, column=3, sticky="nsew")

        ## searchOpFrame Contents
        searchOpLabel.grid(row=0, column=0, columnspan=3, sticky="w", pady=3, padx=3)
        countRB.grid(row=1, column=0, sticky="w")
        regionRB.grid(row=1, column=3, sticky="e")
        
        ## searchEntryFrame Contents
        # Note that this is only for initialization, will change later due to radiobutton values
        # Region shall replace or be replaced by the below code
        self.countFrame.grid(row=0, column=0, sticky="w", pady=3, padx=3)
        countTitle.grid(row=0, column=0, sticky="w", pady=3, padx=3, columnspan=3)
        startLineLabel.grid(row=1, column=0, sticky="w", padx=3, pady=3)
        self.startLineEntry.grid(row=1, column=1, sticky="w", padx=3, pady=3, columnspan=3)
        endLineLabel.grid(row=2, column=0, sticky="w", padx=3, pady=3)
        self.endLineEntry.grid(row=2, column=1, sticky="w", padx=3, pady=3, columnspan=3)
        countSetButton.grid(row=3, column=1, sticky="e", padx=3, pady=3, columnspan=3)

        # Region Code
        self.regionFrame.grid(row=0, column=0, sticky="w", pady=3, padx=3)
        regionTitle.grid(row=0, column=0, sticky="w", pady=3, padx=3, columnspan=3)
        x1Label.grid(row=1, column=0, sticky="w", padx=3, pady=3)
        self.x1Entry.grid(row=1, column=1, sticky="w", padx=3, pady=3)
        x2Label.grid(row=1, column=2, sticky="w", padx=3, pady=3)
        self.x2Entry.grid(row=1, column=3, sticky="w", padx=3, pady=3)
        y1Label.grid(row=2, column=0, sticky="w", padx=3, pady=3)
        self.y1Entry.grid(row=2, column=1, sticky="w", padx=3, pady=3)
        y2Label.grid(row=2, column=2, sticky="w", padx=3, pady=3)
        self.y2Entry.grid(row=2, column=3, sticky="w", padx=3, pady=3)
        regionSetButton.grid(row=3, column=3, sticky="e", padx=3, pady=3)
        self.regionFrame.grid_forget()

        ## frameRBFrame Contents
        frameSelectTitle.grid(row=0, column=0, sticky="w", pady=3, padx=3, columnspan=3)
        allRB.grid(row=1, column=0, sticky="w", pady=3, padx=3)
        currentRB.grid(row=1, column=1, sticky="w", pady=3, padx=3)
        specificRB.grid(row=1, column=2, sticky="w", pady=3, padx=3)

        ## specificFrame Contents
        specFromLabel.grid(row=0, column=0, sticky="w", pady=3, padx=3)
        self.fromEntry.grid(row=0, column=1, sticky="w", pady=3, padx=3)
        specToLabel.grid(row=1, column=0, sticky="e", pady=3, padx=3)
        self.toEntry.grid(row=1, column=1, sticky="w", pady=3, padx=3)
        self.specificFrame.grid_forget()

        ## entityCBFrame Contents
        entityCBTitle.grid(row=0, column=0, sticky="w", pady=3, padx=3, columnspan=3)
        bikeCB.grid(row=1, column=0, sticky="w", pady=3, padx=3)
        carCB.grid(row=1, column=1, sticky="w", pady=3, padx=3)
        peopleCB.grid(row=1, column=2, sticky="w", pady=3, padx=3)

        ## Results Frames Contents
        # countResultsFrame Contents
        countTitle.grid(row=0, column=0, sticky="w")
        bikeCount.grid(row=1, column=0, sticky="w")
        carCount.grid(row=2, column=0, sticky="w")
        peopleCount.grid(row=3, column=0, sticky="w")
        self.countResultsFrame.grid_forget()

        # regionResultsFrame Contents
        regionResultsTitle.grid(row=0, column=0, sticky="w", columnspan=5)

        minLbl.grid(row=1, column=1, sticky="w")
        avgLbl.grid(row=1, column=2, sticky="w")
        maxLbl.grid(row=1, column=3, sticky="w")

        bikeLbl.grid(row=2, column=0, sticky="w")
        carLbl.grid(row=3, column=0, sticky="w")
        peopleLbl.grid(row=4, column=0, sticky="w")

        self.bikeMin.grid(row=2, column=1, sticky="w")
        self.bikeAvg.grid(row=2, column=2, sticky="w")
        self.bikeMax.grid(row=2, column=3, sticky="w")

        self.carMin.grid(row=3, column=1, sticky="w")
        self.carAvg.grid(row=3, column=2, sticky="w")
        self.carMax.grid(row=3, column=3, sticky="w")

        self.peopleMin.grid(row=4, column=1, sticky="w")
        self.peopleAvg.grid(row=4, column=2, sticky="w")
        self.peopleMax.grid(row=4, column=3, sticky="w")

        self.regionResultsFrame.grid_forget()

        # congestionResultsFrame Contents
        congestionResultsTitle.grid(row=0, column=0, columnspan=5, sticky="w", padx=3, pady=3)
        congestionScore.grid(row=1, column=0, pady=3, padx=3, sticky="w")
        vehicleMax.grid(row=2, column=0, pady=3, padx=3, sticky="w")
        self.congestionResultsFrame.grid_forget()

        ## footerFrame Contents
        clearResultsButton.grid(row=0, column=0, sticky="sw", pady=3, padx=3)
        searchButton.grid(row=0, column=2, sticky="sw", pady=3, padx=3)
        statusLabel.grid(row=1, column=0, sticky="sw", pady=3, padx=3)
        self.progressBar.grid(row=2, column=0, sticky="nsew", pady=3, padx=3, columnspan=5)

        # SV / IV Default values and settings
        self.frameEntryIV.set(1)
        self.ofFramesLabelSV.set("of 0")
        self.bikeCB.set(1)
        self.carCB.set(1)
        self.peopleCB.set(1)

        # Invokes
        allRB.invoke()
        countRB.invoke()

    ## imageFrame Functions
    # All functions pertaining to the import or changing of anything
    # within the imageFrame frame

    # Auto-Resizes the image by passing the event <Configure> bound at creation
    def resize(self, event):
        def resizeImage():
            if not self.currentImgPath == "":
                img = imFunc.cv2.imread(self.currentImgPath)
                self.size = (event.width, event.height)
                resized = imFunc.scaleImageNew(img, self.size)
                newImage = imFunc.convertImageForPIL(resized)
                self.display.delete("IMG")
                self.display.create_image(0, 0, image=newImage, anchor="nw", tags="IMG")
                self.display.image = newImage
            else:
                raise cex.noImgPassed("Called from Resize, if seen on launch ignore!")
        
        threading.Thread(target=resizeImage).start()
    
    def changeImage(self, imgNum):
        def countImageChange(imgNum):
            self.progressBar.start()
            if not imgNum < 0:
                imgNum -= 1

            self.currentImgPath = self.imgLocList[imgNum]
            if not self.moddedJsonData == "" and not self.startLineEntry.get() == "" and not self.endLineEntry.get() == "":
                if self.frameChoice == 1 or self.frameChoice == 3:
                    self.moddedJsonData = jFunc.filterAllByClass(self.moddedJsonData, self.getFilterDict())
                    entityList = jFunc.getEntitiesWithinLines(self.moddedJsonData[imgNum])
                    img = imFunc.getSingleImageLineYNew(entityList, self.currentImgPath, self.startLineEntry.get(), self.endLineEntry.get(), self.size)
                    self.display.delete("IMG")
                    self.display.create_image(0, 0, image=img, anchor="nw", tags="IMG")
                    self.display.image = img
                elif self.frameChoice == 2:
                    self.moddedJsonData = jFunc.filterByClass(self.moddedJsonData[imgNum], self.getFilterDict())
                    entityList = jFunc.getEntitiesWithinLines(self.moddedJsonData)
                    img = imFunc.getSingleImageLineYNew(entityList, self.currentImgPath, self.startLineEntry.get(), self.endLineEntry.get(), self.size)
                    self.display.delete("IMG")
                    self.display.create_image(0, 0, image=img, anchor="nw", tags="IMG")
                    self.display.image = img
            elif self.startLineEntry.get() == "" or self.endLineEntry.get() == "":
                img = imFunc.getSingleImageNew(self.currentImgPath, self.size)
                self.display.delete("IMG")
                self.display.create_image(0, 0, image=img, anchor="nw", tags="IMG")
                self.display.image = img
            self.progressBar.stop()
        countImageChange(imgNum)
        # threading.Thread(target=lambda: countImageChange(imgNum)).start()

    def changeImageRegion(self, imgNum):
        def regionChangeImage(imgNum):
            self.progressBar.start()
            if not imgNum < 0:
                imgNum -= 1
            
            self.currentImgPath = self.imgLocList[imgNum]
            if not self.moddedJsonData == "" and not self.x1Entry.get() == "" and not self.x2Entry.get() == "" and not self.y1Entry.get() == "" and not self.y2Entry.get() == "":
                try:
                    entityList = jFunc.getEntitiesWithinBox(self.moddedJsonData[imgNum], self.getCoordTuple())
                    img = imFunc.getSingleImageRegion(entityList, self.currentImgPath, self.getCoordTuple(), self.size)
                    self.display.delete("IMG")
                    self.display.create_image(0, 0, image=img, anchor="nw", tags="IMG")
                    self.display.image = img
                except TypeError:
                    messagebox.showinfo("Error", "No recognisable entities in that region. This could mean that the entities inside aren't of sufficient quality to be considered in the results.")
            elif self.x1Entry.get() == "" or self.x2Entry.get() == "" or self.y1Entry.get() == "" or self.y2Entry.get() == "":
                img = imFunc.getSingleImageNew(self.currentImgPath, self.size)
                self.display.delete("IMG")
                self.display.create_image(0, 0, image=img, anchor="nw", tags="IMG")
                self.display.image = img
            self.progressBar.stop()
        regionChangeImage(imgNum)
        # threading.Thread(target=regionChangeImage).start()


    def imageValueControl(self, direction):
        currentVal = self.frameEntryIV.get()
        if(direction == "back"):
            if(currentVal == 1):
                # Set to highest possible value
                self.frameEntryIV.set(len(self.imgLocList))
            else:
                # Else decrement
                self.frameEntryIV.set(currentVal - 1)
        elif(direction == "forth"):
            if(currentVal > (len(self.imgLocList) - 1)):
                # Set to first value for first frame
                self.frameEntryIV.set(1)
            else:
                # Else increment
                currentVal = self.frameEntryIV.get()
                self.frameEntryIV.set(currentVal + 1)
        
        if(self.searchOption == 1):
            self.changeImage(int(self.frameEntryIV.get()))
        elif(self.searchOption == 2):
            self.changeImageRegion(int(self.frameEntryIV.get()))

    ## userFrame Functions
    # Radio Button grid changes and checkbox functions
    def searchOpRBChange(self, rbVal):
        self.searchOption = rbVal
        if(rbVal == 1):
            self.regionFrame.grid_forget()
            self.countFrame.grid(row=0, column=0, sticky="w", pady=3, padx=3)
        elif(rbVal == 2):
            self.countFrame.grid_forget()
            self.regionFrame.grid(row=0, column=0, sticky="w", pady=3, padx=3)

    def frameOpRBChange(self, rbVal):
        self.frameChoice = rbVal
        print(self.frameChoice)
        if not rbVal == 3:
            self.specificFrame.grid_forget()
        else:
            self.specificFrame.grid(row=7, column=0, sticky="nsew", padx=5, columnspan=3, pady=5)
            self.specificFrame.grid_rowconfigure(0, weight=1)
    
    # Menu Functions
    def settingsOpen(self):
        self.settingsMenu()
    
    ## Count Functions
    # Just stuff to do with counting entities
    def countSetButtonFunc(self):
        if not self.startLineEntry == "" or not self.endLineEntry == "":
            self.updateJsonData()
            self.changeImage(int(self.frameEntryIV.get()))
        else:
            messagebox.showinfo("Error", "Please ensure that the start and end lines are not blank.")

    ## Search Functions
    # Just stuff to do with searching or creating results
    # Count Functions
    def searchForResults(self):
        # Count == 1 || Region == 2
        if(self.searchOption == 1):
            self.countSelectedSearch()
        elif(self.searchOption == 2):
            self.regionSpeedSearch()

    def countSelectedSearch(self):
        self.updateJsonData()

        # Trims by page
        self.moddedJsonData = self.filterJsonDataByChoice(self.moddedJsonData)

        if self.frameChoice == 2:
            # Trims by class filters
            self.moddedJsonData = jFunc.filterByClass(self.moddedJsonData, self.getFilterDict())
        else:
            # Trims by class filters
            self.moddedJsonData = jFunc.filterAllByClass(self.moddedJsonData, self.getFilterDict())

        if self.frameChoice == 2:
            entityStructList = jFunc.countEntities(self.moddedJsonData)
            self.finalCountData['bike'] = (entityStructList['bike'])
            self.finalCountData['car'] = (entityStructList['car'])
            self.finalCountData['people'] = (entityStructList['person'])
        elif self.frameChoice == 1:
            entityStructList = jFunc.countAllEntities(self.moddedJsonData)
            self.finalCountData['bike'] = (str(jFunc.parseEntityStructList(entityStructList, 'bike')))
            self.finalCountData['car'] = (str(jFunc.parseEntityStructList(entityStructList, 'car')))
            self.finalCountData['people'] = (str(jFunc.parseEntityStructList(entityStructList, 'person')))
        elif self.frameChoice == 3:
            try:
                entityStructList = jFunc.countAllEntities(self.moddedJsonData)
                self.finalCountData['bike'] = (str(jFunc.parseEntityStructList(entityStructList, 'bike')))
                self.finalCountData['car'] = (str(jFunc.parseEntityStructList(entityStructList, 'car')))
                self.finalCountData['people'] = (str(jFunc.parseEntityStructList(entityStructList, 'person')))
            except IndexError:
                messagebox.showinfo("Error", "Selected range is above or below the /json/ location may provide.")

        self.updateGUICount()

    def updateGUICount(self):
        try:
            self.bikeCount.set("Bikes: " + str(self.finalCountData['bike']))
            self.carCount.set("Cars: " + str(self.finalCountData['car']))
            self.peopleCount.set("People: " + str(self.finalCountData['people']))
            self.showCountResults()
        except KeyError:
            print("GUI - Count aborted update.")

    def showCountResults(self):
        self.countResultsFrame.grid(row=10, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
        if(self.regionResultsFrame.winfo_ismapped() and not self.congestionResultsFrame.winfo_ismapped()):
            # self.congestionResultsFrame.grid(row=12, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
            self.resultsPage()

    # Region Functions
    def regionSetButtonFunc(self):
        self.updateJsonData()
        if not self.x1Entry.get() == "":
            self.changeImageRegion(int(self.frameEntryIV.get()))
        else:
            messagebox.showinfo("Error", "Please enter all points before setting your box locale.")
    
    def getCoordTuple(self):
        coordTuple = (int(self.x1Entry.get()), int(self.x2Entry.get()), int(self.y1Entry.get()), int(self.y2Entry.get()))
        self.boundingBoxArea = jFunc.findBoundingBoxArea(coordTuple)
        return coordTuple

    def regionSpeedSearch(self):
        self.updateJsonData()

        # Trims the jsonData down to be more efficient
        self.moddedJsonData = self.filterJsonDataByChoice(self.moddedJsonData)

        # Trims by class filters
        self.moddedJsonData = jFunc.filterAllByClass(self.moddedJsonData, self.getFilterDict())

        # Dict for storing Results
        # In getAverageSpeed etc method 1 = Bike, 2 = Car and 3 = Person
        # Current
        if self.frameChoice == 2:
            entityStructList = jFunc.getAverageSpeedOfSingleVehicleList(self.moddedJsonData, 1, self.getCoordTuple())
            self.finalSpeedData['bikeAvg'] = entityStructList['avgSpeed']
            self.finalSpeedData['bikeMin'] = entityStructList['minSpeed']
            self.finalSpeedData['bikeMax'] = entityStructList['maxSpeed']

            entityStructList = jFunc.getAverageSpeedOfSingleVehicleList(self.moddedJsonData, 2, self.getCoordTuple())
            self.finalSpeedData['carAvg'] = entityStructList['avgSpeed']
            self.finalSpeedData['carMin'] = entityStructList['minSpeed']
            self.finalSpeedData['carMax'] = entityStructList['maxSpeed']

            entityStructList = jFunc.getAverageSpeedOfSingleVehicleList(self.moddedJsonData, 3, self.getCoordTuple())
            self.finalSpeedData['peopleAvg'] = entityStructList['avgSpeed']
            self.finalSpeedData['peopleMin'] = entityStructList['minSpeed']
            self.finalSpeedData['peopleMax'] = entityStructList['maxSpeed']
        # All
        elif self.frameChoice == 1:
            entityStructList = jFunc.getAverageSpeedOfVehicle(self.moddedJsonData, 1, self.getCoordTuple())
            self.finalSpeedData['bikeAvg'] = entityStructList['avgSpeed']
            self.finalSpeedData['bikeMin'] = entityStructList['minSpeed']
            self.finalSpeedData['bikeMax'] = entityStructList['maxSpeed']

            entityStructList = jFunc.getAverageSpeedOfVehicle(self.moddedJsonData, 2, self.getCoordTuple())
            self.finalSpeedData['carAvg'] = entityStructList['avgSpeed']
            self.finalSpeedData['carMin'] = entityStructList['minSpeed']
            self.finalSpeedData['carMax'] = entityStructList['maxSpeed']

            entityStructList = jFunc.getAverageSpeedOfVehicle(self.moddedJsonData, 3, self.getCoordTuple())
            self.finalSpeedData['peopleAvg'] = entityStructList['avgSpeed']
            self.finalSpeedData['peopleMin'] = entityStructList['minSpeed']
            self.finalSpeedData['peopleMax'] = entityStructList['maxSpeed']
        # Specific
        elif self.frameChoice == 3:
            try:
                entityStructList = jFunc.getAverageSpeedOfVehicle(self.moddedJsonData, 1, self.getCoordTuple())
                self.finalSpeedData['bikeAvg'] = entityStructList['avgSpeed']
                self.finalSpeedData['bikeMin'] = entityStructList['minSpeed']
                self.finalSpeedData['bikeMax'] = entityStructList['maxSpeed']

                entityStructList = jFunc.getAverageSpeedOfVehicle(self.moddedJsonData, 2, self.getCoordTuple())
                self.finalSpeedData['carAvg'] = entityStructList['avgSpeed']
                self.finalSpeedData['carMin'] = entityStructList['minSpeed']
                self.finalSpeedData['carMax'] = entityStructList['maxSpeed']

                entityStructList = jFunc.getAverageSpeedOfVehicle(self.moddedJsonData, 3, self.getCoordTuple())
                self.finalSpeedData['peopleAvg'] = entityStructList['avgSpeed']
                self.finalSpeedData['peopleMin'] = entityStructList['minSpeed']
                self.finalSpeedData['peopleMax'] = entityStructList['maxSpeed']
            except IndexError:
                messagebox.showinfo("Error", "Selected range is above or below the /json/ location may provide.")

        self.updateGUIRegion()
    
    def updateGUIRegion(self):
        try:
            self.bikeMin['text'] = str(round(self.finalSpeedData['bikeMin'], 3))
            self.bikeAvg['text'] = str(round(self.finalSpeedData['bikeAvg'], 3))
            self.bikeMax['text'] = str(round(self.finalSpeedData['bikeMax'], 3))

            self.carMin['text'] = str(round(self.finalSpeedData['carMin'], 3))
            self.carAvg['text'] = str(round(self.finalSpeedData['carAvg'], 3))
            self.carMax['text'] = str(round(self.finalSpeedData['carMax'], 3))

            self.peopleMin['text'] = str(round(self.finalSpeedData['peopleMin'], 3))
            self.peopleAvg['text'] = str(round(self.finalSpeedData['peopleAvg'], 3))
            self.peopleMax['text'] = str(round(self.finalSpeedData['peopleMax'], 3))

            self.showRegionResults()
        except KeyError:
            print("GUI - Region aborted update.")
    
    def showRegionResults(self):
        self.regionResultsFrame.grid(row=11, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
        if(self.countResultsFrame.winfo_ismapped() and not self.congestionResultsFrame.winfo_ismapped()):
            # self.congestionResultsFrame.grid(row=12, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
            self.resultsPage()
    
    def clearResults(self):
        if self.regionResultsFrame.winfo_ismapped():
            self.regionResultsFrame.grid_forget()
        if self.countResultsFrame.winfo_ismapped():
            self.countResultsFrame.grid_forget()
        if self.congestionResultsFrame.winfo_ismapped():
            self.congestionResultsFrame.grid_forget()

    # Directory toplevel because I can't access methods outside of class without mass performance drops
    # All methods below
    def directoryLocator(self):
        self.dLocate = tk.Toplevel()
        self.dLocate.wm_title("Directory Locator")
        self.dLocate.attributes('-topmost', 'true')
        self.createDirectoryLocator()
    
    def createDirectoryLocator(self):
        # Features
        dirFrame = tk.Frame(self.dLocate)
        dirTitle = tk.Label(dirFrame, text="Please select your directory containing img / json folders")
        self.dirButton = tk.Button(dirFrame, text="Select", command=self.directorySet)

        # Implementation
        dirFrame.grid(row=0, column=0, columnspan=5, pady=5, padx=5)
        dirTitle.grid(row=0, column=0, padx=3, pady=3, sticky="w")
        self.dirButton.grid(row=1, column=0, padx=3, pady=3, sticky="e")

    def directorySet(self):
        def setupDirectory():
            self.progressBar.start()
            path = tk.filedialog.askdirectory()
            self.jsonPath = path + "/json/"
            self.imgPath = path + "/img/"
            self.importAllDataFromFolder(path)
            if(self.imgLocList == []):
                messagebox.showinfo("Error", "No 'img' folder found at location.")
            elif(self.jsonLocList == []):
                messagebox.showinfo("Error", "No 'json' folder found at location.")
            else:
                self.currentImgPath = self.imgLocList[0]
                self.bind("<Configure>", self.resize)
                self.setupBaseGUI()
                self.dLocate.destroy()
            self.progressBar.stop()
        
        threading.Thread(target=setupDirectory).start()
    
    def importAllDataFromFolder(self, path):
        self.progressBar.start()
        imgPath = path + "/img/"
        jPath = path + "/json/"
        self.imgLocList = jFunc.getAllImgFileLoc(imgPath)
        self.jsonLocList = jFunc.getAllJsonFileLoc(jPath)

        # Check for img not being empty
        if not self.imgLocList == [] or not self.imgLocList == None:
            # Check for json not being empty
            if not self.jsonLocList == [] or not self.jsonLocList == None:
                self.jsonData = jFunc.getAllJsonFiles(self.jsonLocList)
        self.progressBar.stop()
    
    def setupBaseGUI(self):
        self.frameEntryIV.set(1)
        self.ofFramesLabelSV.set("of " + str(len(self.imgLocList)))
        self.size = (1200, 800)
        self.changeImage(1)
    
    # Getters and setters
    def getFilterDict(self):
        filterDict = {}
        filterDict['bike'] = self.bikeCB.get()
        filterDict['car'] = self.carCB.get()
        filterDict['people'] = self.peopleCB.get()

        return filterDict

    def updateJsonData(self):
        if self.searchOption == 1:
            if not self.startLineEntry.get() == "" and not self.endLineEntry.get() == "":
                self.moddedJsonData = jFunc.refineAndPrepareJsonData(self.jsonData, int(self.startLineEntry.get()), int(self.endLineEntry.get()), self.tolerance, self.dThreshold, self.sThreshold)
            else:
                messagebox.showinfo("Error", "Please ensure that both Lines are not blank.")
        elif self.searchOption == 2:
            if not self.x1Entry.get() == "" and not self.x2Entry.get() == "" and not self.y1Entry.get() == "" and not self.y2Entry.get() == "":
                self.moddedJsonData = jFunc.refineAndPrepareJsonDataRegion(self.jsonData, self.tolerance, self.dThreshold, self.sThreshold)
            else:
                messagebox.showinfo("Error", "Please ensure that all points have been entered.")
    
    def updateJsonDataSettings(self):
        self.moddedJsonData = jFunc.refineAndPrepareJsonDataRegion(self.jsonData, self.tolerance, self.dThreshold, self.sThreshold)

    def filterJsonDataByChoice(self, jsonData):
        if(self.frameChoice == 1):
            # All
            return jsonData
        elif(self.frameChoice == 2):
            # Current
            jsonData = self.jsonData[int(self.frameEntry.get()) - 1]
            return jsonData
        elif(self.frameChoice == 3):
            # Specific
            jsonData = self.specificJsonDataFilter(jsonData)
            return jsonData

    def specificJsonDataFilter(self, jsonData):
        fromInt = int(self.fromEntry.get())
        toInt = len(self.jsonLocList) - int(self.toEntry.get())
        toInt = len(self.jsonLocList) - toInt

        if(fromInt < toInt):
            newJD = jsonData[fromInt:toInt]
        elif(toInt < fromInt):
            newJD = jsonData[fromInt:toInt]

        return newJD
    
    # Settings Menu Code
    def settingsMenu(self):
        self.settingsGUI = tk.Toplevel(self)
        self.settingsGUI.wm_title("Settings")
        self.settingsGUI.attributes('-topmost', 'true')
        self.setupGUIElements()

    def setupGUIElements(self):
        # Frames
        settingsFrame = tk.Frame(self.settingsGUI)

        # Entry Vars
        self.toleranceSV = tk.StringVar()
        self.dThresholdSV = tk.StringVar()
        self.sThresholdSV = tk.StringVar()

        # Labels
        settingsTitle = tk.Label(settingsFrame, text="Settings", font=("Calibri", 12))
        toleranceLabel = tk.Label(settingsFrame, text="Score Tolerance:")
        distThreshLabel = tk.Label(settingsFrame, text="Distance Threshold:")
        sThresholdLabel = tk.Label(settingsFrame, text="Movement Threshold:")

        # Entries
        toleranceEntry = tk.Entry(settingsFrame, textvariable=self.toleranceSV)
        distThreshEntry = tk.Entry(settingsFrame, textvariable=self.dThresholdSV)
        sThresholdEntry = tk.Entry(settingsFrame, textvariable=self.sThresholdSV)

        # Default Values Setup
        self.toleranceSV.set(self.tolerance)
        self.dThresholdSV.set(self.dThreshold)
        self.sThresholdSV.set(self.sThreshold)

        # Buttons
        setSettings = tk.Button(settingsFrame, text="Set", command=self.setSettings)

        # Populate settingsFrame
        settingsFrame.grid(row=0, column=0, sticky="nsew", ipady=5, ipadx=5)
        settingsTitle.grid(row=0, column=0, sticky="w", columnspan=5, padx=3, pady=3)
        toleranceLabel.grid(row=1, column=0, sticky="e", padx=3, pady=3)
        toleranceEntry.grid(row=1, column=1, sticky="w", padx=3, pady=3)

        distThreshLabel.grid(row=2, column=0, sticky="e", padx=3, pady=3)
        distThreshEntry.grid(row=2, column=1, sticky="w", padx=3, pady=3)

        sThresholdLabel.grid(row=3, column=0, sticky="e", padx=3, pady=3)
        sThresholdEntry.grid(row=3, column=1, sticky="w", padx=3, pady=3)

        setSettings.grid(row=4, column=0, columnspan=5, sticky="e", padx=3, pady=3)
    
    def setSettings(self):
        # Conversions
        tol = float(self.toleranceSV.get())
        dThresh = float(self.dThresholdSV.get())
        sThresh = float(self.sThresholdSV.get())

        if self.inputFilterSettings():        
            # Checks
            if not self.toleranceSV == "":
                self.tolerance = float(self.toleranceSV.get())
            if not self.dThresholdSV == "":
                self.dThreshold = float(self.dThresholdSV.get())
            if not self.sThresholdSV == "":
                self.sThreshold = float(self.sThresholdSV.get())

            self.updateJsonDataSettings()
            
            self.settingsGUI.destroy()
        else:
            messagebox.showerror("Error", "Please ensure the contents of the settings are non-negative numeric values.")
    
    def inputFilterSettings(self):
        if chk.onlyNumbersInStringCheck(self.toleranceSV.get()) and chk.onlyNumbersInStringCheck(self.dThresholdSV.get()) and chk.onlyNumbersInStringCheck(self.sThresholdSV.get()):
            return True
        else:
            return False

    def resultsPage(self):
        ## Main Init for Results
        resultsDisplay = tk.Toplevel(self)
        resultsFrame = tk.Frame(resultsDisplay)
        resultsFrame.pack(side="top", fill="both", expand=True)
        resultsDisplay.wm_title("Results Window")

        ## Widgets
        # Frames
        headerFrame = tk.Frame(resultsFrame)
        countFrame = tk.Frame(resultsFrame)
        speedFrame = tk.Frame(resultsFrame)
        congestionFrame = tk.Frame(resultsFrame)

        # Labels
        resultsTitle = tk.Label(headerFrame, text="Results", font=("Calibri", 14))

        countTitle = tk.Label(countFrame, text="Counted Objects", font=("Calibri", 12))
        bikeCount = tk.Label(countFrame, text="Bikes:")
        carCount = tk.Label(countFrame, text="Cars:")
        peopleCount = tk.Label(countFrame, text="People:")
        self.bikeRes = tk.Label(countFrame, text="")
        self.carRes = tk.Label(countFrame, text="")
        self.peopleRes = tk.Label(countFrame, text="")
        formatLabel = tk.Label(countFrame, text="Vehicle              #")

        speedTitle = tk.Label(speedFrame, text="Speed (px/s)", font=("Calibri", 12))
        minLabel = tk.Label(speedFrame, text="Min")
        avgLabel = tk.Label(speedFrame, text="Avg")
        maxLabel = tk.Label(speedFrame, text="Max")
        self.minResBike = tk.Label(speedFrame, text="")
        self.avgResBike = tk.Label(speedFrame, text="")
        self.maxResBike = tk.Label(speedFrame, text="")
        self.minResCar = tk.Label(speedFrame, text="")
        self.avgResCar = tk.Label(speedFrame, text="")
        self.maxResCar = tk.Label(speedFrame, text="")
        self.minResPeople = tk.Label(speedFrame, text="")
        self.avgResPeople = tk.Label(speedFrame, text="")
        self.maxResPeople = tk.Label(speedFrame, text="")

        congestionTitle = tk.Label(congestionFrame, text="Congestion Score", font=("Calibri", 12))
        scoreLabel = tk.Label(congestionFrame, text="Score:")
        self.scoreRes = tk.Label(congestionFrame, text="")

        ## Populate Frames
        # headerFrame
        headerFrame.grid(row=0, column=0, sticky="w", columnspan=4)
        resultsTitle.grid(row=0, column=0, sticky="w", columnspan=10)

        # countFrame
        countFrame.grid(row=1, column=0, sticky="w")
        countTitle.grid(row=0, column=0, sticky="w", columnspan=2)
        formatLabel.grid(row=1, column=0, sticky="w")
        bikeCount.grid(row=2, column=0, sticky="w")
        self.bikeRes.grid(row=2, column=1, sticky="w")
        carCount.grid(row=3, column=0, sticky="w")
        self.carRes.grid(row=3, column=1, sticky="w")
        peopleCount.grid(row=4, column=0, sticky="w")
        self.peopleRes.grid(row=4, column=1, sticky="w")

        # speedFrame
        speedFrame.grid(row=1, column=1, sticky="w")
        speedTitle.grid(row=0, column=0, sticky="w", columnspan=2)
        minLabel.grid(row=1, column=0, sticky="w")
        avgLabel.grid(row=1, column=1, sticky="w")
        maxLabel.grid(row=1, column=2, sticky="w")
        self.minResBike.grid(row=2, column=0, sticky="w")
        self.avgResBike.grid(row=2, column=1, sticky="w")
        self.maxResBike.grid(row=2, column=2, sticky="w")
        self.minResCar.grid(row=3, column=0, sticky="w")
        self.avgResCar.grid(row=3, column=1, sticky="w")
        self.maxResCar.grid(row=3, column=2, sticky="w")
        self.minResPeople.grid(row=4, column=0, sticky="w")
        self.avgResPeople.grid(row=4, column=1, sticky="w")
        self.maxResPeople.grid(row=4, column=2, sticky="w")

        # congestionFrame
        congestionFrame.grid(row=2, column=0, sticky="w", columnspan=2)
        congestionTitle.grid(row=0, column=0, sticky="w", columnspan=10)
        scoreLabel.grid(row=1, column=0, sticky="w")
        self.scoreRes.grid(row=1, column=1, sticky="w", columnspan=4)

        # Set Results
        self.bikeRes['text'] = self.finalCountData['bike']
        self.carRes['text'] = self.finalCountData['car']
        self.peopleRes['text'] = self.finalCountData['people']
        self.minResBike['text'] = self.finalSpeedData['bikeMin']
        self.avgResBike['text'] = self.finalSpeedData['bikeAvg']
        self.maxResBike['text'] = self.finalSpeedData['bikeMax']
        self.minResCar['text'] = self.finalSpeedData['carMin']
        self.avgResCar['text'] = self.finalSpeedData['carAvg']
        self.maxResCar['text'] = self.finalSpeedData['carMax']
        self.minResPeople['text'] = self.finalSpeedData['peopleMin']
        self.avgResPeople['text'] = self.finalSpeedData['peopleAvg']
        self.maxResPeople['text'] = self.finalSpeedData['peopleMax']

        areaJsonData = jFunc.getAllEntitiesWithinBox(self.moddedJsonData, self.getCoordTuple())
        scoreList = jFunc.getAreaTakenList(areaJsonData, self.boundingBoxArea)
        self.scoreRes['text'] = str(statistics.mean(scoreList)) + " out of 100"