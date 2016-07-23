# -*- coding: UTF-8 -*-
from numpy import *
from pytesseract import *
from os import listdir
import Image
import operator
import sys, os, re, math
#set default decoding way,when encoding
reload(sys)
sys.setdefaultencoding('utf-8')  

def cut_edge(im):
    '''
    切割验证码边缘无字符部分
    '''
    #从x轴开始遍历，切割左右边缘
    split_blank = ()
    data = list(im.getdata())
    w,h = im.size
    for x in range(w):
        if len(split_blank) == 0:
            for y in range(h):
                if data[ y*w + x ] < 50:
                    split_blank = split_blank + (x,0)
                    break
                else:
                    continue
        else:
            break
    for x in range(w)[::-1]:
        if len(split_blank) < 4:
            for y in range(h):
                if data[ y*w + x ] < 50:
                    split_blank = split_blank + (x+2,h-1)
                    break
                else:
                    continue
        else:
            break
    box = split_blank
    region = im.crop(box)
    #从y轴开始遍历，切割上下边缘
    split_blank = ()
    data = list(region.getdata())
    w,h = region.size
    for y in range(h):
        if len(split_blank) == 0:
            for x in range(w):
                if data[ y*w + x ] < 50:
                    split_blank = split_blank + (0,y)
                    break
                else:
                    continue
        else:
            break
    for y in range(h)[::-1]:
        if len(split_blank) < 4:
            for x in range(w):
                if data[ y*w + x ] < 50:
                    split_blank = split_blank + (w-1,y)
                    break
                else:
                    continue
        else:
            break
    box = split_blank
    region = region.crop(box)
    return region

def check(num,w,record):
    '''
    确认该位置是否是分割点
    '''
    #遍历点数列表，寻找数量为0的点并记录，如果在边缘则忽略
    #数量小于5则继续
    #遍历点数列表，寻找数量为1的点，记录，如果存在相邻点数相同的，则取较远的。如果在边缘则忽略
    #循环遍历直到数量等于5则停止
    if len(record) != 0:
        for i in record:
            if abs(num - i) > 20 and num > 19 and num < w-19:
                continue
            else:
                return False
    else:
        if num > 19 and num < w-19:
            return True
        else:
            return False
    return True

def cut_char(region):
    '''
    分割单个字符
    '''
    #将图片像素点投影到x轴，根据像素点分布确定每一个字符的边缘
    point_count = []
    data = list(region.getdata())
    w,h = region.size
    for x in range(w):
        point_num = 0
        for y in range(h):
            if data[ y*w + x ] < 50:
                point_num += 1
            else:
                continue
        point_count.append(point_num)
    record = []
    for point in range(0,15):
        if len(record) < 5:
            for i in range(len(point_count)):
                if point_count[i] == point:
                    if check(i,w,record):
                        record.append(i)
        else:
            break
    record.sort()
    return record

def getWide(im):
    '''
    返回字符的宽度
    '''
    lis = []
    data = list(im.getdata())
    w,h = im.size
    for y in range(h):
        for x in range(w):
            if data[ y*w + x ] < 50:
                lis.append(1)
            else:
                lis.append(255)
    im.putdata(lis)  
    im = im.point(lambda i: i * 4)
    data = list(im.getdata())
    widelist = []
    w,h = im.size
    for x in range(w):
        if len(widelist) == 0:
            for y in range(h):
                if data[ y*w + x ] < 50:
                    widelist.append(x)
                    break
                else:
                    continue
        else:
            break   
    for x in range(w)[::-1]:
        if len(widelist) < 2:
            for y in range(h):
                if data[ y*w + x ] < 50:
                    widelist.append(x)
                    break
                else:
                    continue
        else:
            break
    wide = widelist[1] - widelist[0]
    return wide

def rotate(im,angle = 1):
    '''
    旋转
    '''
    lis = []
    data = list(im.getdata())
    w,h = im.size
    for y in range(h):
        for x in range(w):
            if data[ y*w + x ] < 50:
                lis.append(1)
            else:
                lis.append(255)
    im.putdata(lis)     
    rotate = im.rotate(angle,expand = 1)
    #去除黑边
    w,h = rotate.size
    copy = Image.new('L',rotate.size)
    lis = []
    data = list(rotate.getdata())
    for y in range(h):
        use = 1
        for x in range(w):
            if use == 1:
                if data[ y*w + x ] == 0:
                    lis.append(255)
                else:
                    lis.append(data[ y*w + x ])
                    use = 0
            else:
                lis.append(data[ y*w + x ])

    copy.putdata(lis)
    data = list(copy.getdata())
    lis = []                
    for y in range(h):
        alis = []
        use = 1
        for x in range(w)[::-1]:
            if use == 1:
                if data[ y*w + x ] == 0:
                    alis.append(255)
                else:
                    alis.append(data[ y*w + x ])
                    use = 0
            else:
                alis.append(data[ y*w + x ])
        for it in alis[::-1]:
            lis.append(it)
    copy.putdata(lis)
    # copy.show()
    return copy

def rotateToMin(im):
    '''
    使用旋转卡壳进行判别，找出最小宽度,并标准化大小
    '''
    # print 'rotateToMin'
    # rotateIm = rotate(im)
    minIm = im
    oriWide = getWide(im)
    for i in range(1,100):
        rotateIm = rotate(im, angle = 5*i)
        rotateWide = getWide(rotateIm)
        if rotateWide > oriWide:
            break 
        if rotateWide < oriWide:
            minIm = rotateIm
            oriWide = rotateWide
    if oriWide < getWide(im):
        return tranTo30_40(minIm.point(lambda i: i * 4))
        # return minIm
    minIm = im
    oriWide = getWide(im)
    for i in range(1,100):
        rotateIm = rotate(im, angle = -5*i)
        rotateWide = getWide(rotateIm)
        if rotateWide > oriWide:
            break
        if rotateWide < oriWide:
            minIm = rotateIm
            oriWide = rotateWide
    return tranTo30_40(minIm.point(lambda i: i * 4))  
    # return minIm.point(lambda i: i * 4)

