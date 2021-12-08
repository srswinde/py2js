import tornado.web
import tornado.websocket
import json
import logging
from .api import Executor
from .js import javascript, test_page

try:
    import pandas as pd
    haspandas = True

except ImportError:
    haspandas = False



class RenderJS(tornado.web.RequestHandler):

     def get(self):

         self.write(javascript)


class TestPage(tornado.web.RequestHandler):

     def get(self):

         self.write(test_page)


class Websocket(tornado.websocket.WebSocketHandler):
    """
    Websocket endpoint /execute
    """
    executor = Executor

    async def open(self, *args, **kwargs):
        logging.debug(f"Open {args}")

    async def test(self, **args):
        return {"test":"successful"}

    def check_origin(self, origin):

        return True


    async def on_message(self, msg):
        """
        Name: on_message
        Description:
            Websocket message handler. Msg is assumed
            to be in json format. 
        """
        exe = self.executor()
        resp = {}
        try:
            data = json.loads(msg)
        except Exception as error:
            resp["json_error"] = error
            self.write_message(str(resp))
            raise

        
        logging.debug("MESSAGE")
        logging.debug(data["cmd"])
        rtn = await exe.__getattribute__(data["cmd"])(**data['args'])
        
        if haspandas:
            if isinstance(rtn, pd.DataFrame):
                if isinstance(rtn.index, pd.DatetimeIndex):
                    rtn['dtindex'] = rtn.index
                    rtn.index = rtn.index.astype(int)

                rtn = rtn.to_dict()

        logging.debug("Response collected packaging")
        resp.update({"return": rtn})
                
        try:
            self.write_message(json.dumps(resp, default=str))
        except Exception as error:
            resp["write_error"] = error
            self.write_message(json.dumps({"return":str(error)}, default=str))
            raise 

        if type(rtn) == dict:
            if "execution_error" in rtn:
                pass
                #raise rtn["execution_error"]    
        elif rtn is None:
            logging.debug(f"{data['cmd']} returned\
                    None!")


    def get_executor(self):
        return self.executor()

    @classmethod
    def set_executor(cls, executor):
        cls.executor = executor
