# -*- coding: utf-8 -*-
import re
import os
import logging
import subprocess

from codediff import CodeDiffer
from codediff import CodeDifferError

split_line = "------------------------------------------------------------------------\n"

temp_log = "templog.log"
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
	
def get_file_by_version(svn_url_prefix, path, version):
	i = -1
	while -i < len(path):
		if path[i] == '/' and path[i:].find('.') <> -1:
			dir_path = create_dir(path[:i+1] + version)
						
			filename =path[i+1:] 
			logging.debug("filename = " + filename)

			local_path = dir_path + "/" + filename
			if os.path.isfile(local_path):
				logging.debug("file existed: " + filename)
				return local_path

			# checkout specfic version: svn cat -r version svn_url > file_name
			co_cmd = "svn cat -r " + version + " " + svn_url_prefix + path + " >> " + local_path
			logging.debug("execute cmd: " + co_cmd)
			ret = os.system(co_cmd)	
			return local_path

		i = i - 1
	return None

def create_dir(dir_path):	
	if dir_path[0] == "/":
		dir_path = dir_path[1:]

	dir_path = "src_server/src/" + dir_path
		
	if os.path.isdir(dir_path):
		logging.debug("existing dir..." + dir_path) 
	else:
		ret = os.makedirs(dir_path)
		logging.debug("create dir: " + dir_path)
	return dir_path


# To be removed
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
	def __init__(self, svn_url_prefix, svn_file_url, version, diff_type='u'):
			self.svn_url_prefix = svn_url_prefix
			self.svn_file_url = svn_file_url
			self.version = version
			self.file_svn_url = svn_url_prefix + svn_file_url
			self.diff_type = diff_type
			
	# TODO version param ?
	def get_code(self):
		code_path = get_file_by_version(self.svn_url_prefix, self.svn_file_url, self.version)

		# assume not None 
		file = open(code_path)
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
		
		new_code_path = get_file_by_version(self.svn_url_prefix, self.svn_file_url, self.version)
		old_code_path = get_file_by_version(self.svn_url_prefix, self.svn_file_url, pre_version)

		logging.info('make diff ...')
		delete_file_if_exists(temp_diff)
		try: 
			differ = CodeDiffer(old_code_path, new_code_path, temp_diff, self.diff_type)
			differ.make_diff()
		except CodeDifferError, e:
			logging.error('CodeDiffer error: %s', e)
			return None

		logging.info('filter diff html ...')

		diff = open(temp_diff)
		df_html=''
		for l in diff:
			df_html += l
		diff.close()
	

		logging.info('filter html done...')
		return df_html