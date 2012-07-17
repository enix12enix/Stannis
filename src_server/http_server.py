import os.path

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.database

from tornado.options import define, options
from gen_diff import GenDiffer

define("port", default=8001, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
        	(r"/", IndexHandler),
			(r"/genfdiff", GenFullDiffHandler)
        ]
        settings = dict(
            app_title=u"Tornado Search",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            autoescape=None,
			debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class IndexHandler(tornado.web.RequestHandler):

	def get(self):
		self.write("index page loaded...")
		
class GenFullDiffHandler(tornado.web.RequestHandler):

	def get(self):
		svn_url_prefix = self.get_argument("pre", "http://svn.sc4.paypal.com/svn/projects")
		path = self.get_argument("fp", None)
		version = self.get_argument("ver", None)

		# TODO prefix manage in table of database
		print svn_url_prefix
		print path
		print version

		if path[0] != '/':
			path = '/' + path

		df = GenDiffer(svn_url_prefix , path, version, 'f')
		df_html = df.gen_differ()
		if df_html == None:	
			raise tornado.web.HTTPError(500, "could not get code diff...")			
		else:
			self.write(df_html)


if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()