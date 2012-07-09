# -*- coding: utf-8 -*-
import re
import os
import logging
import subprocess

from codediff import CodeDiffer
 
split_line = "------------------------------------------------------------------------\n"
old_file = "old"
new_file = "new"
temp_log = "templog"
temp_diff = "temp_diff.html"


def delete_file_if_exists(file):
	if os.path.isfile(file):
		os.remove(file)
		logging.info('delete file: %s', file)

def pull_temp_log(file_url, log, depth): 
	delete_file_if_exists(log)
	if depth == None:
		logging.debug('pull full log versions: %s', file_url)
		pull_log_cmd = "svn log -q " + file_url + " >> " + log
	else:
		pull_log_cmd = "svn log -q " + file_url + " -l " + depth + " >> " + log # limit to eight entries
	logging.info('execute cmd: %s', pull_log_cmd)
	# ret = os.system(pull_log_cmd)
	# subprocess --> get return code
	proc = subprocess.Popen(pull_log_cmd, shell=True)
	return_code = proc.wait() # wait for process to finish so we can get the return code

	return return_code

def get_file_versions(log_file_name):
	log_file = open(log_file_name)
	logging.info('get log_file version list...')

	checkin = []
	for line in log_file:
		if line <> split_line:
			version = (line.split('|'))[0].strip()[1:]
			checkin.append(version)
		
	log_file.close()
	return checkin

def get_previous_version(version, list):
	for i in range(len(list)-1):
		if version == list[i]:
			return list[i+1]
			
	return None # not found
	
def get_file_by_version(version, file_url, output):
	delete_file_if_exists(output)
	
	# svn cat -r version svn_url > file_name
	co_cmd = "svn cat -r " + version + " " + file_url + " >> " + output
	logging.info('execute cmd: %s', co_cmd)
	
	ret = os.system(co_cmd)	

def filter_html(diff_file):
	start_tag = "<table"
	end_tag = '''    </table>\n'''

	html = ""
	copy_enable = False
	for line in diff_file:
		if copy_enable:
			html = html + line
		elif line.startswith(start_tag, 4, 10):	
			copy_enable = True
			html = line
		
		if line == end_tag:
			return html
			
	logging.warning('No end tag founded ! filter failed -_-! ')
	
	
class GenDiffer:
	def __init__(self, file_svn_url, version):
			self.file_svn_url = file_svn_url
			self.version = version

	def get_code(self):
		get_file_by_version(self.version, self.file_svn_url, new_file)
		file = open(new_file)
		str=''
		for l in file:
			str += l
		file.close()
		return str

	def gen_differ(self):
		logging.info('pull svn log...')		
		ret_code = pull_temp_log(self.file_svn_url, temp_log, '15')

		if ret_code == 1:
			logging.warning('pull log failed... path: %s', self.file_svn_url)
			return None

		ver_list = get_file_versions(temp_log)

		logging.debug('self.version: %s', self.version)
		logging.debug('ver_list: %s', ver_list)
		pre_version = get_previous_version(self.version, ver_list)
		
		# repull full versions
		if pre_version == None:
			pull_temp_log(self.file_svn_url, temp_log, None)
			ver_list = get_file_versions(temp_log)
			pre_version = get_previous_version(self.version, ver_list)
			if pre_version == None:
				logging.warning('Final version can not found: %s', self.file_svn_url)
				return None		
		
		logging.info('find previous version: %s', pre_version)
		
		get_file_by_version(self.version, self.file_svn_url, new_file)
		get_file_by_version(pre_version, self.file_svn_url, old_file)

		logging.info('make diff ...')
		delete_file_if_exists(temp_diff)
		try: 
			differ = CodeDiffer(old_file, new_file, temp_diff)
			differ.make_diff()
		except CodeDifferError, e:
			logging.error('CodeDiffer error: %s', e)
			
		logging.info('filter diff html ...')
		diff = open(temp_diff)
		diff_html = filter_html(diff)
		diff.close()
		
		logging.info('filter html done...')
		return diff_html