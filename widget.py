# This Python file uses the following encoding: utf-8

import os
from pathlib import Path
import sys
import requests

import urllib
from bs4 import BeautifulSoup
from selenium import webdriver
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit
from PyQt5.QtCore import QThread
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QTimer
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


class Widget(QWidget):
    def __init__(self):
        super(Widget, self).__init__()
        self.MyTimer = QTimer()
        self.index = 0
        self.songs_list = []
        self.load_ui()
        self.crawler = self.findChild(QPushButton, "pushButton")
        self.closeWg = self.findChild(QPushButton, "pushButton_2")
        self.textEdit = self.findChild(QTextEdit, "textEdit")
#        self.crawler.clicked.connect(self.get_info)
        self.crawler.clicked.connect(self.startSearh)
        self.closeWg.clicked.connect(self.close)

    def get_info(self):
        self.index += 1
        host = "https://www.kugou.com/yy/rank/home/"
        url = host+"{}-8888.html".format(self.index)
        web_data = requests.get(url, headers=headers)
        soup = BeautifulSoup(web_data.text, 'lxml')
        ranks = soup.select('span.pc_temp_num')
        titles = soup.select('div.pc_temp_songlist > ul > li > a')
        times = soup.select('span.pc_temp_tips_r > span')
        for rank, title, time1 in zip(ranks, titles, times):
            data = {
                "rank": rank.get_text().strip(),
                "singer": title.get_text().replace("\n", "").replace("\t", "").split('-')[1],
                "song": title.get_text().replace("\n", "").replace("\t", "").split('-')[0],
                "time": time1.get_text().strip(),
                "url": title.get('href')
            }
            print("tile", title.get('href'))
            strData = str(data)
            self.textEdit.append(strData)
            # 获取歌曲
            songs_url = title.get('href')
            if songs_url != '':
                self.songs_list.append(data["singer"]+'|'+data["song"]+'|'+songs_url)
        # 启动任务
        if self.index == 23:
            print("启动任务,获取歌曲地址")
            self.MyTimer.stop()
            work = Thread()
            work.init_songs(self.songs_list)
            work.wait()
            work.start()
            work.finished.connect(self.finish)

    def finish(self):
        self.textEdit.append("任务结束,详情查看mp3目录\n\n\n")

    def startSearh(self):
        self.MyTimer.start(100)
        self.MyTimer.timeout.connect(self.get_info)

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self)
        ui_file.close()


class webman(object):
    def __init__(self):
        super().__init__()
        # 不开网页搜索 设置chrome浏览器无界面模式
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        s = Service(executable_path=r"C:\\Program Files\\Google\Chrome\\Application\\chromedriver.exe")
        self.browser = webdriver.Chrome(service=s, options=chrome_options)
        self.count = 0

    async def get_music(self, songdata):
        self.count += 1
        try:
            songinfo = songdata.split('|')
            print("网址信息: ", songdata, len(songinfo))
            if len(songinfo) < 3:
                return
            mp3name = './mp3/{}.mp3'.format(songinfo[0]+"-"+songinfo[1])
            mp3name = mp3name.replace(" ", "")
            if os.path.exists(mp3name):
                print("已经存在: ", mp3name)
                pass
            else:
                self.browser.get(songinfo[2])
#                await asyncio.sleep(0.5)
                time.sleep(0.5)
                audio = self.browser.find_element(By.CLASS_NAME, "music")
                mp3url = audio.get_attribute('src')
                print("正在下载: ", mp3name)
                urllib.request.urlretrieve(url=mp3url, filename=mp3name)
        finally:
            return

    def finished(self):
        self.browser.quit()
        print("异步任务已完成")


# 继承QThread
class Thread(QThread):
    def __init__(self):
        super().__init__()
        self.urllist = []

    def init_songs(self, list):
        self.urllist = list

    def run(self):
        needer = webman()
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        tasks = [needer.get_music(song) for song in self.urllist]
        wait_coro = asyncio.wait(tasks)
        loop.run_until_complete(wait_coro)
        loop.close()
        if len(self.urllist) <= needer.count:
            needer.finished()
            self.quit()


if __name__ == "__main__":
    app = QApplication([])
    path = "mp3"
    if os.path.isdir(path):
        pass
    else:
        os.makedirs(path)
    widget = Widget()
    widget.show()
    sys.exit(app.exec_())

