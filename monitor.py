# -*- coding: utf-8 -*-
import re
import os
import logging
from datetime import datetime

from gen_diff import GenDiffer

import tornado.database

svn_url_prefix = "http://svn.sc4.paypal.com/svn/projects"
#svn_url_prefix = "http://v8.googlecode.com/svn"
split_line = "------------------------------------------------------------------------\n"
db = tornado.database.Connection("localhost:3306", "test_pull", "root", "mysql")

#svn_url = "http://v8.googlecode.com/svn/trunk/sc/"

def assemble(log_file):
	checkin = []
	for line in log_file:
		if line == split_line:
			logging.debug('split started...')
			if len(checkin) <> 0:
				insert_record(checkin)			
			checkin = []
		else:
			checkin.append(line)


def insert_record(record):	
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
		svn_log_id = db.execute("insert into svn_log(version, acct_name, date_time, comments) values(%s, %s, %s, %s)",\
			 version, acct_name, date_time, comments)
		
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
					gen_diff(change_path[0], change_path[1], version, svn_cp_id)
	

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


	
def gen_diff(action, path, version, cp_id):
	if action == "A":
		if path[-1] <> "/":
			logging.info('code path: %s', path)
			df = GenDiffer(svn_url_prefix + path, version)
			code = df.get_code()

			db.execute("insert into svn_diffs(f_cp_id, diff) values(%s, %s)", cp_id, code)
			logging.debug('insert added record to db...')

	elif action == "M":
		# not directory
		if path[-1] <> "/":
			logging.info('code path: %s', path)
			df = GenDiffer(svn_url_prefix + path, version)
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

		
def pull_log(svn_url, log_file_name):
	delete_file_if_exists(log_file_name)
	cmd = "svn -v log -q " + svn_url + " -l 100 >> " + log_file_name
	ret = os.system(cmd)

		
log_file_name = "idi_log2.txt" 
svn_url_old = "http://svn.sc4.paypal.com/svn/projects/risk/frameworks/IDI/analytics/branches/ts-decision-kernel-1-28"
svn_url="http://svn.sc4.paypal.com/svn/projects/risk/frameworks/IDI/eventrouter/branches/ts-decision-kernel-1-28"


def main():
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='monitor.log', level=logging.DEBUG)
	logging.info('Started...')
	
	#logging.info('Pull svn log...')
	#pull_log(svn_url, log_file_name)

	#file = open(log_file_name)
	file = open('ts-decision-kernel-1-28_svninfo.txt')
	assemble(file)
	file.close()
	logging.info('Finished...')

if __name__ == '__main__':
    main()
	