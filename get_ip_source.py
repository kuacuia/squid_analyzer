#!/usr/bin/env python
#coding=utf8

import urllib,sys,json
import urllib2



def get_url(url, ip):
	req = urllib2.Request(url)
	res_data = urllib2.urlopen(req)
	res = json.loads(res_data.read())
	print res['data']['region'], res['data']['city'], ip

def fetch(url):
        req = urllib2.Request(url)
        res_data = urllib2.urlopen(req)
        res = json.loads(res_data.read())
        #return (res['data']['region'], res['data']['city'], url)
	return res['data']['region'], res['data']['city']


def get_url2(ip_raw):
  ip = ip_raw[1][1]
  if len(ip) >8:
        url = 'http://ip.taobao.com/service/getIpInfo.php?ip=%s' % ip
        req = urllib2.Request(url)
        res_data = urllib2.urlopen(req)
        res = json.loads(res_data.read())
        return res['data']['region'], res['data']['city'], ip_raw
"""
def get_url2(ip_raw):
  ip = ip_raw[0].split('/')
  if len(ip[0]) >8:
	url = 'http://ip.taobao.com/service/getIpInfo.php?ip=%s' % ip[0] 
	req = urllib2.Request(url)
        res_data = urllib2.urlopen(req)
        res = json.loads(res_data.read())
        return res['data']['region'], res['data']['city'], ip_raw
"""
if __name__ == '__main__':
	ip = sys.argv[1]
	url = 'http://ip.taobao.com/service/getIpInfo.php?ip=%s' %ip.split('/')[0]
	get_url(url,'')
