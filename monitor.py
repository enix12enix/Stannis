# -*- coding: utf-8 -*-
import re
import os
import logging
import threading
import time
from datetime import datetime

import tornado.database
from gen_diff import GenDiffer



svn_url_prefix = "http://svn.sc4.paypal.com/svn/projects"
#svn_url_prefix = "http://v8.googlecode.com/svn"
split_line = "------------------------------------------------------------------------\n"

# TODO set in conf file
db = tornado.database.Connection("localhost:3306", "stannis", "root", "mysql")

#svn_url = "http://v8.googlecode.com/svn/trunk/sc/"

def assemble(file_name, m_id):
	logging.debug('assemble method...')

	log_file = open(file_name)
	checkin = []
	for line in log_file:
		if line == split_line:			
			if len(checkin) <> 0:
				insert_record(checkin, m_id)			
			checkin = []
		else:
			checkin.append(line)

	log_file.close()

def insert_record(record, m_id):	
	sp_line = find_split_line(record)
	
	# change path
	if sp_line == 3:
		change_paths = record[2:3]	
	else:
		change_paths = record[2:sp_line]  
		
	result = record[0].split('|')
	
	# comments
	comments = ''
	for i in record[sp_line+1:]:
		comments = comments + i
		
	comments = re.sub(r'[^\x00-\x7F]', '_', comments)
	comments = comments.replace('\n', '<br>')
	logging.debug('comments: %s', comments)
	
	if result <> None:
		version = result[0].strip()[1:] # version
		acct_name = result[1].strip() # name
		str_dt =  result[2].strip() # date time
		date_time = datetime.strptime(str_dt[:19], "%Y-%m-%d %H:%M:%S")
		# get record id from db
		svn_log_id = db.execute("insert into svn_log(version, acct_name, date_time, comments, m_id) values(%s, %s, %s, %s, %s)",\
			 version, acct_name, date_time, comments, m_id)
		
		logging.debug('svn_log_id: %s', svn_log_id)
		
		for entry in change_paths:
			change_path = entry.strip().split(' ')
			logging.debug('change_path: %s', change_path)

			if len(change_path) > 0:			
				filename = get_filename(change_path[1])
				lcp_id = None
				
				if len(change_path) == 4:
					# change_path[3] --> '/risk/frameworks/IDI/eventrouter/trunk:192953)'
					lcp_id = add_linked_change_path(change_path[3][:-1])

				if filename == None:
					if lcp_id == None:
						svn_cp_id = db.execute("insert into svn_change_path(action, path, f_id) values(%s, %s, %s)", \
							change_path[0], change_path[1], svn_log_id)
					else:
						svn_cp_id = db.execute("insert into svn_change_path(action, path, f_id, f_link_cp_id) values(%s, %s, %s, %s)", \
							change_path[0], change_path[1], svn_log_id, lcp_id)
				else:
					if lcp_id == None:
						svn_cp_id = db.execute("insert into svn_change_path(action, path, filename, f_id) values(%s, %s, %s, %s)", \
							change_path[0], change_path[1], filename, svn_log_id)
					else:
						svn_cp_id = db.execute("insert into svn_change_path(action, path, filename, f_id, f_link_cp_id) values(%s, %s, %s, %s, %s)", \
							change_path[0], change_path[1], filename, svn_log_id, lcp_id)
					# gen diff for file path
					gen_diff(change_path[0], change_path[1], version, svn_cp_id, filename)
	

def add_linked_change_path(path):
	logging.debug('insert linked change path record to db...')
	return db.execute("insert into svn_linked_change_path(path) values(%s)", path)
	
def get_filename(path):
	i = -1
	while -i < len(path):
		if path[i] == '/' and path[i:].find('.') <> -1:
			return path[i+1:]
		i = i - 1
	return None
		

def find_split_line(lines):
	i = 3
	for line in lines[3:]:
		if line == '\n':
			return i
		i= i + 1
	return 3

