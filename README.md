# Gluster Tools

My collection of handy Gluster tools

* __geo-rep-status-compare.py__: Gluster geo-replication status check comparison tool
    * Parse output for two geo-replication status reports
    * Report the time difference between the two, as well as the progress rates
    * Report any errors identified
    * Timestamp defaults to the modification time of file, overridden by a timestamp of the format yyyy-mm-dd hh:mm:ss inside the file on a line by itself
    * Sample of how to collect data:
~~~
gluster volume geo-replication mastervol ssh://node-5::slavevol status > mastervol.status
date +"%F %T" >> mastervol.status
~~~
    * Sample of running the tool:
~~~
# geo-rep-status-compare.py 4x3 status_t2 status_t1
===== Times =====
F1 time:  2017-09-12 14:14:00
F2 time:  2017-09-08 12:36:00
Elapsed time:  4 days, 1:38:00
[W] Warning: Previous active count ( 3 ) not equal to subvolume count ( 4 )
[W] Warning: Some previous bricks not in Active/Passive status:
	Brick:  ('node-1', '/brick/mastervol')  Status:  Faulty
('node-1', '/brick/mastervol') not matched in be4
Node: ('node-2', '/brick/mastervol') Current: 2017-09-12 14:13:22 ||| Behind: 0:00:38 ||| Progress: 4 days, 1:37:46 ||| Progress Ratio: 1.0000
Node: ('node-3', '/brick/mastervol') Current: 2017-09-12 14:13:20 ||| Behind: 0:00:40 ||| Progress: 4 days, 1:37:49 ||| Progress Ratio: 1.0000
Node: ('node-4', '/brick/mastervol') Current: 2017-09-12 14:13:16 ||| Behind: 0:00:44 ||| Progress: 4 days, 1:37:40 ||| Progress Ratio: 0.9999
~~~
