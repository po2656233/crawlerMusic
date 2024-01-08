# This Python file uses the following encoding: utf-8

import os
import re
import sys
import requests
import urllib

from bs4 import BeautifulSoup
from selenium import webdriver
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QLineEdit, QLabel
from PySide2.QtCore import QFile, QThread, Signal
from PySide2.QtUiTools import QUiLoader
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import time
import asyncio

headers = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    }

params = {
        'authority': 'www.kugou.com',
        'method': 'GET',
        'path': '/mixsong/1hiccibc.html',
        'scheme': 'https'
    }


## mp3filePath是否是mp3格式的
#def removeFailMp3():
#    # 读取文件内字符串
#    for filepath, dirnames, filenames in os.walk(r'./mp3'):
#        for filename in filenames:
#            filename = os.path.join(filepath, filename)
#            stats = os.stat(filename)
#            if stats.st_size == int(101831) or stats.st_size == 0:
#                os.remove(filename)
#                return False
#    return True


# 检测并删除非mp3格式的文件
def checkMp3File(fileStr):
    mp3Size = len(fileStr)
    print("开始检测 ", mp3Size)
    if mp3Size == int(101831) or mp3Size == 0:
        return False
    return True
#    if len(fileStr) < 35:
#        return False
#    head3Str = fileStr[:3]
#    # 判断开头是不是ID3
#    if head3Str == "ID3":
#        return True
#    # 判断结尾有没有TAG
#    last32Str = fileStr[-32:]
#    if last32Str[:3] == "TAG":
#        return True
#    # 判断第一帧是不是FFF开头, 转成数字
#    # fixme 应该循环遍历每个帧头，这样才能100%判断是不是mp3
#    ascii = ord(fileStr[:1])
#    if ascii == 255:
#        return True
#    return False


def getDataUrl(url):
    with requests.get(url, headers=headers) as response:
        if response.status_code == 200:
            return response
        else:
            return None

def postDataUrl(url, param):
    with requests.post(url, json=param, headers=headers) as response:
        print(response)
        return response

class Widget(QWidget):
    def __init__(self):
        super(Widget, self).__init__()
        # self.MyTimer = QTimer()
        self.index = 0
        self.songs_list = []
        self.songs_fin = []
        self.songs_exist = []
        self.load_ui()
        self.work = Thread()
        self.label = self.findChild(QLabel, "label")
        self.searchBtn = self.findChild(QPushButton, "pushButton_search")
        self.crawlerBtn = self.findChild(QPushButton, "pushButton_crawler")
        self.openMp3DirBtn = self.findChild(QPushButton, "pushButton_mp3dir")
        self.stopWgBtn = self.findChild(QPushButton, "pushButton_close")
        self.textEdit = self.findChild(QTextEdit, "textEdit")
        self.lineEditSong = self.findChild(QLineEdit, "lineEdit_song")
        self.lineEditIndexs = self.findChild(QLineEdit, "lineEdit_index")
        # self.crawler.clicked.connect(self.get_rankList)
        self.searchBtn.clicked.connect(self.startSearh)
        self.lineEditSong.returnPressed.connect(self.startSearh)
        self.crawlerBtn.clicked.connect(self.startCrawler)
        self.lineEditIndexs.returnPressed.connect(self.startCrawler)
        self.stopWgBtn.clicked.connect(self.onClose)
        self.openMp3DirBtn.clicked.connect(self.openMp3Dir)
        self.work.finished.connect(self.finish)
        self.work.needer.sigDownload.connect(self.showInfo)
        self.work.needer.sigDownload.connect(self.showInfo)
        self.work.needer.sigFinal.connect(self.addFinal)
        self.work.needer.sigExist.connect(self.addExist)
        self.work.needer.sigFail.connect(self.addInfo)

