from genericpath import isdir
from operator import length_hint
import pydicom
import matplotlib.pyplot as plt
import re
import os

rootPath = "/Users/fiona/Desktop/MRA"
desPath = "/Users/fiona/Desktop/MRADesFile"
# 原输入可以认为根路径+隐私路径+非隐私路径（中间有单个病人）
# 输出的肯定是一个设定好的终极文件夹/病人的姓名

index = 0
patientRootIndex = 2 #单个病人文件夹的根目录序号
notPrivacyRootIndex = 2 #不含隐私信息的文件夹根部序号，想保留下来的文件夹路径的起始点序号
DICOMIndex = 3#DICOM文件属于的文件夹序号


insideFolderPath = ''
nameFolder = ''

# ---------------------------------haylee的分界线 工具类------------------------------------------
def mkdir(folderPath):
    
    isExist = os.path.exists(folderPath)

    if not isExist:
        os.makedirs(folderPath)

def getSafeListDir(currentFolder):
    return [name for name in os.listdir(currentFolder) if not name.startswith('.')]

def getSafeDICOMList(currentPath):
    imageList = getSafeListDir(currentPath)
    # dsArr = [pydicom.read_file(currentPath + '/' + name) for name in imageList]
    dsArr = []
    for name in range(0, len(imageList)):
        if ".dcm" not in imageList[name].lower():
            continue
        tempPath = currentPath + '/' + imageList[name]
        dsArr.append(pydicom.read_file(tempPath))
    dsArrLength = len(dsArr)
    return dsArr, dsArrLength

def isPatientNameExist(ds):
    return hasattr(ds, "PatientName") and len(ds.PatientName) !=0

def isFamilyNameExist(ds):
    return hasattr(ds.PatientName, "family_name") and len(ds.PatientName.family_name) !=0

def isGivenNameExist(ds):
    return hasattr(ds.PatientName, "given_name") and len(ds.PatientName.given_name) !=0

def isStudyDateExist(ds):
    return hasattr(ds, "StudyDate") and len(ds.StudyDate) != 0

def isStudyTimeExist(ds):
    return hasattr(ds, "StudyTime") and len(ds.StudyTime) != 0

def getSafePatientName(ds):
    return ds.PatientName if isPatientNameExist(ds) else 'notHavePatientName'

def getSafeStudyDate(ds):
    return ds.StudyDate if isStudyDateExist(ds) else '000'

def getSafeStudyTime(ds):
    return ds.StudyTime if isStudyTimeExist(ds) else '000'

# 选取一个文件夹里的dcm文件路径
def getSubFileOnePath(path):
    subPath = 'Nothing'
    for root, subFolderName, File in os.walk(path, topdown=True):
        for fileName in File:
            if os.path.splitext(fileName)[1] == '.dcm':
                subPath = os.path.join(root, fileName)
                break
    # if(subPath == 'Nothing'): print("haylee look at me")
    return subPath
# ---------------------------------haylee的分界线 特殊工具类------------------------------------------

# 获取安全的名字缩写
def getSafeAbbreviation(ds):
    abbreviation = 'notHavePatientName'
    if isPatientNameExist(ds):
        abbreviation = 'notfit' + str(ds.PatientName) + 'code'
        
        if isFamilyNameExist(ds) and isGivenNameExist(ds):
            familyName = str(ds.PatientName.family_name)
            givenName = str(ds.PatientName.given_name)
            
            spaceLetterArr = re.findall(r'\s\w',givenName)
            secondLetter = 'x'
            if spaceLetterArr:
                tempSplitLetter = re.split(' ',spaceLetterArr[0])
                secondLetter = tempSplitLetter[1]
            
            abbreviation = 'HRMRI_' + familyName[0] + givenName[0] + secondLetter
    return abbreviation

def isNewNameOrNot(ds):
    patientN = getSafePatientName(ds)

    desPathNameList = getSafeListDir(desPath)
    for name in desPathNameList:
        namePath = desPath + '/' + name
        nameFilePath = getSubFileOnePath(namePath)
        if nameFilePath == 'Nothing':
            continue
        dsFind = pydicom.read_file(nameFilePath)
        patientFindN = getSafePatientName(dsFind)
        if str(patientFindN) == str(patientN):
            return False, name
    return True, ''

def getNewNameFolderName(ds):
    abbreviation = getSafeAbbreviation(ds)
    i = 0
    expectPath = desPath + '/' + abbreviation + '_' + str(i)
    while(os.path.exists(expectPath)):
        i += 1
        expectPath = desPath + '/' + abbreviation + '_' + str(i)
    return abbreviation + '_' + str(i)


def getNameFolderString(currentPath):
    nameFolderString = ''
    # 源文件请在rootpath后面就是名字文件夹，这个结构改了，这里会出错
    ds = pydicom.read_file(getSubFileOnePath(currentPath))

    isNewName, nameFolderString = isNewNameOrNot(ds)
    
    if isNewName:
        nameFolderString = getNewNameFolderName(ds)

    return nameFolderString
        
    

def getNextFolder(currentPath):
    global index
    index += 1
    currentFolderList = getSafeListDir(currentPath)
    currentFolderLength = len(currentFolderList)
    
    for k in range(0, currentFolderLength):
        nextPath = currentPath + '/' + currentFolderList[k]
        
        if index > notPrivacyRootIndex :
            global insideFolderPath
            insideFolderPath = currentFolderList[k]#TO do 这里要思考下用数组存了
        if index == patientRootIndex:#nextpath是一个病人的文件夹
            global nameFolder
            nameFolder = getNameFolderString(nextPath)

        if index < DICOMIndex:
            getNextFolder(nextPath)
            index -= 1
        else:
            changeDICOM(nextPath)

        
def changeDICOM(currentPath):
    dsArr, dsArrLength = getSafeDICOMList(currentPath)

    for e in range(0, dsArrLength):
        abbreviation = getSafeAbbreviation(dsArr[e])
        dsArr[e].PatientName = abbreviation
        dsArr[e].PatientID = '0'

        global insideFolderPath
        studyDate = getSafeStudyDate(dsArr[e])
        studyTime = getSafeStudyTime(dsArr[e])
        
        finalPath = desPath + '/' + nameFolder + '/' + studyDate + '_' + studyTime + '/' + insideFolderPath
        mkdir(finalPath)
        dsArr[e].save_as(finalPath + '/' + str(e) + '.dcm')

mkdir(desPath)
getNextFolder(rootPath)