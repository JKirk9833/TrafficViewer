import json
import glob
import math
import statistics

def getAllJsonFileLoc(jsonPath):
    jsonStore = []

    for loc in glob.glob(jsonPath + '*.json'):
        jsonStore.append(loc)

    return jsonStore


def getAllImgFileLoc(imgPath):
    imgStore = []

    for loc in glob.glob(imgPath + '*.png'):
        imgStore.append(loc)

    return imgStore


def getAllJsonFiles(jsonLocList):
    data = []

    for loc in jsonLocList:
        with open(loc) as jsonFile:
            data.append(json.load(jsonFile))

    return data


def getIndexOfImg(imgLocList, imgNum):
    for idx, loc in enumerate(imgLocList):
        if(imgNum in loc):
            return idx


def getEntitiesBetwixtX(jsonFileData, lineY):
    entityStore = []
    lineYVal = int(lineY)
    for entity in jsonFileData:
        if(entity['box'][1] <= lineYVal and entity['box'][3] >= lineYVal):
            entityStore.append(entity)

    return entityStore


def filterByClass(entityList, classDict):
    filteredList = []
    for entity in entityList:
        if(entity['class'] == 1 and classDict['bike'] == 1):
            filteredList.append(entity)
        elif(entity['class'] == 2 and classDict['car'] == 1):
            filteredList.append(entity)
        elif(entity['class'] == 3 and classDict['people'] == 1):
            filteredList.append(entity)

    return filteredList

def filterAllByClass(jsonData, classDict):
    filtList = []

    for jsonFileData in jsonData:
        filtList.append(filterByClass(jsonFileData, classDict))
    
    return filtList


def trimBadJsonEntities(jsonFileData, tolerance):
    entityStore = []

    for entity in jsonFileData:
        if(entity['score'] > tolerance):
            entityStore.append(entity)
        else:
            continue

    return entityStore


def trimAllBadJsonEntities(jsonData, tolerance):
    newJsonData = []
    for jsonFileData in jsonData:
        newJsonData.append(trimBadJsonEntities(jsonFileData, tolerance))

    return newJsonData


def assignEntityCentreCoord(jsonFileData):
    for entity in jsonFileData:
        xDiff = (entity['box'][2] - entity['box'][0]) / 2
        x = entity['box'][0] + xDiff

        yDiff = (entity['box'][3] - entity['box'][1]) / 2
        y = entity['box'][1] + yDiff

        entity['centre'] = [x, y]

    return jsonFileData


def assignJsonDataCentreCoord(jsonData):
    jsonStore = []
    for jsonFileData in jsonData:
        jsonStore.append(assignEntityCentreCoord(jsonFileData))

    return jsonStore


def assignOffLineStatusToAll(jsonData, lineY):
    for jsonFileData in jsonData:
        for entity in jsonFileData:
            entity['lineStatus'] = "offLine"
            entity['lineTravelled'] = 0

    return jsonData


def entityOnLineCheck(entity, lineY):
    if(lineY > entity['box'][1] and lineY < entity['box'][3]):
        return True
    else:
        return False


def assignOnLineStatus(jsonData, lineY):
    for jsonFileData in jsonData:
        for entity in jsonFileData:
            if entityOnLineCheck(entity, lineY):
                entity['lineStatus'] = "onLine"
            elif not entityOnLineCheck(entity, lineY):
                entity['lineStatus'] = "offLine"

    return jsonData


def gCE(prevJFD, jFD, dThreshold):
    entityFormat = {}
    entityFormat['nextEntity'] = 0
    entityFormat['distance'] = 0
    entityFormat['direction'] = 0
    entityFormat['prevEntity'] = 0

    entityList = []

    for pEntity in prevJFD:
        for nEntity in jFD:
            eDist = getDistanceBetweenEntities(pEntity, nEntity)
            entityFormat.clear()
            if(eDist['distance'] < dThreshold):
                entityFormat.update(nextEntity=nEntity['id'])
                entityFormat.update(distance=eDist['distance'])
                entityFormat.update(direction=eDist['direction'])
                entityFormat.update(prevEntity=pEntity['id'])

                entityList.append(entityFormat.copy())

    return entityList


