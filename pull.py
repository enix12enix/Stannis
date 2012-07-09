import os
import threading

def delete_file_if_exists(file):
	if os.path.isfile(file):
		os.remove(file)
		print "delete file: " + file
				
svn_url = "http://svn.sc4.paypal.com/svn/projects/risk/frameworks/IDI/analytics/branches/ts-decision-kernel-1-28"
#svn_url = "http://v8.googlecode.com/svn/trunk/src/"
file_name = "ts-decision-kernel-1-28_svninfo.txt"

def pull(file_name):
	delete_file_if_exists(file_name)
	cmd = "svn -v log " + svn_url + " -l 100 >> " + file_name
	ret = os.system(cmd)

	
def get_last_changed_version(svn_url, file_name):
	delete_file_if_exists(file_name)
	cmd = "svn info " + svn_url + " >> " + file_name
	ret = os.system(cmd)
	f = open(file_name)
	for l in f:
		if l.find('Last Changed Rev') <> -1:
			print l[18:]
			return l[18:]
	f.close()


#get_last_changed_version(svn_url, file_name)

max_version=None
def get_max_version():
	global max_version
	if max_version == None:
		import tornado.database
		db = tornado.database.Connection("localhost:3306", "test_pull", "root", "mysql")
		r = db.get("SELECT max(version) as max FROM svn_log")
		max_version = r['max']
	return max_version
		
		
def check_action():
	svn_max = get_last_changed_version(svn_url, file_name)
	current_max = get_max_version()
	if svn_max > current_max:
		pass


def schdule_pull():
  threading.Timer(10, schdule_pull).start()
  check_action()


pull(file_name)