def char_to_string(record,region):
    '''
    字符识别
    '''
    w,h = region.size
    try:
        box = (0,0,record[0],h)
        char1 = rotateToMin(region.crop(box))
        changeToText(char1,'char1')
        char1.save('cache\\char1.jpg')
    except:
        return 'error'
        char1 =  None
    try:   
        box = (record[0],0,record[1],h)
        char2 = rotateToMin(region.crop(box))
        changeToText(char2,'char2')
        char2.save('cache\\char2.jpg')
    except:
        return 'error'
        char2 =  None
    try:        
        box = (record[1],0,record[2],h)
        char3 = rotateToMin(region.crop(box))
        changeToText(char3,'char3')
        char3.save('cache\\char3.jpg')
    except:
        return 'error'
        char3 =  None
    try:
        box = (record[2],0,record[3],h)
        char4 = rotateToMin(region.crop(box))
        changeToText(char4,'char4')
        char4.save('cache\\char4.jpg')
    except:
        return 'error'
        char4 =  None
    try:
        box = (record[3],0,record[4],h)
        char5 = rotateToMin(region.crop(box))
        changeToText(char5,'char5')
        char5.save('cache\\char5.jpg')
    except:
        return 'error'
        char5 =  None
    try:    
        box = (record[4],0,w,h)
        char6 = rotateToMin(region.crop(box))
        changeToText(char6,'char6')
        char6.save('cache\\char6.jpg')
    except:
        return 'error'
        char6 =  None
    str1 = charTest('char1')
    str2 = charTest('char2')
    str3 = charTest('char3')
    str4 = charTest('char4')
    str5 = charTest('char5')
    str6 = charTest('char6')
    string = str1+str2+str3+str4+str5+str6
    return string

def changeToText(im,strname):
    '''
    图片保存为txt文档
    '''
    testvaries = tranTo2(im)
    file = open('cache\\' + strname + '.txt','w')
    for j in range(40):
        for i in range(30):
            file.write(str(testvaries[j*30+i]))
        file.write('\n')
    file.close()

def tranTo30_40(im):
    '''
    图片标准化为30*40
    '''
    im = cut_edge(im)
    w,h = im.size
    data = list(im.getdata())
    copy = Image.new('L',(30,40))
    lis = []
    if w > 30 or h > 40:
        return None
    if w < 30:
        wbit = 30-w
    else:
        wbit = 0
    if h < 40:
        hbit = 40-h
    else:
        hbit = 0
    for y in range(hbit/2):
        for x in range(30):
            lis.append(255)
    for y in range(h):
        for x in range(wbit/2):
            lis.append(255)
        for x in range(w):
            lis.append(data[ y*w + x ])
        for x in range(wbit-wbit/2):
            lis.append(255)
    for y in range(hbit-hbit/2):
        for x in range(30):
            lis.append(255)   
    copy.putdata(lis)
    return copy

def tranTo2(im):
    '''
    二值化
    '''
    #30*40 = 1200 pix
    w,h = im.size
    data = list(im.getdata())
    count = 0
    varies = []
    for y in range(h):
        for x in range(w):
            if data[ y*w + x ] < 50:
                varies.append(1)
            else:
                varies.append(0)
    return varies

def vector(filename):
    '''
    txt向量化
    '''
    returnVect = zeros((1,1200))
    fr = open(filename)
    for i in range(40):
        lineStr = fr.readline()
        for j in range(30):
            returnVect[0,30*i+j] = int(lineStr[j])
    return returnVect

def classify0(inX, dataSet, labels, k):
    '''
    knn近邻算法，比对识别
    '''
    dataSetSize = dataSet.shape[0]
    diffMat = tile(inX, (dataSetSize,1)) - dataSet
    sqDiffMat = diffMat**2
    sqDistances = sqDiffMat.sum(axis=1)
    distances = sqDistances**0.5
    sortedDistIndicies = distances.argsort()     
    classCount={}          
    for i in range(k):
        voteIlabel = labels[sortedDistIndicies[i]]
        classCount[voteIlabel] = classCount.get(voteIlabel,0) + 1
    sortedClassCount = sorted(classCount.iteritems(), key=operator.itemgetter(1), reverse=True)
    return sortedClassCount[0][0]

def charTest(charname):
    '''
    识别入口函数，处理traindatatxt
    '''
    hwLabels = []
    traindatatext = listdir('traindatatext')           #load the training set
    m = len(traindatatext)
    trainingMat = zeros((m,1200))
    for i in range(m):
        fileNameStr = traindatatext[i]
        fileStr = fileNameStr.split('.')[0]     #take off .txt
        charNameStr = fileStr.split('_')[0]
        hwLabels.append(charNameStr)
        trainingMat[i,:] = vector('traindatatext/%s' % fileNameStr)
    vectorUnderTest = vector('cache\\' + charname + '.txt')
    Result = classify0(vectorUnderTest, trainingMat, hwLabels, 3)
    return Result

def main(image):
    '''
    main func
    '''
    #打开图像
    im = Image.open(image)
    #切除图像边缘
    region = cut_edge(im)
    #分割单个字符
    record = cut_char(region)
    #图像转换为文字
    string = char_to_string(record,region)
    return string

if __name__ == '__main__':
    for i in range(40):
        image = 'testimage\\'+str(i)+'.jpg'
        string = main(image)
        print string