#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   cold
#   E-mail  :   wh_linux@126.com
#   Date    :   14/01/16 11:33:32
#   Desc    :   SimSimi插件
#
import json

from tornadohttpclient import TornadoHTTPClient

import config

from plugins import BasePlugin


class SimSimiTalk(object):
    """ 模拟浏览器与SimSimi交流

    :params http: HTTP 客户端实例
    :type http: ~tornadhttpclient.TornadoHTTPClient instance
    """
    def __init__(self, http = None):
        self.http = http or TornadoHTTPClient()

        if not http:
            self.http.set_user_agent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/28.0.1500.71 Chrome/28.0.1500.71 Safari/537.36")
            self.http.debug = getattr(config, "TRACE", False)
            self.http.validate_cert = False
            self.http.set_global_headers({"Accept-Charset": "UTF-8,*;q=0.5"})

        self.url = "http://www.simsimi.com/func/req"
        self.params = {"lc":"zh", "ft":0.0}
        self.ready = False

        self.fetch_kwargs = {}
        if config.SimSimi_Proxy:
            self.fetch_kwargs.update(proxy_host = config.SimSimi_Proxy[0],
                                     proxy_port = config.SimSimi_Proxy[1])

        self._setup_cookie()


    def _setup_cookie(self):
        def callback(resp):
            self.ready = True

        self.http.get("http://www.simsimi.com", callback = callback)


    def talk(self, msg, callback):
        """ 聊天

        :param msg: 信息
        :param callback: 接收响应的回调
        """
        headers = {"Referer":"http://www.simsimi.com/talk.htm",
                   "Accept":"application/json, text/javascript, */*; q=0.01",
                   "Accept-Language":"zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
                   "Content-Type":"application/json; charset=utf-8",
                   "X-Requested-With":"XMLHttpRequest",
                   }
        if not msg.strip():
            return callback(u"小的在")
        params = {"msg":msg.encode("utf-8")}
        params.update(self.params)

        def _talk(resp):
            data = {}
            if resp.body:
                try:
                    data = json.loads(resp.body)
                except ValueError:
                    pass
            callback(data.get("response", "Server respond nothing!"))

        self.http.get(self.url, params, headers = headers,
                      callback = _talk)


class SimSimiPlugin(BasePlugin):
    simsimi = None

    def is_match(self, form_uin, content, type):
        if not getattr(config, "SimSimi_Enabled", False):
            return False
        else:
            self.simsimi = SimSimiTalk()

        if type == "g":
            if content.startswith(self.nickname.lower().strip()) or \
               content.endswith(self.nickname.lower().strip()):
                self.content = content.strip(self.nickname)
                return True
        else:
            self.content = content
            return True
        return False

    def handle_message(self, callback):
        self.simsimi.talk(self.content, callback)


if __name__ == "__main__":
    import threading,time
    simsimi = SimSimiTalk()
    def callback(response):
        print response
        simsimi.http.stop()

    def talk():
        while 1:
            if simsimi.ready:
                simsimi.talk("nice to meet you", callback)
                break
            else:
                time.sleep(1)

    t = threading.Thread(target = talk)
    t.setDaemon(True)
    t.start()
    simsimi.http.start()