#     # 酷狗排行榜
#     def get_rankList(self):
#         self.index += 1
#         self.showInfo("第"+str(self.index)+"次,获取歌曲地址")
#         host = "https://www.kugou.com/yy/rank/home/"
#         url = host+"{}-8888.html".format(self.index)
#         web_data = getDataUrl(url)
#         soup = BeautifulSoup(web_data.text, 'lxml')
#         ranks = soup.select('span.pc_temp_num')
#         titles = soup.select('div.pc_temp_songlist > ul > li > a')
#         times = soup.select('span.pc_temp_tips_r > span')
#         for rank, title, time1 in zip(ranks, titles, times):
#             data = {
#                 "rank": rank.get_text().strip(),
#                 "singer": title.get_text().replace("\n", "").replace("\t", "").split('-')[1],
#                 "song": title.get_text().replace("\n", "").replace("\t", "").split('-')[0],
#                 "time": time1.get_text().strip(),
#                 "url": title.get('href')
#             }
#             print("tile", title.get('href'))
#             strData = str(data)
#             self.textEdit.append(strData)
#             # 获取歌曲
#             songs_url = title.get('href')
#             if songs_url != '':
#                 self.songs_list.append(data["singer"]+'|'+data["song"]+'|'+songs_url)
#         # 启动任务
#         if self.index == 23:
#             print("启动任务,获取歌曲地址")
#             self.showInfo("启动任务,获取歌曲地址")
# #            self.MyTimer.stop()
#             self.textEdit.append("\n\n正在下载歌曲...请勿关闭")
#             self.work.init_songs(self.songs_list)
#             # self.work.quit()
#             # self.work.wait()
#             self.work.start()

    # 查找歌曲 网易云歌曲下载
    def startSearh(self):
        if not self.searchBtn.isEnabled() :
            return
        songname = self.lineEditSong.text()
        if songname == "":
            self.textEdit.clear()
            self.textEdit.append("\n查询内容不能为空")
            return
        url = "http://music.163.com/api/search/get/web?type=1&offset=0&total=true&limit=100&s=" + songname;
        r = getDataUrl(url)
        webdata = r.json()
        if len(webdata) == 0:
            return
        try:
            webdata["result"]
        except KeyError:
            return
        self.songs_list.clear()
        self.textEdit.clear()
        self.textEdit.append("\n歌曲列表如下:")
        idx = 0
        for info in webdata["result"]["songs"]:
            url = "http://music.163.com/song/media/outer/url?id={}.mp3".format(info["id"])
            idx += 1
            self.songs_list.append(info["artists"][0]["name"]+'|'+info["name"]+'|'+url)
            self.textEdit.append("\n第{}首歌曲:".format(idx)+info["name"]+ " 歌手:"+info["artists"][0]["name"]+" 下载地址:"+url)
        self.textEdit.append("\n共{}首歌曲".format(len(self.songs_list)))

# 开始爬取歌曲
    def startCrawler(self):
        if not self.searchBtn.isEnabled() :
            return
        strIndexs = self.lineEditIndexs.text()
        indexs = []
        # 获取前几首
        if 3 < len(strIndexs) and strIndexs[0] == '[' and strIndexs[-1] == ']':
            numbers = re.findall(r'\d+', strIndexs)
            if strIndexs.find(":"):
                numbers = [int(n) for n in numbers]  # 转换为整数
                min = -1
                max = -1
                print(strIndexs, '当前数值0', numbers)
                if 1 < len(numbers):
                    min = numbers[0]
                    max = numbers[1]
                elif strIndexs[1] == ':':
                    max = numbers[0]
                else:
                    min = numbers[0]
                    max = numbers[0]
                for i in range(0, len(self.songs_list)):
                    if min <= i+1 and i+1 <= max:
                        indexs.append(str(i))
            else:
                indexs = numbers
        if 0 == len(indexs):
            if strIndexs.find("，"):
                indexs = strIndexs.split('，')
            elif len(indexs) <= 1:
                indexs = strIndexs.split(',')
        print(len(indexs), '当前数值', indexs, len(strIndexs))
        if 0 < len(strIndexs) and not indexs[0].isdigit():
            self.showInfo("索引不符合规则,请重新填写")
            return
        songslist = []
        for i in range(0, len(self.songs_list)):
            if str(i+1) in indexs or 0 == len(strIndexs):
                songslist.append(self.songs_list[i])
        if 0 == len(songslist):
            self.showInfo("没有可爬取的资源")
            return
        self.songs_fin = []
        self.songs_exist = []
        self.showInfo("启动任务,获取歌曲地址")
        self.searchBtn.setEnabled(False)
        self.crawlerBtn.setEnabled(False)