def getDistanceBetweenEntities(entity1, entity2):
    distDirDict = {}
    distDirDict['direction'] = 0
    distDirDict['distance'] = 0

    directionY = entity1['centre'][1] - entity2['centre'][1]
    if(directionY >= 0):
        distDirDict.update(direction=1)
    elif(directionY < 0):
        distDirDict.update(direction=-1)

    x, y = abs(entity1['centre'][0] - entity2['centre'][0]
               ), abs(entity1['centre'][1] - entity2['centre'][1])
    x, y = x ** 2, y ** 2
    total = math.sqrt(x + y)
    distDirDict.update(distance=total)
    
    return distDirDict


def gCEJsonData(jsonData, dThreshold):
    prevJsonFileData = jsonData[0]
    dataStore = []

    for jsonFileData in jsonData[1:]:
        dataStore.append(gCE(prevJsonFileData, jsonFileData, dThreshold))
        prevJsonFileData = jsonFileData

    return dataStore


def assignDistanceToAll(jsonData):
    for jsonFileData in jsonData:
        for entity in jsonFileData:
            entity['distance'] = 0
            entity['direction'] = 0
            entity['lineStatus'] = 'None'
            entity['movement'] = 0
            entity['mLife'] = 3
            entity['camDist'] = 0
            entity['area'] = 0
    return jsonData

def getCamDist(jsonData):
    for jsonFileData in jsonData:
        for entity in jsonFileData:
            x, y = entity['centre'][0] ** 2, entity['centre'][1] ** 2
            total = math.sqrt(x + y)
            entity['camDist'] = total
    
    return jsonData


def assignPrevID(jsonFileData, entityList):
    for entity in jsonFileData:
        for eDict in entityList:
            if(entity['id'] == eDict['nextEntity']):
                entity['prevID'] = eDict['prevEntity']
                entity['distance'] = eDict['distance']
                entity['direction'] = eDict['direction']
                break
            else:
                entity['prevID'] = -1
                entity['distance'] = 0
                entity['direction'] = 0
                continue

    return jsonFileData


def idAssignmentJsonData(jsonData, cEntityList):
    newJsonData = []
    jd = jsonData[0]
    newJsonData.append(jd)
    for idx, jsonFileData in enumerate(jsonData[1:]):
        newJsonData.append(assignPrevID(jsonFileData, cEntityList[idx]))

    return newJsonData


def findPrevIDEntity(prevJsonFileData, prevID):
    for entity in prevJsonFileData:
        if(entity['id'] == prevID):
            return entity
            break
        else:
            continue

    return None


def modThreshold(entity, sThreshold):

    if(entity['class'] == 1):
        sThreshold *= 0.90
    elif(entity['class'] == 2):
        sThreshold *= 0.70
    elif(entity['class'] == 3):
        sThreshold *= 0.40

    return sThreshold


def identifyStationaryEntities(jsonData, sThreshold):
    prevJsonFileData = jsonData[0]

    for jsonFileData in jsonData[1:]:
        for entity in jsonFileData:

            if(entity['distance'] < modThreshold(entity, sThreshold)):
                eStore = findPrevIDEntity(prevJsonFileData, entity['prevID'])
                if not eStore == None:
                    if(eStore['distance'] < modThreshold(entity, sThreshold)):
                        entity['movement'] += eStore['movement'] + 1

                    elif(eStore['distance'] >= modThreshold(entity, sThreshold)):
                        entity['movement'] = eStore['movement'] - 1
                    else:
                        continue
                else:
                    entity['movement'] += 1

            elif(entity['distance'] >= modThreshold(entity, sThreshold)):
                eStore = findPrevIDEntity(prevJsonFileData, entity['prevID'])
                if not eStore == None:
                    entity['movement'] = eStore['movement'] - 1
                else:
                    continue

        prevJsonFileData = jsonFileData

    return jsonData

def checkKey(dict, key): 
    if key in dict.keys(): 
        return True
    else: 
        return False

def countEntities(jsonFileData):
    entityStruct = {}
    bike, car, person = 0, 0, 0
    entityStruct['bike'], entityStruct['car'], entityStruct['person'] = 0, 0, 0

    for entity in jsonFileData:
        if(checkKey(entity, 'lineStatus')):
            if(entity['lineStatus'] == "within"):
                if(entity['class'] == 1):
                    bike += 1
                elif(entity['class'] == 2):
                    car += 1
                elif(entity['class'] == 3):
                    person += 1
        else:
            continue

    entityStruct['bike'], entityStruct['car'], entityStruct['person'] = bike, car, person

    return entityStruct.copy()


