from .handlers import Websocket, RenderJS, TestPage


def make_routes(exe_class=None):

    if exe_class is None:
        raise TypeError("You must supply a subclass of Executor. See example_app.py")
    ws = Websocket
    ws.set_executor(exe_class)

    url_routes = [ 
        ("/execute", ws),
        ("/execute/execute.js", RenderJS),
        ('/execute/test.html', TestPage),

        ]
    
    return url_routes