def filter(filename):
	# filter pom.xml
	if filename == 'pom.xml':
		return True
	
	filter_table = ["zip", "rar", "bmp", "png", "gif"]

	for t in filter_table:
		if filename.split('.')[-1] == t:
			return True

	return False

	
def gen_diff(action, path, version, cp_id, filename):
	if filter(filename):
		return

	if action == "A":
		if path[-1] <> "/":
			logging.info('code path: %s', path)
			df = GenDiffer(svn_url_prefix, path, version)
			code = df.get_code()

			db.execute("insert into svn_diffs(f_cp_id, diff) values(%s, %s)", cp_id, code)
			logging.debug('insert added record to db...')

	elif action == "M":
		# not directory
		if path[-1] <> "/":
			logging.info('code path: %s', path)
			df = GenDiffer(svn_url_prefix , path, version)
			df_html = df.gen_differ()
			if df_html <> None:
				db.execute("insert into svn_diffs(f_cp_id, diff) values(%s, %s)", cp_id, df_html)
				logging.debug('insert diff record to db...')
	elif action == "D":
		pass		
	elif action == 'R':
		pass


def delete_file_if_exists(file):
	if os.path.isfile(file):
		os.remove(file)
		logging.info('delete file: %s', file)
	

def pull_log(svn_url, depth):
	url_dict = svn_url.split('/')
	if svn_url[-1] == '/':
		log_file_name = url_dict[2] + "_" + url_dict[-2] + ".log"
	else:		
		log_file_name = url_dict[2] + "_" + url_dict[-1] + ".log"

	delete_file_if_exists(log_file_name)

	cmd = "svn -v log " + svn_url + " -l " + depth + " >> " + log_file_name
	logging.info('pull cmd: %s', cmd)
	ret = os.system(cmd)
	return log_file_name

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
		r = db.get("select max(version) as max from svn_log")
		max_version = r['max']
	return int(max_version)
		
		
def check_action():
	print "Start check action..."
	
	# load url from database, from module table
	# TODO: Load once, store in mem
	result = db.query("select path from svn_module where level=5 and active=1")
	url_list = []
	for i in result:
		url_list.append(i['path'])

	for svn_url in url_list:
		svn_max = get_last_changed_version(svn_url, "temp_svn.log")
		current_max = get_max_version()

		if int(svn_max) > current_max:
			log_file_name = "svn_history.log"
			delete_file_if_exists(log_file_name)
			cmd = "svn -v log " + svn_url + " -r " + str(current_max+1) + ":" + svn_max + " >> " + log_file_name
			logging.info("svn pull cmd: %s", cmd)
			ret = os.system(cmd)

			m_id = get_module(svn_url)
			assemble(log_file_name, m_id)

def get_module(url):
	# default module name
	url_dict = url.split('/')
	if url[-1] == '/':
		module_name = url_dict[-2] 
		url = url[:-1]
	else:		
		module_name = url_dict[-1]

	logging.debug("module_name: %s", module_name)

	result = db.get("select id from svn_module where name=%s and path=%s", module_name, url)

	if result == None:
		logging.debug("Add a new module '%s' to db", module_name)
		return db.execute("insert into svn_module(name, path, level, active) values(%s, %s, %s, %s)", \
					module_name, url, 5, 1)
	else:
		return result['id']


svn_url = "http://svn.sc4.paypal.com/svn/projects/risk/frameworks/IDI/workflow/branches/idi-DecisionEngine-1-21/"
#svn_url = "http://v8.googlecode.com/svn/trunk"


def schdule():
	threading.Timer(60, schdule).start()
	check_action()

def fresh_pull(depth):
	# invoke pull log at first time
	logging.info('Pull svn log...')

	log_file_name = pull_log(svn_url, depth)

	m_id = get_module(svn_url)
	assemble(log_file_name, m_id)



def main():
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', \
				filename='monitor.log', level=logging.DEBUG)
	logging.info('Started...')

	#fresh_pull("50")

	schdule()
	logging.info('Finished...')

if __name__ == '__main__':
    main()