def parseEntityStructList(entityStructList, classID):
    pEntity = 0

    prevVehicleCount = entityStructList[0]
    for vehicle in entityStructList[1:]:
        if(prevVehicleCount[classID] < vehicle[classID]):
            diff = vehicle[classID] - prevVehicleCount[classID]
            pEntity += diff
        else:
            continue

        prevVehicleCount = vehicle
    
    pEntity += prevVehicleCount[classID]
    return pEntity    


def countAllEntities(jsonData):
    entityStructList = []

    for jsonFileData in jsonData:
        entityStructList.append(countEntities(jsonFileData))

    return entityStructList


def getAverageSpeedOfVehicle(jsonData, classID, coordTuple):
    speedList = []
    vehicleFormat = {}
    vehicleFormat['classID'], vehicleFormat['minSpeed'], vehicleFormat['maxSpeed'], vehicleFormat['avgSpeed'] = classID, -1, -1, -1

    for jsonFileData in jsonData:
        for entity in jsonFileData:
            if(entity['class'] == classID and regionWithinCheck(entity, coordTuple) and entity['distance'] > 0):
                speedList.append(abs(entity['distance']))

    if not len(speedList) == 0:
        vehicleFormat['minSpeed'] = min(speedList)
        vehicleFormat['maxSpeed'] = max(speedList)
        vehicleFormat['avgSpeed'] = statistics.mean(speedList)
        return vehicleFormat.copy()
    else:
        vehicleFormat['minSpeed'] = 0
        vehicleFormat['maxSpeed'] = 0
        vehicleFormat['avgSpeed'] = 0
        return vehicleFormat.copy()

def getAverageSpeedOfSingleVehicleList(jsonFileData, classID, coordTuple):
    speedList = []
    vehicleFormat = {}
    vehicleFormat['classID'], vehicleFormat['minSpeed'], vehicleFormat['maxSpeed'], vehicleFormat['avgSpeed'] = classID, -1, -1, -1
    for entity in jsonFileData:
        if(checkKey(entity, 'centre') == True):
            if(entity['class'] == classID and regionWithinCheck(entity, coordTuple) and entity['distance'] > 0):
                speedList.append(abs(entity['distance']))
            else:
                continue
        else:
            continue

    if not len(speedList) == 0:
        vehicleFormat['minSpeed'] = min(speedList)
        vehicleFormat['maxSpeed'] = max(speedList)
        vehicleFormat['avgSpeed'] = statistics.mean(speedList)
        return vehicleFormat.copy()
    else:
        vehicleFormat['minSpeed'] = 0
        vehicleFormat['maxSpeed'] = 0
        vehicleFormat['avgSpeed'] = 0
        return vehicleFormat.copy()

def assignLineStatus(jsonData, lineY1, lineY2):
    for jsonFileData in jsonData:
        assignLine(jsonFileData, lineY1, lineY2)
    
    return jsonData

def assignLine(jsonFileData, lineY1, lineY2):
    for entity in jsonFileData:
        entity['lineStatus'] = lineCheck(entity, lineY1, lineY2)

def lineCheck(entity, lineY1, lineY2):
    if entity['centre'][1] > lineY1 and entity['centre'][1] > lineY2:
        return 'after'
    elif entity['centre'][1] < lineY1 and entity['centre'][1] > lineY2:
        return 'within'
    elif entity['centre'][1] < lineY1 and entity['centre'][1] < lineY2:
        return 'before'
    elif entity['centre'][1] > lineY1 and entity['centre'][1] < lineY2:
        return 'within'
    else:
        return 'Check lineCheck() in jsonFunctions because it clearly isnt working'

def returnEntitiesBetweenLines(jsonData):
    largeEntityStore = []
    for jsonFileData in jsonData:
        largeEntityStore.append(getEntitiesWithinLines(jsonFileData, lineY1, lineY2))
    
    return largeEntityStore

def getEntitiesWithinLines(jsonFileData):
    entityStore = []
    for entity in jsonFileData:
        if(entity['lineStatus'] == 'within'):
            entityStore.append(entity)
    
    return entityStore

def returnListOfEntitiesWithin(jsonData):
    entityCount = []

    for jsonFileData in jsonData:
        entityCount.append(listOfEntitiesForCount(jsonFileData))
    
    return entityCount

def getAllEntitiesWithinBox(jsonData, coordTuple):
    entityList = []
    for jsonFileData in jsonData:
        entityList.append(getEntitiesWithinBox(jsonFileData, coordTuple))
    
    return entityList

def getEntitiesWithinBox(jsonFileData, coordTuple):
    entityStore = []
    for entity in jsonFileData:
        if regionWithinCheck(entity, coordTuple) == True:
            entityStore.append(entity)
        else:
            continue
    
    return entityStore

