from fs.errors import FSError
from sanic import Blueprint, json, Request, HTTPResponse, redirect
from tortoise.exceptions import BaseORMException
from voluptuous.error import Invalid

from .api import api
from .pages import pages
from .resp import Resp
from ..utils.authenticator.exceptions import NoAuthorizationError, AccessDeniedError, CSRFError, InvalidHeaderError

router = Blueprint.group(api, pages)


@router.exception(FSError)
async def catcher_exception_01(request: Request, exception) -> HTTPResponse:
    return json(Resp.err(50000, None, str(exception)))


@router.exception(NoAuthorizationError)
async def catcher_exception_02(request: Request, exception) -> HTTPResponse:
    if request.ctx.html:
        return redirect("/login")
    return json(Resp.err(50010, None, str(exception)))


@router.exception(AccessDeniedError)
async def catcher_exception_03(request: Request, exception) -> HTTPResponse:
    if request.ctx.html:
        return redirect("/no_permission")
    return json(Resp.err(50011, None, str(exception)))


@router.exception(CSRFError)
async def catcher_exception_04(request: Request, exception) -> HTTPResponse:
    if request.ctx.html:
        return redirect("/login")
    return json(Resp.err(50012, None, str(exception)))


@router.exception(InvalidHeaderError)
async def catcher_exception_05(request: Request, exception) -> HTTPResponse:
    if request.ctx.html:
        return redirect("/login")
    return json(Resp.err(50013, None, str(exception)))


@router.exception(Invalid)
async def catcher_exception_05(request: Request, exception) -> HTTPResponse:
    return json(Resp.err(425, None, str(exception)))


@api.exception(TypeError, BaseORMException)
async def catcher_exception_02(request: Request, exception) -> HTTPResponse:
    return json(Resp.err(430, None, "服务器发生了一点故障"))
