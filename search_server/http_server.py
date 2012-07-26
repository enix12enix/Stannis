import os.path

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.database
import tornado.gen
import tornado.httpclient

from tornado.options import define, options
 

define("port", default=8000, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="stannis", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default="mysql", help="database password")

define("page_size", default="10", help="result set page size")
PAGE_ITEM = 10


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
			(r"/search", SearchHandler),
			(r"/diff", DiffHandler),
			(r"/timeline", TimelineHandler),
			(r"/fulldiff", GetFullDiffHandler)
        ]
        settings = dict(
            app_title=u"Tornado Search",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Entry": EntryModule},
            autoescape=None,
			debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)
        
class IndexHandler(tornado.web.RequestHandler):		
	@property
	def db(self):
		return self.application.db
		
	def get(self):	
		# load module from db
		# TODO, save in session
		# level 4
		l4_result = self.db.query("select id, name from svn_module where level = 4 and active = 1")

		# branch level = 5
		l5_result = self.db.query("select name from svn_module where level = 5 and active = 1 group by name")

		self.render('index.html', l5=l5_result, l4=l4_result)
		
		
# ?
class Log(object):
	entries = []	

# TODO write a generic function for search
def search(*args):
	pass

# TODO async
def track(req, content):
	self.db.execute("insert into search_history(ip, content) values(%s, %s)", req.remote_ip, content)




class SearchHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db
	
	# TODO
	def on_finish(self):
		pass

	def get(self):
		# param =''
		# l4 = self.get_argument("l4", None)

		# if l4 != None:
		# 	param += 'l4r=' +l4
		l5 = self.get_argument("l5", None)
		param = ''
		if l5 != None:
			param ='?l5r=' + l5

		input = self.get_argument("input", None)
		if input == None:
			self.redirect('/timeline' + param)
			#raise tornado.web.HTTPError(500, "Please input user account name !")
		elif input.find('.') != -1:
			# TODO
			# file type
			self.write("TO BE IMPLMENTED...")
		elif input.find('@') != -1:
			# TODO
			# email address
			self.write("TO BE IMPLMENTED...")
		else:
			self.search_acct_name(input)
		

	def search_acct_name(self, acct_name):
		offset = int(self.get_argument("offset", 1))
			
		# TODO tracking
		self.db.execute("insert into search_history(ip, content) values(%s, %s)", self.request.remote_ip, acct_name)
		
		result_size = self.db.get("select count(*) as count from svn_log where acct_name=%s", acct_name)
		page_size = result_size['count']/PAGE_ITEM
		if result_size['count'] % PAGE_ITEM != 0:
			page_size = page_size +1
		
		check_in_entries = self.db.query("select * from svn_log where acct_name=%s ORDER BY date_time DESC LIMIT %s, 10", \
				acct_name, (offset -1)*PAGE_ITEM)
	
		change_path_set = []

		for entry in check_in_entries:			
			#change_path_entries = self.db.query("select * from svn_change_path where f_id=%s", entry.id)			
			change_path_entries = self.db.query( \
			"select *,(select di.id from svn_diffs di where di.f_cp_id = cp.id) as diff_id from svn_change_path cp where cp.f_id=%s", \
			entry.id)
			if len(change_path_entries) != 0:
				change_path_set.append(change_path_entries)
		
		# TODO
		msg = None
		if len(check_in_entries) != 0:
			msg = "No records found!"
		
		self.render("search.html", acct_name=acct_name, result_size=result_size['count'], page_size=page_size, \
				actived_page=offset, entries=check_in_entries, change_path_set=change_path_set)

class TimelineHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db

	def get(self):
		offset = int(self.get_argument("offset", 1))
		start_index = int(self.get_argument("start", 1))
		level5 = self.get_argument("l5r", None)
		# level4 = self.get_argument("l4r", None)
		rs = self.get_argument("rs", None)

		if rs == None:
			if level5 == None:
				result = self.db.get("select count(*) as count from svn_log")
			else:
			 	sql = "select count(*) as count from svn_log where m_id in (select id from svn_module where name=%s)"
				result = self.db.get(sql, level5)
			
			result_size = int(result['count'])
		else: 
			result_size = int(rs)


		page_size = result_size/PAGE_ITEM
		if result_size % PAGE_ITEM != 0:
			page_size = page_size +1

		if offset -5 >= 1:
			start_index = offset - 5 

		if 	start_index + 10 < page_size:
			end_index = start_index + 10
		else:
			end_index = page_size
		
		if level5 == None:
			check_in_entries = self.db.query("select * from svn_log ORDER BY date_time DESC LIMIT %s, 10", (offset -1)*PAGE_ITEM)
		else:
			sql = "select * from svn_log where m_id in (select id from svn_module where name=%s) ORDER BY date_time DESC LIMIT %s, 10"
			check_in_entries = self.db.query(sql, level5, (offset -1)*PAGE_ITEM)

		change_path_set = []

		for entry in check_in_entries:			
			#change_path_entries = self.db.query("select * from svn_change_path where f_id=%s", entry.id)			
			change_path_entries = self.db.query( \
			"select *,(select di.id from svn_diffs di where di.f_cp_id = cp.id) as diff_id from svn_change_path cp where cp.f_id=%s", \
			entry.id)
			if len(change_path_entries) != 0:
				change_path_set.append(change_path_entries)

		# level 4
		#l4_result = self.db.query("select id, name from svn_module where level = 4 and active = 1")

		# branch level = 5
		l5_result = self.db.query("select name from svn_module where level = 5 and active = 1 group by name")

		self.render("timeline.html", result_size=result_size, start_index=start_index, end_index=end_index, \
			actived_page=offset, entries=check_in_entries, change_path_set=change_path_set, l5r=l5_result, l5=level5)


class DiffHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db
		
	def get(self):
		cp_id = self.get_argument("cp_id", None)
		# validation
		if cp_id == None:
			raise tornado.web.HTTPError(500, "parameter cp.id needed!")
		
		cp_result = self.db.get("select path from svn_change_path where id=%s", cp_id)
		di_result = self.db.get("select diff from svn_diffs where f_cp_id=%s", cp_id)
		if di_result == None:
			raise tornado.web.HTTPError(500, "diff record not found!")
		
		# print cp_result['path']
		title = cp_result['path'].split('/')[-1]
		# print title
		self.render("diff.html", title=title, diff=di_result['diff'])
	
class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)
		

# TODO
class GetFullDiffHandler(tornado.web.RequestHandler):

	@tornado.web.asynchronous
	def get(self):
		#svn_url_prefix = self.get_argument("pre", "http://svn.sc4.paypal.com/svn/projects")
		path = self.get_argument("fp", None)
		version = self.get_argument("ver", None)

		print "---------------"
		print path
		print version

		http_client = tornado.httpclient.AsyncHTTPClient()
		response = yield tornado.gen.Task(http_client.fetch, "http://localhost:8001/genfdiff?fp="+path+"&ver="+version)
		self.write(response)
        #self.render("template.html")


if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()