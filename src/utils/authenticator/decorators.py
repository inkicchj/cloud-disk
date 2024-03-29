from functools import wraps
from typing import Callable, List, Optional, Tuple

from sanic.request import Request

from .auth_manager import Auth
from .tokens import Token
from src.utils.cache_store import MemCache
from .exceptions import NoAuthorizationError, InvalidHeaderError, CSRFError, AccessDeniedError, \
    ConfigurationConflictError

try:
    from hmac import compare_digest
except ImportError:  # pragma: no cover

    def compare_digest(a, b):
        if isinstance(a, str):
            a = a.encode("utf-8")
        if isinstance(b, str):
            b = b.encode("utf-8")

        if len(a) != len(b):
            return False

        r = 0
        for x, y in zip(a, b):
            r |= x ^ y

        return not r

jwt_get_function = Callable[[Request], Tuple[str, Optional[str]]]


def _get_raw_token_from_request(request):
    functions: List[jwt_get_function] = []

    for eligible_location in Auth.config.token_location:
        if eligible_location == "header":
            functions.append(_get_raw_token_from_headers)
        if eligible_location == "query":
            functions.append(_get_raw_token_from_query_params)
        if eligible_location == "cookies":
            functions.append(_get_raw_token_from_cookies)

    raw_token = None
    csrf_value = None
    errors = []

    for f in functions:
        try:
            raw_token, csrf_value = f(request)
            break
        except NoAuthorizationError as e:
            errors.append(str(e))

    if not raw_token:
        raise NoAuthorizationError(', '.join(errors))

    return raw_token, csrf_value


def _get_raw_token_from_headers(request):
    header_key = Auth.config.token_header_key
    header_prefix = Auth.config.token_header_prefix

    token_header = request.headers.get(header_key)

    if not token_header:
        raise NoAuthorizationError(f'Missing header "{header_key}"')

    parts: List[str] = token_header.split()

    if parts[0] != header_prefix or len(parts) != 2:
        raise InvalidHeaderError(
            f"Bad {header_key} header. Expected value '{header_prefix} <JWT>'"
        )

    encoded_token: str = parts[1]

    return encoded_token, None


def _get_raw_token_from_query_params(request):
    encoded_token = request.args.get(Auth.config.token_query_param_name)
    if not encoded_token:
        raise NoAuthorizationError(
            f'Missing query parameter "{Auth.config.token_query_param_name}"'
        )

    return encoded_token, None


def _get_raw_token_from_cookies(request: Request):
    cookie_key = Auth.config.token_cookie
    csrf_header_key = Auth.config.csrf_header
    encoded_token = request.cookies.get(cookie_key)
    csrf_value = None

    if not encoded_token:
        raise NoAuthorizationError(f'Missing cookie "{cookie_key}"')

    if Auth.config.csrf_protect and request.method in Auth.config.csrf_request_methods:
        csrf_value = request.headers.get(csrf_header_key)
        if not csrf_value:
            raise CSRFError("Missing CSRF token")

    return encoded_token, csrf_value


def _csrf_check(csrf_from_request, csrf_from_token):
    if not csrf_from_token or not isinstance(csrf_from_token, str):
        raise CSRFError('Can not find valid CSRF data from token')
    if not compare_digest(csrf_from_request, csrf_from_token):
        raise CSRFError('CSRF double submit tokens do not match')


def token_required(
        function=None, *, allow: Optional[list] = None, deny: Optional[list] = None, html: bool = False
):
    def real(fn):
        @wraps(fn)
        async def wrapper(request: Request, *args, **kwargs):

            request.ctx.html = html

            raw_token, csrf_value = _get_raw_token_from_request(request)

            token_obj = await Token(raw_token=raw_token).init()

            if csrf_value:
                _csrf_check(csrf_value, token_obj.csrf)

            if allow and token_obj.role not in allow:
                raise AccessDeniedError("You are not allowed to access here")

            if deny and token_obj.role in deny:
                raise AccessDeniedError("You are not allowed to access here")

            if token_obj.ip and token_obj.ip != request.remote_addr:
                await MemCache.del_data(token_obj.raw_token)
                raise NoAuthorizationError("请重新登录!")

            kwargs["token"] = token_obj
            request.ctx.auth = token_obj
            return await fn(request, *args, **kwargs)

        return wrapper

    if function:
        return real(function)
    else:
        if allow and deny:
            raise ConfigurationConflictError(
                "'deny' and 'allow' 不能同时设置."
            )
        return real
