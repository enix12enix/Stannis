import os
import threading
import logging

def delete_file_if_exists(file):
	if os.path.isfile(file):
		os.remove(file)
		print "delete file: " + file
				
svn_url = "http://svn.sc4.paypal.com/svn/projects/risk/frameworks/IDI/workflow/branches/ts-decision-kernel-1-28"
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
			last_rev = l[18:-1]
			logging.info("Last Changed Rev:" + last_rev) 
			f.close()
			return last_rev
	f.close()

max_version=None
def get_max_version():
	global max_version
	if max_version == None:
		import tornado.database
		db = tornado.database.Connection("localhost:3306", "stannis", "root", "mysql")
		r = db.get("SELECT max(version) as max FROM svn_log")
		max_version = r['max']
	return max_version
		
		
def check_action():
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='monitor.log', level=logging.DEBUG)
	svn_max = get_last_changed_version(svn_url, file_name)
	current_max = get_max_version()

	if int(svn_max) > int(current_max):
		log_file_name = "svn_history.log"
		#delete_file_if_exists(log_file_name)
		cmd = "svn -v log " + svn_url + " -r " + current_max + ":" + svn_max + " >> " + log_file_name
		logging.info("svn pull cmd: " + cmd)
		ret = os.system(cmd)


def schdule_pull():
  threading.Timer(10, schdule_pull).start()
  #check_action()


