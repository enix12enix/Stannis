import os.path

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.database

from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="test_pull", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default="mysql", help="database password")

define("page_size", default="10", help="result set page size")
PAGE_ITEM=10


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
			(r"/search", SearchHandler),
			(r"/diff", DiffHandler),
			(r"/timeline", TimelineHandler)
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
		# result = self.db.get("select count(*) as count from search_history")
		# , search_count=result['count']
		self.render('index.html')
		
		

class Log(object):
	entries = []	

# TODO write a generic function for search
def search(*args):
	pass


		
class SearchHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db

	# TODO 
	def track(self, ip, acct_name):
		id = self.db.get("select id from search_history where ip=%s and acct_name=%s", ip, acct_name)
		if id:
			self.db.execute("update search_history set ")
		self.db.execute("insert into search_history(ip, content) values(%s, %s)", ip, acct_name)
		
	def get(self):
		input = self.get_argument("input", None)
		if input == None:
			self.redirect('/timeline')
			#raise tornado.web.HTTPError(500, "Please input user account name !")
		elif input.find('.') != -1:
			pass # file type
		elif input.find('@') != -1:
			pass # email address
		else:
			self.search_acct_name(input)
		

	def search_acct_name(self, acct_name):
		offset = int(self.get_argument("offset", 1))

			
		# tracking
		self.db.execute("insert into search_history(ip, content) values(%s, %s)", self.request.remote_ip, acct_name)
		
		result_amount = self.db.get("select count(*) as count from svn_log where acct_name=%s", acct_name)
		page_size = result_amount['count']/PAGE_ITEM
		if result_amount['count'] % PAGE_ITEM != 0:
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
		
		self.render("search.html", acct_name=acct_name, result_amount=result_amount['count'], page_size=page_size, \
				actived_page=offset, entries=check_in_entries, change_path_set=change_path_set)

class TimelineHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db

	def get(self):
		offset = int(self.get_argument("offset", 1))
		mid = int(self.get_argument("mid", 6))
		
		result_amount = self.db.get("select count(*) as count from svn_log")
		page_size = result_amount['count']/PAGE_ITEM
		if result_amount['count'] % PAGE_ITEM != 0:
			page_size = page_size +1
		
		check_in_entries = self.db.query("select * from svn_log ORDER BY date_time DESC LIMIT %s, 10", \
				(offset -1)*PAGE_ITEM)
	
		change_path_set = []

		for entry in check_in_entries:			
			#change_path_entries = self.db.query("select * from svn_change_path where f_id=%s", entry.id)			
			change_path_entries = self.db.query( \
			"select *,(select di.id from svn_diffs di where di.f_cp_id = cp.id) as diff_id from svn_change_path cp where cp.f_id=%s", \
			entry.id)
			if len(change_path_entries) != 0:
				change_path_set.append(change_path_entries)
		
		print '------------------'
		print mid
		print range(mid-5, mid+5)
			#index_range=range(mid-5, mid+5)

		self.render("timeline.html", result_amount=result_amount['count'], mid=mid, \
			actived_page=offset, entries=check_in_entries, change_path_set=change_path_set)


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
		
		print cp_result['path']
		title = cp_result['path'].split('/')[-1]
		print title
		self.render("diff.html", title=title, diff=di_result['diff'])
	
class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)
		

if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()