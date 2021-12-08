import tornado.web
from py2js.urls import make_routes
from py2js.api import Executor, WrapperHelper

class foobar(Executor):
    
    @WrapperHelper.js_callable
    async def do_something(self, arg1:float, arg2:str)->str: 
        """A useless fxn
        You can call it from the javascript page this way:
        exe = new Executor(ws://<address>:<port>/execute)
        resp = await exe.do_something()
        """

        return "Successfully did nothing"
    


def main():
    # This gives you the following routes
    # /execute -> the websocket
    # /execute/execute.js -> client js to run js_callables.
    # /execute/test.html -> an example implementation of the client side
    url_routes = make_routes(exe_class=foobar)

    app = tornado.web.Application(
            url_routes,
            )

    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


main()
