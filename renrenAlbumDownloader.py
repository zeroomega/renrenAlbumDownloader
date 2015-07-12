#!/usr/bin/env python
# coding=<utf-8>
import urllib2, urllib
from HTMLParser import HTMLParser
from cookielib import CookieJar
import sys
import time
import os
import re
import json


username=""
password=""
UA="Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"
Cookie = ""
cj = CookieJar()
opener = None
regEx = "\\(第\d+/\d+张\\)"
fDebug = False
configFileName = 'configs.json'

# class MyHTMLParser(HTMLParser):
#     def handle_starttag(self, tag, attrs):
#         print "Encountered a start tag:", tag
#     def handle_endtag(self, tag):
#         print "Encountered an end tag :", tag
#     def handle_data(self, data):
#         print "Encountered some data  :", data

class albumItem():
    def __init__(self, albumName, albumHref):
        self.Name = albumName
        self.trimName()
        self.Href = albumHref
        self.dirPath = ""
        self.opener = None

    def trimName(self):
        index = len(self.Name) - 1
        while index >= 0:
            if self.Name[index] == '(':
                break
                pass
            index -= 1
            pass
        if index > 0:
            self.Name = self.Name[:index]
            pass

    def createDir(self):
        self.dirPath = os.path.abspath('./' + self.Name)
        if not os.path.exists(self.dirPath):
            os.mkdir(self.dirPath)
        pass

    def getFirstURL(self):
        req = urllib2.Request(self.Href)
        req.add_header("User-Agent", UA)
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        ret = opener.open(req)
        pageS = ret.read()
        ret.close()
        divIndex = pageS.find('<div class="list')
        divList = pageS[divIndex:]
        pParser = photoListParser()
        pParser.feed(divList)
        return pParser.href

    def saveLinktoDisk(self, urlLink, fileName):
        print("Saving " + fileName)
        req = urllib2.Request(urlLink)
        req.add_header("User-Agent", UA)
        ret = self.opener.open(req)
        time.sleep(1)
        lcFile = open(self.dirPath + "/" + fileName, "wb")
        lcFile.write(ret.read())
        lcFile.close()
        ret.close()

    def saveToDisk(self):
        self.createDir()
        firstPhotoLink = self.getFirstURL()
        
        if fDebug:
            print("Link to First Photo: " + firstPhotoLink)
            pass
        # try:
        #     input("Press Enter to continue")

        # except:
        #     #Do nothing
        #     pass

        nextPage = firstPhotoLink
        while len(nextPage) != 0:
            req = urllib2.Request(nextPage)
            req.add_header("User-Agent", UA)
            ret = self.opener.open(req)
            pageS = ret.read()
            ret.close()
            p = re.compile(regEx)
            b = p.search(pageS)
            
            curNum = ""
            totalNum = ""
            tempNum = ""
            if b == None:
                #Album empty or only have 1 photo
                curNum = "1"
                totalNum = "1"
            else:
                match = b.group()
                #Album has multiple photos                
                for index in range(len(match)):
                    curChar = match[index]
                    if curChar >= '0' and curChar <= '9':
                        tempNum += curChar
                    if curChar == '/':
                        curNum = tempNum
                        tempNum = ""
                totalNum = tempNum
            fileName = curNum + '.jpg'
            hrefP = hrefParser()
            hrefP.feed(pageS)
            if '下载' not in hrefP.dict:
                print("Warning: Album " + self.Name + " is empty!")
                return
            downloadLink = hrefP.dict['下载']
            if curNum == totalNum:
                nextPage = ""
            else:
                if '下一张' not in hrefP.dict:
                    return
                nextPage = hrefP.dict['下一张']

            if fDebug:
                print("Current Num: ", curNum)
                print("Total Num: ",totalNum )
            # try:
            #     input("Press Enter to continue")
            # except:
            #     pass

            self.saveLinktoDisk(downloadLink, fileName)
            pass
        pass

    def __str__(self):
        curLine = "{0} : {1}".format(self.Name, self.Href)
        return curLine

class photoListParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack=[]
        self.albumList = []
        self.do = True
        self.stackAttrs=[]
        self.href = ""
        pass
    def handle_starttag(self, tag, attrs):
        if (self.do):
            self.stack.append(tag)
            self.stackAttrs.append((tag, attrs))
            if tag == 'img' and 'td' in self.stack:
                attrsD = {}
                (curTag, curAttrs) = self.stackAttrs[-2]
                for (name, value) in curAttrs:
                    attrsD[name] = value
                    pass
                if curTag == 'a':
                    self.href = attrsD['href']
                    self.do = False
                pass
            pass
        pass
    def handle_data(self, data):
        pass
    def handle_endtag(self, tag):
        if not self.do:
            return
        if len(self.stack) == 0:
            self.do = False
            return
        curTag = self.stack.pop()
        (curTag, curAttrs) = self.stackAttrs.pop()
        if (curTag != tag) and fDebug:
            print("ERROR Stack not balanced ", curTag, tag)
        if (len(self.stack) == 0):
            self.do = False
        pass


class albumListParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack=[]
        self.albumList = []
        self.do = True
        self.stackAttrs=[]
        self.nextPage=""
        pass
    def handle_starttag(self, tag, attrs):
        if (self.do):
            self.stack.append(tag)
            self.stackAttrs.append((tag, attrs))
            if tag == 'a' and 'td' not in self.stack:
                attrsD = {}
                for (name, value) in attrs:
                    attrsD[name] = value
                    pass

                if 'title' in attrsD and attrsD['title'] == '下一页':
                    self.nextPage = attrsD['href']
                    pass

                pass
            pass
        pass
    def handle_data(self, data):
        if (not self.do):
            return
        curTag = self.stack[-1]
        if curTag == 'a' and 'td' in self.stack:
            #HREF
            (curTag, curAttrs) = self.stackAttrs[-1]
            attrsD = {}
            for (name, value) in curAttrs:
                attrsD[name] = value
                pass
            abHref = attrsD['href']
            abName = data
            abItem = albumItem(abName, abHref)
            self.albumList.append(abItem)

        pass
    def handle_endtag(self, tag):
        if not self.do:
            return
        if len(self.stack) == 0:
            self.do = False
            return
        curTag = self.stack.pop()
        (curTag, curAttrs) = self.stackAttrs.pop()
        if (curTag != tag and fDebug):
            print("ERROR Stack not balanced ", curTag, tag)
        if (len(self.stack) == 0):
            self.do = False
        pass

class hrefParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.dict = {}
        self.stack = []
        self.tempHref = ""

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        attrsD = {}
        if tag == 'a':
            for (name, value) in attrs:
                attrsD[name] = value
            pass
            if 'href' in attrsD:
                self.tempHref = attrsD['href']
        pass

    def handle_data(self, data):
        curTag = self.stack[-1]
        if (curTag == 'a'):
            self.dict[data] = self.tempHref
        pass


    def handle_endtag(self, tag):
        topTag = ""
        if len(self.stack) != 0:
            topTag = self.stack.pop()
        if (topTag != tag and fDebug):
            print("ERROR: Stack not balanced ", topTag, tag)
        pass



class formParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        #print(attrs)
        attrsD = {}
        for (name, value) in attrs:
            attrsD[name] = value

        #print(attrsD)
        if 'name' in attrsD and tag == 'input':
            curName = attrsD['name']
            #print(curName)
            curVal = ""
            if ('value' in attrsD):
                curVal = attrsD['value']
            #print(curVal)
            self.dict[curName] = curVal

        if tag == 'form':
            if ('action' in attrsD):
                self.post = attrsD['action']
        pass

    def handle_endtag(self, tag):
        topTag = self.stack.pop()
        if (topTag != tag and fDebug):
            print("ERROR: Stack not balanced ", topTag, tag)
        pass
    def handle_data(self, data):
        #print(data)
        pass
    def __init__(self):
        #super(formParser, self).__init__()
        HTMLParser.__init__(self)
        self.dict = {}
        self.stack = []
        self.post=""
        pass

