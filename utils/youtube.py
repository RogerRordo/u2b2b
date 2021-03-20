#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import re
import ssl
import json
import logging
import requests
import youtube_dl
from requests_toolbelt import SSLAdapter
from tenacity import *


class youtube:
    @classmethod
    @retry(stop=stop_after_attempt(5))
    def getVideos(cls, channel, last_updated, proxy=''):
        '''
        通过 RSS 获取 YouTube 频道最近的视频列表

        Args:
            channel: 频道 ID
            last_updated: 时间戳，只爬取该时间以后视频
            proxy(optional): http/https 代理地址，e.g. '127.0.0.1:1080'

        Returns:
            包含视频 ID 的 list

        '''
        logging.debug('正在爬取 channel {} 视频 ...'.format(channel))
        url = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + channel

        s = requests.Session()
        s.mount('https://', SSLAdapter(ssl.PROTOCOL_TLSv1))
        requests.packages.urllib3.disable_warnings()
        ssl._create_default_https_context = ssl._create_unverified_context
        if proxy != '':
            proxies = {'http': 'http://' + proxy, 'https': 'https://' + proxy}
            response = s.get(url, verify=False, proxies=proxies)
        else:
            response = s.get(url, verify=False)
        if response.status_code != 200:
            raise 'requests 错误 {}'.format(response.status_code)

        resp = response.text
        r1 = r'<yt:videoId>(.*)</yt:videoId>'
        r2 = r'<published>(.*)</published>\n\s*<updated>'
        allVids = re.findall(r1, resp)
        pubTimes = re.findall(r2, resp)
        if len(allVids) != len(pubTimes):
            raise 'allVids 与 pubTimes 长度不匹配'
        res = []
        for i in range(len(allVids) - 1, -1, -1):  # 从旧到新
            if pubTimes[i] > last_updated:
                res.append(allVids[i])
        logging.debug('共进队 {} 条视频：'.format(len(res)))
        return res

    @classmethod
    @retry(stop=stop_after_attempt(5))
    def downloadSub(cls, vid, proxy='', tempDir='temp'):
        '''
        下载 YouTube 自动字幕

        Args:
            vid: 视频 ID
            proxy(optional): http/https 代理地址，e.g. '127.0.0.1:1080'
            tempDir(optional): 临时文件夹名，默认为'temp'

        '''
        logging.debug('尝试下载自动字幕 ...')
        ydl_opts = {
            # 'logger': log,
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'outtmpl': '{}/%(id)s.%(ext)s'.format(tempDir),
        }
        if proxy:
            ydl_opts['proxy'] = 'http://' + proxy

        # youtube-dl --proxy http://{proxy}/ --list-sub https://www.youtube.com/watch?v={vid}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['https://www.youtube.com/watch?v=' + vid])

    @classmethod
    @retry(stop=stop_after_attempt(5))
    def downloadVideo(cls, vid, proxy='', tempDir='temp'):
        '''
        下载 YouTube 视频

        Args:
            vid: 视频 ID
            proxy(optional): http/https 代理地址，e.g. '127.0.0.1:1080'
            tempDir(optional): 临时文件夹名，默认为'temp'
        
        Returns:
            Info Json 对应的 dict
        
        '''
        logging.debug('正在下载视频 {} ...'.format(vid))
        ydl_opts = {
            # 'logger': log,
            'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/' + 'bestvideo[height<=720]+bestaudio/' +
            'best[height<=720]',
            'merge_output_format': 'mp4',
            'writeinfojson': True,
            'writethumbnail': True,
            'outtmpl': '{}/%(id)s.%(ext)s'.format(tempDir),
        }
        if proxy:
            ydl_opts['proxy'] = 'http://' + proxy

        # youtube-dl --proxy http://{proxy}/ -f 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]' --merge-output-format mp4 --write-info-json --write-thumbnail --write-auto-sub --sub-format vtt --sub-lang en --verbose https://www.youtube.com/watch?v={vid}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['https://www.youtube.com/watch?v=' + vid])

        with open('{}/{}.info.json'.format(tempDir, vid), 'r', encoding='utf-8') as f:
            res = json.load(f)

        return res