def regionWithinCheck(entity, coordTuple):
    # Within X points? [0] and [1] x1/x2 respectively | Within Y points?
    if entity['centre'][0] > coordTuple[0] and entity['centre'][0] < coordTuple[1]:
        if entity['centre'][1] > coordTuple[2] and entity['centre'][1] < coordTuple[3]:
            return True
        else:
            return False
    else:
        return False

def listOfEntitiesForCount(jsonFileData):
    entityCountDict = {}
    entityCountDict['bike'] = 0
    entityCountDict['car'] = 0
    entityCountDict['people'] = 0

    for entity in jsonFileData:
        if(entity['lineStatus'] == 'within'):
            if(entity['class'] == 1):
                entityCountDict['bike'] += 1
            elif(entity['class'] == 2):
                entityCountDict['car'] += 1
            elif(entity['class'] == 3):
                entityCountDict['people'] += 1
    
    return entityCountDict

def getAreaOfEntity(entity):
    x = entity['box'][3] - entity['box'][1]
    y = entity['box'][2] - entity['box'][0]
    return x * y

def setAreaOfEntity(jsonData):
    data = []

    def setAreaOfEntityJFD(jsonFileData):
        entityStore = []

        for entity in jsonFileData:
            entity['area'] = getAreaOfEntity(entity)
            entityStore.append(entity)
        
        return entityStore

    for jsonFileData in jsonData:
        data.append(setAreaOfEntityJFD(jsonFileData))
    
    return data

def findBoundingBoxArea(coordTuple):
    x = coordTuple[1] - coordTuple[0]
    y = coordTuple[3] - coordTuple[2]
    return x * y

def getAreaTakenList(areaJsonData, boundingBoxArea):
    areaTotal = boundingBoxArea
    scoreList = []

    for jsonFileData in areaJsonData:
        for entity in jsonFileData:
            areaTotal -= entity['area']
        score = (areaTotal / boundingBoxArea) * 100
        score = 100 - score
        scoreList.append(score)
        areaTotal = boundingBoxArea
    
    return scoreList
        

def refineAndPrepareJsonData(jsonData, lineY1, lineY2, tolerance, dThreshold, sThreshold):
    # The number is a tolerance for score (gets rid of the random flashes of bikes becoming cars and children becoming cars)
    jsonData = trimAllBadJsonEntities(jsonData, tolerance)

    # Assigns the centre of an entity as a dict value
    jsonData = assignJsonDataCentreCoord(jsonData)

    # Distance from camera assign
    jsonData = getCamDist(jsonData)

    # Assigns all entities all required labels such as distance, movement and mLife for checking whether things are still or not
    jsonData = assignDistanceToAll(jsonData)

    # Goes through every json file and compares each entity to another
    # Uses this data to assign the closest entity for each
    cEntityList = gCEJsonData(jsonData, dThreshold)

    # Uses the previous data to assign semi-accurate id's allowing for tracking entities
    jsonData = idAssignmentJsonData(jsonData, cEntityList)

    # Within Line Status Assign
    jsonData = assignLineStatus(jsonData, lineY1, lineY2)

    # Area finder
    jsonData = setAreaOfEntity(jsonData)

    # Assigns all entities that do not move as stationary
    jsonData = identifyStationaryEntities(jsonData, sThreshold)

    return jsonData

def refineAndPrepareJsonDataRegion(jsonData, tolerance, dThreshold, sThreshold):
    # The number is a tolerance for score (gets rid of the random flashes of bikes becoming cars and children becoming cars)
    jsonData = trimAllBadJsonEntities(jsonData, tolerance)

    # Assigns the centre of an entity as a dict value
    jsonData = assignJsonDataCentreCoord(jsonData)

    # Distance from camera assign
    jsonData = getCamDist(jsonData)

    # Assigns all entities all required labels such as distance, movement and mLife for checking whether things are still or not
    jsonData = assignDistanceToAll(jsonData)

    # Goes through every json file and compares each entity to another
    # Uses this data to assign the closest entity for each
    cEntityList = gCEJsonData(jsonData, dThreshold)

    # Uses the previous data to assign semi-accurate id's allowing for tracking entities
    jsonData = idAssignmentJsonData(jsonData, cEntityList)

    # Area finder
    jsonData = setAreaOfEntity(jsonData)

    # Assigns all entities that do not move as stationary
    jsonData = identifyStationaryEntities(jsonData, sThreshold)

    return jsonData
