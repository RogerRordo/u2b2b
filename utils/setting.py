#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: RogerRordo

import json
import logging
from datetime import datetime


class setting:
    @classmethod
    def __local2utc(cls, local_dtm):
        ''' 本地转 UTC '''
        return datetime.utcfromtimestamp(local_dtm.timestamp())

    @classmethod
    def load(cls, fileName='setting.json'):
        '''
        读取 setting JSON 文件

        Args:
            fileName(optional): setting 文件名，默认为'setting.json'
        
        Returns:
            对应的 dict

        '''
        logging.debug('正在读取 {} ...'.format(fileName))
        with open(fileName, 'r', encoding='utf-8') as f:
            res = json.load(f)
        return res

    @classmethod
    def save(cls, st, userId, fileName='setting.json'):
        '''
        读取 setting JSON 文件

        Args:
            st: setting 对应的 dict
            userId: 此次更新的 user ID
            fileName(optional): setting 文件名，默认为'setting.json'

        '''
        logging.debug('正在保存 {} ...'.format(fileName))
        utcNow = cls.__local2utc(datetime.now()).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        logging.debug('现在是 UTC 时间 {}'.format(utcNow))
        st['users'][userId]['last_updated'] = utcNow
        with open('setting.json', 'w+', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False)
