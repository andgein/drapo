import multiprocessing


user = 'www-data'
group = 'www-data'
bind = '0.0.0.0:80'
workers = multiprocessing.cpu_count() * 2 + 1
threads = workers
accesslog = '-'
errorlog = '-'

# allow x-forwarder-for headers
forwarded_allow_ips = '*'

# alter log format to see real ip of a user
access_log_format = '%({X-Real-IP}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
