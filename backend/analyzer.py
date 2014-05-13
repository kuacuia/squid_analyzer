import sys,time,json,pickle
import eventlet
from  get_ip_source import *
import redis_connector as redis

logfile = '/usr/local/squid/var/logs/squid_access.log'
#logfile = 'log25w.log'

column_time = [ ]  # each hour as key
column_ip = {}   # source ip
column_cache_type = {} #hit or miss
column_response_code = {} # http repsonse code ,200,400...
column_response_size = {} # size responsed from web server
column_url = {}  # url list
column_content_type = {} # img or file
column_mime_type = {} # browser content type, system type...
browser_type = {
	'Iphone' : 0,
	'Ipad' : 0,
	'Android' : 0,
	'PC_device' : 0,
	}


def get_top_region(source_ip_list): 
	'''return a sorted region ip list'''
	region_rank_dic = {}
	#for ip in source_ip_list:
	for ip in source_ip_list:
		region_ip = '.'.join(ip.split('.')[0:2] )
		if not region_ip.startswith('-/'): #remove - 
			if region_rank_dic.has_key(region_ip):
				region_rank_dic[region_ip][0] +=1
			else:
				region_rank_dic[region_ip] = [1, ip.split('/')[0] ]

	#print "Region:", len(region_rank_dic),'Vistor:',len(ip_rank_list) 


	#print sorted(ip_rank_list, key=lambda x:x[1] , reverse=True)[:15]
	top_region_list = sorted(region_rank_dic.items(), key=lambda x:x[1][0],reverse=True)[:100]
	return top_region_list #region_rank_dic


def get_region_rank_list(top_region_list):
	'''return a top region list which has converted to real address'''
	print top_region_list	
	pool = eventlet.GreenPool()
	summary_region = {}
	for province,city,uv  in pool.imap(get_url2, top_region_list):
		#print province,city,uv
		if summary_region.has_key('%s%s' %(province,city) ):
			summary_region['%s%s' %(province,city)] += uv[1][0]
		else:
			summary_region['%s%s' %(province,city)] = uv[1][0]
		#print province,city,uv
	#for region,count in summary_region.items():print region,count
	return summary_region


f = file(logfile)
hour_end_time = float(f.readline().split()[0]) #
column_time = [{'hour_end_time':[hour_end_time, []],
		'total_size': 0, 
	}]

raw_ip_list = [] #save all the ip address
while True:
	line = f.readline().split()
	if len(line) == 0:break
	access_time,raw_ip , cache_type, response_size,request_url,content_type,MIME_content_type= float(line[0]) ,line[2], line[3],line[4],line[6],line[9],line[11]
	refer_link = line[10]
	squid_cache_type,http_response_code = cache_type.split('/')
	if  access_time < hour_end_time : #log less than one hour
		column_time[-1]['hour_end_time'][1].append(raw_ip)
		column_time[-1]['total_size'] += int(response_size)
	else:
		hour_end_time = access_time + 3600 
		column_time.append(
			{'hour_end_time':[hour_end_time ,[] ], 'total_size': int(response_size) }
		)
	#print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( access_time)),  column_time[-1]['total_size']/1024/1024 	
	
	#cache type
	if column_cache_type.has_key(squid_cache_type):
		column_cache_type[squid_cache_type]	+=1
	else:
		column_cache_type[squid_cache_type] = 1
	#Http response code
	if column_response_code.has_key(http_response_code):
		column_response_code[http_response_code] +=1
	else:
		column_response_code[http_response_code] = 1
	#Content type
	if column_content_type.has_key(content_type):
		column_content_type[ content_type ] +=1
	else:
		column_content_type[content_type] = 1
	#Request url  
	if column_url.has_key(request_url):
		column_url[request_url] +=1
	else:	
		column_url[request_url] = 1
	#Browser type
	if 'iPhone' in MIME_content_type:
		browser_type['Iphone'] +=1
	elif 'iPad' in MIME_content_type:
		browser_type['Ipad'] +=1

	elif 'Android' in MIME_content_type:
		browser_type['Android'] +=1
	else:
		browser_type['PC_device'] +=1
	#by region
	raw_ip_list.append(raw_ip)

total_uv_list = set(raw_ip_list)
column_by_region= get_region_rank_list( get_top_region(  total_uv_list )  )
column_by_region_pv = get_region_rank_list( get_top_region( raw_ip_list) )
print '*'*50
for i in column_time:
 	i['hour_end_time'][1] = set( i['hour_end_time'][1] )
	#print i['hour_end_time'][1] 
	#i['region_rank'] = get_top_region( i['hour_end_time'][1] )	
	#i['region_rank_readable']  =get_region_rank_list( i['region_rank'] )	
	#delete ip list
	i['vistors'] = len(i['hour_end_time'][1]) 
	del i['hour_end_time'][1]
	print 'Time:%s   Vistor:%s   TotalSize:%s' % ( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(  i['hour_end_time'][0])), i['vistors'], i['total_size']/1024/1024 )
for k,v in column_cache_type.items():print k,v

for k,v in column_response_code.items():print k,v

for k,v in column_content_type.items():print k,v

column_url = sorted(column_url.items(), key=lambda x:x[1] , reverse=True)[:20]

for k,v in browser_type.items():print k,v


statistic_dic = {
		'by_hour' : column_time,
		'by_cache_type' : column_cache_type,
		'by_response_code' : column_response_code,
		'by_content_type' : column_content_type,
		'by_url' : column_url,
		'by_browser_type': browser_type,
		'by_region' : column_by_region,
		'by_region_pv' : column_by_region_pv,
		'total_pv': len(raw_ip_list),
		'total_uv': len(total_uv_list),
	}

print statistic_dic
redis.r['SquidLog::localhost'] = pickle.dumps( statistic_dic)

f = file('log_data.pkl','wb')
pickle.dump( statistic_dic, f)
f.close()