#        self.MyTimer.stop()
        self.textEdit.append("\n正在下载歌曲...请勿关闭")
        self.work.init_songs(songslist)
        self.work.quit()
        self.work.wait()
        self.work.start()

    def showInfo(self, hints):
        self.label.setText(hints)

    def addInfo(self, hints):
        self.textEdit.append("\n"+hints)

    def addFinal(self, hints):
        self.songs_fin.append(hints)

    def addExist(self, hints):
        self.songs_exist.append(hints)

    def finish(self):
        if 0 < len(self.songs_exist):
            self.textEdit.append("本地已存在歌曲:\n"+'\n'.join(self.songs_exist))
        if 0 < len(self.songs_fin):
            self.textEdit.append("已下载的歌曲:\n"+'\n'.join(self.songs_fin))
        self.textEdit.append("\n任务结束,详情查看mp3目录\n\n")
        self.showInfo("任务结束")
        self.work.quit()
        self.searchBtn.setEnabled(True)
        self.crawlerBtn.setEnabled(True)

#    def startSearh(self):
#        self.MyTimer.start(100)
#        self.MyTimer.timeout.connect(self.searchSongs)

    def openMp3Dir(self):
        folder = os.path.dirname(sys.executable)+"\\mp3"
        # 方法1：通过start explorer
#        os.system("start explorer %s" %folder)
        # 方法2：通过startfile
        os.startfile(folder)

    def load_ui(self):
        loader = QUiLoader()
        path = os.path.realpath(os.curdir)+"/form.ui"
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self)
        ui_file.close()

    def onClose(self):
        self.deleteLater()

class webman(QWidget):
    sigDownload = Signal(str)
    sigFinal = Signal(str)
    sigFail = Signal(str)
    sigExist = Signal(str)

    def __init__(self):
        super().__init__()
        # 不开网页搜索 设置chrome浏览器无界面模式
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        s = Service(executable_path=r"C:\\Program Files\\Google\Chrome\\Application\\chromedriver.exe")
        self.browser = webdriver.Chrome(service=s, options=chrome_options)
        self.count = 0
        self.goodMp3Count = 0

    def reset(self):
        self.browser.quit()
        self.count = 0
        self.goodMp3Count = 0

#     async def get_music(self, songdata):
#         try:
#             songinfo = songdata.split('|')
#             print("网址信息: ", songdata, len(songinfo))
#             if len(songinfo) < 3:
#                 return
#             mp3name = os.path.join(os.path.dirname(sys.executable), 'mp3/{}.mp3'.format(songinfo[0]+"-"+songinfo[1]))
#             mp3name = mp3name.replace(" ", "")
#             if os.path.exists(mp3name):
#                 print("已经存在: ", mp3name)
#                 pass
#             else:
#                 self.browser.get(songinfo[2])
# #                await asyncio.sleep(1)
#                 time.sleep(0.5)
#                 audio = self.browser.find_element(By.CLASS_NAME, "music")
#                 mp3url = audio.get_attribute('src')
#                 print("正在下载: ", mp3name)
#                 urllib.request.urlretrieve(url=mp3url, filename=mp3name)
#                 self.sigDownload.emit("正在下载: " + mp3name)
#             lrcName = os.path.join(os.path.dirname(sys.executable), 'mp3/{}.lrc'.format(songinfo[0]+"-"+songinfo[1]))
#             lrcName = lrcName.replace(" ", "")
#             if os.path.exists(lrcName):
#                 print("已经存在歌词文件: ", lrcName)
#                 pass
#             else:
#                 lrcData = self.get_songsLRC(songinfo[0], songinfo[1])
#                 if lrcData != "":
#                     with open(lrcName, 'w', encoding='utf_8_sig') as f:
#                         lrcData = lrcData.replace("\\r\\n", "\n")
#                         lrcData = lrcData.replace("\\n", "\n")
#                         f.writelines(lrcData)
#         finally:
#             self.count += 1
#             return

