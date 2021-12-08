# -*- coding: utf-8 -*-

import json
import logging
import datetime
import pandas as pd
import numpy as np
import logging
from dateutil.parser import parse
from typing import get_type_hints
from functools import wraps
from inspect import signature,_empty
import re
import pytz
from pathlib import Path
import time
import pickle
import uuid
import fnmatch
import os
import asyncio


class WrapperHelper:
    registry = None
    ldframe = None
    cache_index = None
    cache = None
    cache_path = Path(__file__).parent.parent/'cache'
    _cacheable = []
   

    @classmethod
    def js_callable(cls, fxn):
        print(fxn)
        if cls.registry is None:
            cls.registry = []
        cls.registry.append(fxn)

        @wraps(fxn)
        async def wrapper(self, **kwargs):
            logging.debug(f"Validating {fxn}")
            type_hints = get_type_hints(fxn)
            cls.init_cache()
            if "return" in type_hints:
                rtn = type_hints.pop("return")

            for name, Type in type_hints.items():
                if name in kwargs:
                    print(name, kwargs[name])
                    kwargs[name] = cls.convert(kwargs[name], Type)

            cacheit = fxn.__name__ in cls._cacheable
            logging.debug(f"Cacheable {cls._cacheable}")
            if cacheit:
                logging.debug(f"Cacheable {fxn}")
                resp = cls.lookup_cache(fxn, kwargs)
                if isinstance(resp, pd.DataFrame):
                        cls.ldframe = resp
            else :
                resp = None

            if resp is None:
                try:
                    logging.debug(f"Calling fxn {fxn}")
                    resp = await fxn(self, **kwargs)
                    if isinstance(resp, pd.DataFrame):
                        cls.ldframe = resp
                    if cacheit:
                        cls.write_cache(fxn, kwargs, resp)

                except Exception as error:
                    logging.debug(f"Exception in function: {error}")
                    resp = {"execution_error": error}


            
            return resp

        return wrapper

    @classmethod
    def cacheable(cls, fxn):
        print(f"cacheableizing {fxn}")
        if cls._cacheable is None:
            cls._cacheable = []

        cls._cacheable.append(fxn.__name__)
        logging.debug(f"Cacheable: {cls._cacheable}")
        return fxn
        

    @classmethod 
    def init_cache(cls):
        if cls.cache_index is None:
            if (cls.cache_path/'cache_index').exists():
                with (cls.cache_path/'cache_index').open('rb') as fd:
                    logging.debug(f"fd is {fd}")
                    cls.cache_index = pickle.load(fd)


    @classmethod
    def lookup_cache(cls, fxn, kwargs):

        logging.debug(f"looking up cache {cls.cache_index}")

        if cls.cache_index is None:
            if (cls.cache_path/'cache_index').exists():
                with (cls.cache_path/'cache_index').open('rb') as fd:
                    logging.debug(f"fd is {fd}")
                    cls.cache_index = pickle.load(fd)
            else:
                with (cls.cache_path/'cache_index').open('wb') as fd:
                    cls.cache_index = []
                    pickle.dump(cls.cache_index, fd)
            return None

        resp = None
        for ii, (c_fxn, c_kwargs, c_ts, cache) in enumerate(cls.cache_index):
            
            if fxn.__name__ == c_fxn and kwargs == c_kwargs:
                logging.debug(f"Cache hit {fxn}, {kwargs}")
                with (cls.cache_path/cache).open('rb') as cache_fd:
                    resp = pickle.load(cache_fd)
                break

        if resp is not None:
            awhile_ago = old = datetime.datetime.now() -\
                    datetime.timedelta(hours=8)
            if c_ts < awhile_ago:
                cls.cache_index.pop(ii)
                with (cls.cache_path/'cache_index').open('wb') as fd:
                    pickle.dump(cls.cache_index, fd)
                (cls.cache_path/cache).unlink()
                resp = None

        return resp


    @classmethod 
    def write_cache(cls, fxn, kwargs, resp):

        for c_fxn, c_kwargs, _, __ in cls.cache_index:
            if c_fxn == fxn and c_kwargs == kwargs:
                raise RuntimeError(f"This Cache exists why are we attempting to\
                        write {kwargs} {fxn}")

        c_name = "cache_"+str(uuid.uuid4())[:4]+".pkl"
        c_path = cls.cache_path/c_name
        with c_path.open('wb') as cache_fd:
            logging.debug(f"Caching {fxn}, {kwargs}")
            pickle.dump(resp, cache_fd)

        idx = (fxn.__name__, kwargs, datetime.datetime.now(), c_name)
        cls.cache_index.append(idx)
        with (cls.cache_path/'cache_index').open('wb') as fd:
            pickle.dump(cls.cache_index, fd)



    @classmethod
    def _datetime(cls, arg):

        
        if type(arg) in (float, int):
            return datetime.fromtimestamp(arg)

        elif type(arg) == str:
            regex_int = re.compile(r"\d{10,19}")
            regex_float = re.compile(r"\d{10,11}\.\d{1,10}")

            if regex_int.match(arg):
                return datetime.datetime(int(arg))

            elif regex_float.match(arg):
                return datetime.datetime(float(arg))

            else:
                return parse(arg)

        elif type(arg) == datetime.datetime:
            return arg
    
        raise TypeError(f"Could not convert {arg} to datetime.datetime")


            
    @classmethod
    def _date(cls, arg):
        
            return parse(arg)

    @classmethod
    def convert(cls, arg, Type): 
        type_list = {
            datetime.datetime:cls._datetime,
            datetime.date:cls._date,
            }

        if Type in type_list:
            return type_list[Type](arg)
        else:
            return Type(arg)

    @classmethod
    def store_dataframe(cls, dframe):
        cls.dframe = dframe


class Executor:

    @WrapperHelper.js_callable
    async def show(self):

        resp = {}
        for fxn in WrapperHelper.registry:

            type_hints = get_type_hints(fxn)

            resp[fxn.__name__] = {}
            if "return" in type_hints:
                resp[fxn.__name__]["return"] = type_hints.pop("return")
            else:
                resp[fxn.__name__]["return"] = None
            
            resp[fxn.__name__]['args'] = []
            for name, param in signature(fxn).parameters.items():
                if name == "self":
                    continue
                arg={"name":name}
                
                if param.default != _empty:
                    arg.update(default=param.default)

                if name in type_hints:
                    arg.update(type_hint=str(type_hints[name]))


                resp[fxn.__name__]['args'].append(arg)

            resp[fxn.__name__]["description"] = fxn.__doc__

        return resp


    @WrapperHelper.js_callable
    async def test(self):
        """
        A test function
        """
        return {"test":"successfull"}



    @WrapperHelper.js_callable
    async def get_cached(self)->dict:
        logging.debug(WrapperHelper.cache_index)
        return {'cache':WrapperHelper.cache_index}


    




