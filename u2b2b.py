#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import logging
from time import sleep
from utils.converter import converter
from utils.setting import setting
from utils.bilibili import bilibili
from utils.youtube import youtube

log = logging.getLogger()
DEBUG = True


def main():
    logging.info('U2B2B 运行开始')

    st = setting.load()

    for userId in range(len(st['users'])):
        logging.info('开始处理账号{}/{}'.format(userId + 1, len(st['users'])))
        user = st['users'][userId]
        failTag = False

        # 验证 Cookie
        bl = bilibili.instance(user['cookie'])
        try:
            bilibili.checkCookie(bl)
        except Exception as e:
            logging.error('user {} -> {}'.format(userId, e))
            continue

        # 从 YouTube 找视频
        videos = []
        for channel in user['channels']:
            try:
                getVideosRes = youtube.getVideos(channel, user['last_updated'], proxy=st['proxy'])
            except Exception as e:
                failTag = True
                logging.error('channel {} -> {}'.format(channel, e))
                break
            else:
                videos.extend(getVideosRes)
        if failTag:
            continue

        # 处理视频队列
        videosLen = len(videos)
        logging.info('开始处理视频队列，共 {} 个视频'.format(videosLen))
        for i in range(videosLen):
            vid = videos[i]
            logging.info('开始处理视频({}/{})：{}'.format(i + 1, videosLen, vid))

            try:
                # 下载自动字幕
                statusStr = 'youtube.downloadSub'
                youtube.downloadSub(vid, proxy=st['proxy'])

                # 转换字幕
                statusStr = 'converter.convertSub'
                convertSubRes = converter.convertSub(vid)
                if not convertSubRes:  # 无自动字幕
                    continue

                # 下载视频
                statusStr = 'youtube.downloadVideo'
                info = youtube.downloadVideo(vid, proxy=st['proxy'])

                # 转换封面
                statusStr = 'converter.convertCover'
                converter.convertCover(info)

                # 压制字幕
                statusStr = 'converter.compressSub'
                converter.compressSub(vid)

                # 上传视频
                statusStr = 'bilibili.uploadVideo'
                bilibili.uploadVideo(bl, info, user['tid'], user['tags'])
            except Exception as e:
                failTag = True
                logging.error('{}: {}'.format(statusStr, e))
                break
        if failTag:
            continue

        # 同步 setting
        logging.info('正在保存 setting.json...')
        setting.save(st, userId)

        # 点赞评论
        sleep(10)
        try:
            bilibili.likeComment(bl, user['tid'], user['like'])
        except Exception as e:
            logging.error('点赞失败: {}'.format(e))

        logging.info('账号处理完成')

    logging.info('U2B2B 运行结束')


if __name__ == '__main__':
    if DEBUG:
        log.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(filename='log.txt',
                            filemode='w+',
                            format='levelname:%(levelname)s filename: %(filename)s '
                            'outputNumber: [%(lineno)d]  thread: %(threadName)s output msg:  %(message)s'
                            ' - %(asctime)s',
                            datefmt='[%d/%b/%Y %H:%M:%S]',
                            level=logging.INFO)
    main()
