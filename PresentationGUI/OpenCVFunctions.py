import cv2
import numpy as np
import matplotlib.pyplot as plt
import PIL
from PIL import Image
from PIL import ImageTk
import glob


def getSingleImage(imgPath, scale):
    imgOrigin = cv2.imread(imgPath)
    newImg = scaleImage(imgOrigin, scale)
    img = convertImageForPIL(newImg)

    return img

def getSingleImageNew(imgPath, size):
    img = cv2.imread(imgPath)
    img = scaleImageNew(img, size)
    img = convertImageForPIL(img)

    return img

def getSingleImageLineYNew(entityList, imgPath, lineY1, lineY2, size):
    lineYVal1 = int(lineY1)
    lineYVal2 = int(lineY2)
    img = cv2.imread(imgPath)

    lineThickness = 3
    # Draw lineY visually
    cv2.line(img, (0, lineYVal1), (1920, lineYVal1), (255, 0, 0), lineThickness)
    cv2.line(img, (0, lineYVal2), (1920, lineYVal2), (255, 0, 0), lineThickness)
    # Draw bounding boxes for all entities on LineY
    img = drawBoundingBox(img, entityList)

    # Scale Image
    img = scaleImageNew(img, size)

    # Make it compatible with tkinter
    newImg = convertImageForPIL(img)

    return newImg

def getSingleImageLineY(entityList, imgPath, lineY, scale):
    lineYVal = int(lineY)
    img = cv2.imread(imgPath)

    lineThickness = 3
    cv2.line(img, (0, lineYVal), (1920, lineYVal), (255, 0, 0), lineThickness)

    img = drawBoundingBox(img, entityList)

    newImg = scaleImage(img, scale)

    newImg = convertImageForPIL(newImg)

    return newImg

def getSingleImageRegion(entityList, imgPath, coordTuple, size):
    img = cv2.imread(imgPath)

    # Draw the selection box
    img2 = drawBoundingBoxRegion(img, coordTuple)

    # Highlight any entities inside the coords
    img3 = drawEntityBoundingBoxes(img2, entityList)

    # Scale Image
    img = scaleImageNew(img3, size)

    # Make it compatible with tkinter
    newImg = convertImageForPIL(img)

    return newImg

def drawBoundingBoxRegion(img, coordTuple):
    # Tuple structure - [0] x1 | [1] x2 | [2] y1 | [3] y2
    lineThickness = 2
    # Top
    cv2.line(img, (coordTuple[0], coordTuple[2]), (coordTuple[1], coordTuple[2]), (255, 0, 0), lineThickness)

    # Bottom
    cv2.line(img, (coordTuple[0], coordTuple[3]), (coordTuple[1], coordTuple[3]), (255, 0, 0), lineThickness)

    # Left
    cv2.line(img, (coordTuple[0], coordTuple[2]), (coordTuple[0], coordTuple[3]), (255, 0, 0), lineThickness)

    # Right
    cv2.line(img, (coordTuple[1], coordTuple[2]), (coordTuple[1], coordTuple[3]), (255, 0, 0), lineThickness)

    return img

def drawEntityBoundingBoxes(img, entityList):
    for entity in entityList:
        lineThickness = 2
        x1 = round(entity['box'][0])
        x2 = round(entity['box'][2])
        y1 = round(entity['box'][1])
        y2 = round(entity['box'][3])

        if(entity['movement'] < 2):
            # Top
            cv2.line(img, (x1, y1), (x2, y1), (0, 0, 255), lineThickness)

            # Bottom
            cv2.line(img, (x1, y2), (x2, y2), (0, 0, 255), lineThickness)

            # Left
            cv2.line(img, (x1, y1), (x1, y2), (0, 0, 255), lineThickness)

            # Right
            cv2.line(img, (x2, y1), (x2, y2), (0, 0, 255), lineThickness)
        elif(entity['movement'] >= 2):
            # Top
            cv2.line(img, (x1, y1), (x2, y1), (128, 128, 128), lineThickness)

            # Bottom
            cv2.line(img, (x1, y2), (x2, y2), (128, 128, 128), lineThickness)

            # Left
            cv2.line(img, (x1, y1), (x1, y2), (128, 128, 128), lineThickness)

            # Right
            cv2.line(img, (x2, y1), (x2, y2), (128, 128, 128), lineThickness)
    return img

def drawBoundingBox(img, entityList):
    for entity in entityList:
        lineThickness = 2
        x1 = round(entity['box'][0])
        x2 = round(entity['box'][2])
        y1 = round(entity['box'][1])
        y2 = round(entity['box'][3])

        if(entity['movement'] < 2):
            # Top
            cv2.line(img, (x1, y1), (x2, y1), (0, 0, 255), lineThickness)

            # Bottom
            cv2.line(img, (x1, y2), (x2, y2), (0, 0, 255), lineThickness)

            # Left
            cv2.line(img, (x1, y1), (x1, y2), (0, 0, 255), lineThickness)

            # Right
            cv2.line(img, (x2, y1), (x2, y2), (0, 0, 255), lineThickness)
        elif(entity['movement'] >= 2):
            # Top
            cv2.line(img, (x1, y1), (x2, y1), (128, 128, 128), lineThickness)

            # Bottom
            cv2.line(img, (x1, y2), (x2, y2), (128, 128, 128), lineThickness)

            # Left
            cv2.line(img, (x1, y1), (x1, y2), (128, 128, 128), lineThickness)

            # Right
            cv2.line(img, (x2, y1), (x2, y2), (128, 128, 128), lineThickness)
    return img


def scaleImage(imgOrigin, scale):
    w = scale
    height, width, depth = imgOrigin.shape
    imgScale = w/width
    newX, newY = imgOrigin.shape[1] * imgScale, imgOrigin.shape[0] * imgScale
    newImg = cv2.resize(imgOrigin, (int(newX), int(newY)))

    return newImg

def scaleImageNew(imgOrigin, sizeTuple):
    w = sizeTuple[0]
    h = sizeTuple[1]

    height, width, depth = imgOrigin.shape
    imgScaleX = w/width
    imgScaleY = h/height
    newX, newY = imgOrigin.shape[1] * imgScaleX, imgOrigin.shape[0] * imgScaleY
    newImg = cv2.resize(imgOrigin, (int(newX), int(newY)))

    return newImg


def convertImageForPIL(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(img)

    return img


def getImgLocList(imgPath):
    imgLocStore = []

    for loc in glob.glob(imgPath + '*.png'):
        imgLocStore.append(loc)

    return imgLocStore

def generateCountVideoFromFiles(jsonData, imgPath, videoName, lineY1, lineY2):
    img_array = []
    for filename in glob.glob(imgPath + '*.png'):
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)
    
    out = cv2.VideoWriter(videoName + '.avi', cv2.VideoWriter_fourcc(*'DIVX'), 15, size)
    
    for i in range(len(img_array)):
        out.write(img_array[i])

    out.release()

def generateRegionVideoFromFiles(jsonData, imgPath, videoName, coordTuple):
    img_array = []
    for filename in glob.glob(imgPath + '*.png'):
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)
    
    out = cv2.VideoWriter(videoName + '.avi', cv2.VideoWriter_fourcc(*'DIVX'), 15, size)
    
    for i in range(len(img_array)):
        out.write(img_array[i])

    out.release()