def accessHomePage():
    global Cookie
    global opener
    hpUrl = "http://3g.renren.com/"
    req = urllib2.Request(hpUrl)
    req.add_header("User-Agent", UA)
    time.sleep(5)
    ret = urllib2.urlopen(req)
    pageS = ret.read()
    pageInfo = ret.info()
    formIndexb = pageS.find('<form')
    formIndexe = pageS.find('/form>')
    formS = pageS[formIndexb:formIndexe+6]

    ret.close()
    formP = formParser();
    formP.feed(formS)

    formP.dict['email'] = username
    formP.dict['password'] = password

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    data = urllib.urlencode(formP.dict)
    reqLogin = urllib2.Request(formP.post, data)
    reqLogin.add_header("User-Agent", UA)
    time.sleep(5)
    ret = opener.open(reqLogin)
    pageS = ret.read()
    ret.close()
    hParse = hrefParser()
    hParse.feed(pageS)
    #print(hParse.dict)
    if "个人主页" in hParse.dict:
        return (hParse.dict['个人主页'])

def accessAlbum(hpLink):
    global opener
    req = urllib2.Request(hpLink)
    req.add_header("User-Agent", UA)
    time.sleep(5)
    ret = opener.open(req)
    pageS = ret.read()
    #print(pageS)
    hParser = hrefParser()
    hParser.feed(pageS)
    abLink = ""
    if '相册' in hParser.dict:
        abLink = hParser.dict['相册']
    ret.close()
    if abLink == "":
        print("ERROR: Album link is empty")
        sys.exit(0)

    nextLink = abLink
    albumItemList = []
    print("Acquiring album list")
    while len(nextLink) != 0 :
        if fDebug:
            print("Accessing", nextLink)
        req = urllib2.Request(nextLink)
        req.add_header("User-Agent", UA)
        time.sleep(2)
        ret = opener.open(req)
        pageS = ret.read();
        ret.close()
        #print(pageS)
        listIndex = pageS.find('<div class="list"')
        albumDiv = ""
        if (listIndex != 0):
            albumDiv = pageS[listIndex:]

        #print(albumDiv)
        abParser = albumListParser()
        abParser.feed(albumDiv)
        albumItemList.extend(abParser.albumList)
        nextLink = abParser.nextPage
        pass

    print("Available Albums: ")
    for item in albumItemList:
        print(item.Name)
        pass

    for item in albumItemList:
        print("Accessing album " + item.Name)
        item.saveToDisk()
        pass
    pass

def loadConfigs():
    global username
    global password
    try:
        inFile = open(configFileName, 'r')
    except:
        print("ERROR: configs.json failed to open.")
        sys.exit(-1)

    jsonData = json.load(inFile)
    for key in jsonData:
        if key == 'username':
            username = jsonData[key]
        if key == 'password':
            password = jsonData[key]
    inFile.close()
    # if fDebug:
    #     print("User Name: ", username)
    #     print("Password:  ", password)


def main():
    global configFileName
    global fDebug
    params = sys.argv
    if len(params) > 1:
        for index in range(1, len(params)):
            curParam = params[index]
            if curParam[0] != '-':
                continue
            for cIndex in range(1, len(curParam)):
                curChar = curParam[cIndex]
                if curChar == 'd':
                    fDebug = True
                    pass
                if curChar == 'a':
                    configFileName = 'configsD.json'
                    pass
                pass
            pass
        pass
    loadConfigs()
    print("Do Login")
    hpLink = accessHomePage()
    accessAlbum(hpLink)
    pass

if __name__ == '__main__':
    main()