# 网易云下载
    async def get_musicWYY(self, songdata):
        self.count += 1
        try:
            songinfo = songdata.split('|')
            print("网址信息2: ", songdata, len(songinfo))
            if len(songinfo) < 2:
                return
            mp3url = songinfo[2]
            mp3name1 = os.path.join(os.path.dirname(sys.executable),'mp3/{}.mp3'.format(songinfo[0]+"-"+songinfo[1]))
            mp3name = mp3name1.replace(" ", "")
            ishave = False
            if os.path.exists(mp3name):
                parts = re.split(r'id=', mp3url)
                if 1 < len(parts):
                    mp3name = mp3name1.replace(".mp3", parts[1])
                    ishave = os.path.exists(mp3name)
                else:
                    ishave = True
            if not ishave:
                self.goodMp3Count += 1
                r = requests.get(mp3url, stream=True)
                # 不满足mp3格式则不写入
                if not checkMp3File(r.content):
                    print(mp3name+"不满足mp3格式！！！")
                    self.sigFail.emit("下载失败(非mp3格式):"+mp3name+" 链接:"+mp3url)
                    return
                self.sigDownload.emit("正在下载(第{}文件): ".format(self.goodMp3Count) + mp3name)
                with open(mp3name, "wb") as f:
                    for bl in r.iter_content(chunk_size=1024):
                        if bl:
                            f.write(bl)
                    f.close()
                lrcName = os.path.join(os.path.dirname(sys.executable), 'mp3/{}.lrc'.format(songinfo[0]+"-"+songinfo[1]))
                lrcName = lrcName.replace(" ", "")
                if os.path.exists(lrcName):
                    print("已经存在歌词文件: ", lrcName)
                    self.sigFinal.emit(mp3name)
                    pass
                else:
                    lrcData = self.get_songsLRC(songinfo[0], songinfo[1])
                    if lrcData != "":
                        # print('wj:', lrcData)
                        with open(lrcName, 'wb') as f:
                            # lrcData = lrcData.replace("\\r\\n", "\n")
                            # lrcData = lrcData.replace("\\n", "\n")
                            f.write(lrcData)
                        self.sigFinal.emit(mp3name)
                    else:
                        self.sigFinal.emit(mp3name+"(无歌词)")
            else:
                self.sigExist.emit(mp3name)
                print("已经存在: ", mp3name)

        finally:
            return

    # 从爬取歌曲 按歌曲或歌手
    def get_songsLRC(self, singer, songsName):
        host = "https://www.93lrc.com"
        print("歌词-->0",singer, songsName)
        keyword = "keyword="+songsName
        web_data = getDataUrl(host+"/search?"+keyword)
        htmldoc = str(web_data.text)
        htmldoc = htmldoc.replace('<!doctype html>', '', 1)
        soup = BeautifulSoup(htmldoc, 'lxml')
        # soup = BeautifulSoup(htmldoc, 'html.parser')
        lrcList = soup.select('div > table > tbody > tr > td > a')
        if len(lrcList) == 0:
            return ""
        lrcUrl = ""
        songIndex = -1
        for i in range(len(lrcList)):
            lrc = lrcList[i]
            if lrc.get_text() == singer:
                # lrcUrl = lrc.get('href')
                songIndex += i
                break
        if -1 != songIndex:
            lrcUrl = '/lrc/'+''.join(c for c in lrcList[songIndex].get('href') if c.isdigit())+".lrc"
            print(lrcList[songIndex].get('href'))
        if lrcUrl == "":
            lrcUrl = '/lrc/'+''.join(c for c in lrcList[0].get('href') if c.isdigit())+".lrc"
        lrcUrl = host+lrcUrl
        print(songsName+'歌词地址:', lrcUrl)
        r = requests.get(lrcUrl, stream=True)
        return r.content
        # soup2 = BeautifulSoup(web_data.text, 'lxml')
        # lrcWord2 = soup2.select('div.ciInfo > script')
        # pattern = r"\"\[(.*?)\"\;"
        # results = re.search(pattern, str(lrcWord2))
        # if results:
        #     return "["+results.group(1)
        # return ""

    def finished(self):
        self.browser.quit()
        print("异步任务已完成")


# 继承QThread
class Thread(QThread):
    def __init__(self):
        super().__init__()
        self.urllist = []
        self.needer = webman()

    def init_songs(self, list):
        self.needer.reset()
        self.urllist = list

    def run(self):
        # tasks = [needer.get_music(song) for song in self.urllist]
        tasks = [self.needer.get_musicWYY(song) for song in self.urllist]
        if len(tasks):
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            loop = asyncio.get_event_loop()
            wait_coro = asyncio.wait(tasks)
            loop.run_until_complete(wait_coro)
            loop.close()
            if len(self.urllist) <= self.needer.count:
                self.needer.finished()
                self.quit()


if __name__ == "__main__":
    app = QApplication([])
    path = os.path.dirname(sys.executable)+"\\mp3"
    print(path)
    if os.path.isdir(path):
        pass
    else:
        os.makedirs(path)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())

