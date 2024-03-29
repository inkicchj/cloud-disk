from functools import wraps
from inspect import isawaitable
from typing import Callable, TypeVar, Union, Tuple, Any, Optional
from sanic_ext.exceptions import InitError
from sanic_ext.utils.extraction import extract_request
from sanic import json as sjson
from voluptuous import Schema
from src.routers.resp import Resp
from voluptuous.error import MultipleInvalid

T = TypeVar("T")


def parse_data(schema: Schema, obj: Optional[Any], data: dict):
    if obj:
        r = schema(obj(**data))
    else:
        r = schema(data)
    return r


def validate(
        json: Union[Tuple[Schema, Optional[Any]], None] = None,
        form: Union[Tuple[Schema, Optional[Any]], None] = None,
        query: Union[Tuple[Schema, Optional[Any]], None] = None,
        json_argument: str = "body",
        form_argument: str = "form",
        query_argument: str = "query",
) -> Callable[[T], T]:

    if json and form:
        raise InitError("不能同时定义form和json验证")

    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):

            request = extract_request(*args)

            param = {
                "json": request.json or {},
                "form": request.form or {},
                "query": request.args or {}
            }

            if json:
                r = parse_data(json[0], json[1], param['json'])
                kwargs[json_argument] = r
            elif form:
                r = parse_data(form[0], form[1], param['form'])
                kwargs[form_argument] = r
            if query:
                r = parse_data(query[0], query[1], param['query'])
                kwargs[query_argument] = r
            retval = f(*args, **kwargs)
            if isawaitable(retval):
                retval = await retval
            return retval

        return decorated_function

    return decorator
