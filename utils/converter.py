#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import re
import os
import json
import logging
from datetime import datetime
from datetime import timedelta
from subprocess import DEVNULL, STDOUT, check_call


class converter:
    # parameters
    __SCRIPT_INFO_HEADER = '[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: Yes\nYCbCr Matrix: TV.709\nPlayResX: 1920\nPlayResY: 1080\n\n'
    __V4STYLE_HEADER = '[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: '
    __STYLE = 'Default,Arial,53.7,&H00FFFFFF,&HC0FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,2,0,1,10,10,10,1'
    __EVENTS_HEADER = '\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'

    __BOX_X = 540
    __BOX_Y = 1100
    __LINE_HEIGHT = 54
    __DURATION = 370

    @classmethod
    def __dt2Str(cls, x):
        ''' datetime to str '''
        return x.strftime('%H:%M:%S.%f')[:-3]

    @classmethod
    def __str2Dt(cls, x):
        ''' str to datetime '''
        return datetime.strptime(x + '000', '%H:%M:%S.%f')

    @classmethod
    def __strAfterX(cls, x, ms):
        ''' str + ms microseconds -> str '''
        dt = cls.__str2Dt(x) + timedelta(microseconds=ms)
        return cls.__dt2Str(dt)

    @classmethod
    def __calcK(cls, x, y):
        ''' calculate {\k(?)}, unit = 10ms '''
        timeDelta = cls.__str2Dt(y) - cls.__str2Dt(x)
        return round((timeDelta / timedelta(microseconds=1)) / 10000)

    @classmethod
    def __readVtt(cls, vttPath):
        ''' read .vtt file '''
        # import
        with open(vttPath, 'r', encoding='utf-8') as f:
            vttContent = f.read()

        # extract
        r0 = r'(\d{2}:\d{2}:\d{2}.\d{3}) --> (\d{2}:\d{2}:\d{2}.\d{3}) .*\n.*\n([^\n]*)'
        r1 = r'(</c>)?<(\d{2}:\d{2}:\d{2}.\d{3})>(<c>)?'
        subs = []
        valid = False
        for batchIter in re.finditer(r0, vttContent):
            valid = not valid
            if not valid:
                continue
            times = [batchIter.group(1)]
            lastTime = batchIter.group(2)
            words = []
            rowElems = re.split(r1, batchIter.group(3))
            rowElems = list(filter(lambda x: x not in ['<c>', '</c>', None], rowElems))
            for i in range(len(rowElems)):
                if i % 2:
                    times.append(rowElems[i])
                else:
                    words.append(rowElems[i])
            words[-1] = re.sub(r'</c>', '', words[-1])
            times.append(lastTime)
            subs.append((times, words))

        return subs

    @classmethod
    def __subs2ass(cls, subs, assPath):
        ''' export subs to .ass file '''
        with open(assPath, 'w') as f:
            f.write(cls.__SCRIPT_INFO_HEADER + cls.__V4STYLE_HEADER + cls.__STYLE + cls.__EVENTS_HEADER)
            for i in range(len(subs)):
                times, words = subs[i]
                if (i < len(subs) - 1):
                    times.append(subs[i + 1][0][0])
                    times.append(subs[i + 1][0][-1])
                    times.append(cls.__strAfterX(times[-1], 500000))
                else:
                    times.append(subs[i][0][-1])
                    times.append(cls.__strAfterX(times[-1], 1000000))
                    times.append(cls.__strAfterX(times[-1], 500000))

                # line 1
                line = 'Dialogue: 0,' + times[0][:-1] + ',' + times[-3][:-1] + ',Default,,0,0,0,,'
                line += '{' + '\move({},{},{},{},{},{})'.format(
                    cls.__BOX_X, cls.__BOX_Y, cls.__BOX_X, cls.__BOX_Y - cls.__LINE_HEIGHT, 0, cls.__DURATION) + '}'
                for j in range(len(words)):
                    line += '{' + '\k{}'.format(cls.__calcK(times[j], times[j + 1])) + '}'
                    line += words[j]
                f.write(line + '\n')

                # line 2
                line = 'Dialogue: 0,' + times[-3][:-1] + ',' + times[-2][:-1] + ',Default,,0,0,0,,'
                line += '{' + '\move({},{},{},{},{},{})'.format(cls.__BOX_X, cls.__BOX_Y - cls.__LINE_HEIGHT,
                                                                cls.__BOX_X, cls.__BOX_Y - 2 * cls.__LINE_HEIGHT, 0,
                                                                cls.__DURATION) + '}'
                line += ''.join(words)
                f.write(line + '\n')

                # line 3
                line = 'Dialogue: 0,' + times[-2][:-1] + ',' + times[-1][:-1] + ',Default,,0,0,0,,'
                line += '{' + '\move({},{},{},{},{},{})'.format(cls.__BOX_X, cls.__BOX_Y - 2 * cls.__LINE_HEIGHT,
                                                                cls.__BOX_X, cls.__BOX_Y - 3 * cls.__LINE_HEIGHT, 10,
                                                                cls.__DURATION + 10)
                line += '\clip({},{},{},{})'.format(0, cls.__BOX_Y - cls.__LINE_HEIGHT * 3 - 15, 1920, 1080) + '}'
                line += ''.join(words)
                f.write(line + '\n')

    @classmethod
    def __subs2bcc(cls, subs, bccPath):
        with open(bccPath, 'w') as f:
            lastLine = ''
            body = []
            for i in range(len(subs) - 1):
                times, words = subs[i]
                currLine = ''
                for j in range(len(words)):
                    st = cls.__calcK('00:00:00.000', times[j]) / 100
                    if j < len(words) - 1:
                        ed = cls.__calcK('00:00:00.000', times[j + 1]) / 100
                    else:
                        ed = cls.__calcK('00:00:00.000', subs[i + 1][0][0]) / 100
                    currLine += words[j]
                    if st < ed:
                        body.append({'from': st, 'to': ed, 'location': 1, 'content': lastLine + '\n' + currLine})
                lastLine = currLine

            jsonData = {
                'font_size': 0.4,
                'font_color': '#FFFFFF',
                'background_alpha': 0.5,
                'background_color': '#9C27B0',
                'Stroke': 'none',
                'body': body
            }
            json.dump(jsonData, f)

    @classmethod
    def convertSub(cls, vid, tempDir='temp'):
        '''
        转换自动字幕

        Args:
            vid: 视频 ID
            proxy(optional): http/https 代理地址，e.g. '127.0.0.1:1080'
            tempDir(optional): 临时文件夹名，默认为'temp'
        
        Returns:
            是否有自动字幕(bool)

        '''

        vttPath = '{}/{}.en.vtt'.format(tempDir, vid)
        if os.path.exists(vttPath):
            assPath = '{}/{}.ass'.format(tempDir, vid)
            logging.debug('正在转换自动字幕 {} -> {} ...'.format(vttPath, assPath))
            cls.__subs2ass(cls.__readVtt(vttPath), assPath)
            return True
        else:
            logging.debug('无自动字幕 {}'.format(vttPath))
            return False

    @classmethod
    def convertCover(cls, info, tempDir='temp'):
        '''
        转换封面图片为 .jpg 文件

        Args:
            info: YouTube 视频下载得到的 info dict
            tempDir(optional): 临时文件夹名，默认为'temp'

        '''
        origFmt = info['thumbnail'].split('.')[-1].split('?')[0]
        origPath = '{}/{}.{}'.format(tempDir, info['id'], origFmt)
        newPath = '{}/{}.jpg'.format(tempDir, info['id'])
        logging.debug('正在转换封面 {} -> {} ...'.format(origPath, newPath))

        # ffmpeg -y -i {tempDir}/{vid}.webp {tempDir}/{vid}.jpg
        check_call(['ffmpeg', '-y', '-i', origPath, newPath], stdout=DEVNULL, stderr=STDOUT)

    @classmethod
    def compressSub(cls, vid, tempDir='temp'):
        '''
        硬压制自动字幕

        Args:
            vid: 视频 ID
            tempDir(optional): 临时文件夹名，默认为'temp'

        '''
        logging.debug('正在压制字幕 ...')

        if os.path.exists('{}/{}_sub.mp4'.format(tempDir, vid)):
            logging.debug('字幕已存在')
            return

        # ffmpeg -y -i {tempDir}/{vid}.mp4 -vf subtitles={tempDir}/{vid}.ass {tempDir}/{vid}_sub.mp4
        check_call([
            'ffmpeg', '-y', '-i', '{}/{}.mp4'.format(tempDir, vid), '-vf', 'subtitles={}/{}.ass'.format(tempDir, vid),
            '{}/{}_sub.mp4'.format(tempDir, vid)
        ],
                   stdout=DEVNULL,
                   stderr=STDOUT)
