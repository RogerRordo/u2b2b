#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import logging
from datetime import datetime
from datetime import timedelta
from time import sleep
from bilibiliupload.bilibili import Bilibili
from tenacity import *
from bilibiliupload import VideoPart


class bilibili:
    @classmethod
    def __getYesterdayStr(cls):
        ''' 昨天的yyyymmdd字符串 '''
        return datetime.strftime(datetime.now() - timedelta(days=1), '%Y%m%d')

    @classmethod
    def __info2Data(cls, info, tid, tags, tempDir):
        ''' info to uploadData '''
        # title
        # 官方：80字以内
        # title = '【英语字幕】【' + info['uploader'] + '】' + info['title']
        title = info['title']
        title = title[:80]

        # tag
        # 官方：Tag不能为空，总数量不能超过12个， 并且单个不能超过20个字
        # 此处：长度1-15，不超过10个
        tag = ['Youtube'] + tags + [info['uploader']]
        tag = tag[:10]
        u2bTags = info['tags']
        if u2bTags:
            for x in u2bTags:
                if len(x) in range(1, 16):
                    if len(tag) >= 10:
                        break
                    tag.append(x)

        # desc
        # 官方：250字以内
        # 此处：按回车分割字符串，取至250
        '''
        u2bDesc = info['description']
        descList = u2bDesc.split('\n')
        desc = ''
        for x in descList:
            temp = desc + x + '\n'
            if len(temp) > 250:
                break
            desc = temp
        '''
        desc = '作者：{}\n\n'.format(info['uploader'])
        desc += '字幕是自动字幕，有好的建议或想看什么请评论或私聊\n'

        data = {
            'parts': VideoPart('{}/{}_sub.mp4'.format(tempDir, info['id'])),
            'title': title,
            'tid': tid,
            'tag': tag,
            'desc': desc,
            'source': 'https://www.youtube.com/watch?v=' + info['id'],
            'cover': '{}/{}.jpg'.format(tempDir, info['id']),
            'open_subtitle': True
        }
        return data

    @classmethod
    def instance(cls, cookie):
        '''
        获取 cookie 对应的 Bilibili 实例

        Args:
            cookie: cookie 字符串
        
        Returns:
            Bilibili 实例
        
        '''
        return Bilibili(cookie)

    @classmethod
    @retry(stop=stop_after_attempt(5))
    def checkCookie(cls, bl):
        '''
        检查 Cookie

        Args:
            bl: Bilibili 实例
        
        '''
        logging.debug('正在检查 Cookie ...')
        navResp = bl.nav().get('code')
        if navResp != 0:
            raise 'Cookie失效！'

    @classmethod
    @retry(stop=stop_after_attempt(5))
    def uploadVideo(cls, bl, info, tid, tags, tempDir='temp'):
        '''
        上传视频到 Bilibili

        Args:
            bl: Bilibili 实例
            info: YouTube 视频下载得到的 info dict
            tid: 上传分区 ID
            tags: tags list
            tempDir(optional): 临时文件夹名，默认为'temp'

        Returns:
            API 返回 JSON 对应的 dict
        
        '''
        logging.debug('正在上传视频 ...')
        data = cls.__info2Data(info, tid, tags, tempDir)

        data['cover'] = bl.cover_up(data['cover'])

        res = bl.upload(**data)
        # {'code': 0, 'message': '0', 'ttl': 1, 'data': {'aid': 885682511, 'bvid': 'BV1aK4y1L7Rh'}}
        # {"code": 21070, "message": "您投稿的频率过快，请稍等30秒", "ttl": 1}

        if res.get('code') != 0:
            raise '上传视频失败 {}'.format(res.get('code'))

        return res

    @classmethod
    def likeComment(cls, bl, tid, like):
        searchResp = bl.search(cate_id=tid,
                               time_from=cls.__getYesterdayStr(),
                               time_to=cls.__getYesterdayStr(),
                               order='scores')

        if searchResp['code'] != 0 or searchResp.get('result') is None or len(searchResp['result']) == 0:
            raise '搜索视频失败 {}'.format(searchResp)

        aid = searchResp['result'][0]['id']
        count = searchResp['result'][0]['review']
        # 只点一个视频
        if count > like['count']:
            count = like['count']
        logging.debug('正在点赞视频 av{} 的评论，共 {} 个 ...'.format(aid, count))
        pageId = 0
        while count:
            pageId += 1
            logging.debug('正在点赞第 {} 页 ...'.format(pageId))
            getCommResp = bl.get_comments(oid=aid, pn=pageId, sort=0)
            if getCommResp['code'] != 0:
                raise '读取评论失败 {}'.format(getCommResp)
            replies = getCommResp['data'].get('replies')
            if replies is None:
                logging.debug('评论触底')
                return

            for reply in replies:
                rpid = reply['rpid']
                likeCommResp = bl.like_comment(oid=aid, rpid=rpid)
                if likeCommResp['code'] != 0:
                    raise '点赞失败 rpid={} {}'.format(rpid, likeCommResp)
                count -= 1
                if count == 0:
                    return
                sleep(like['sleep'])
