from sanic import Request, Blueprint

from config import AppConfig
from src.model.user import Role
from src.utils.authenticator import token_required
from src.utils.authenticator.tokens import Token
from src.utils.jinja_extend import render

pages = Blueprint("Pages")


@pages.on_request
async def inject_config(request: Request):
    request.ctx.config = AppConfig.config


@pages.get("/")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-files.html", render_as="html")
async def index(request: Request, token: Token):
    return {}


@pages.get("/file")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-file.html", render_as="html")
async def file(request: Request, token: Token):
    return {}


@pages.get("/video")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-video.html", render_as="html")
async def video_file(request: Request, token: Token):
    return {}


@pages.get("/image")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-image.html", render_as="html")
async def image_file(request: Request, token: Token):
    return {}


@pages.get("/audio")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-audio.html", render_as="html")
async def audio_file(request: Request, token: Token):
    return {}


@pages.get("/text")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-text.html", render_as="html")
async def text_file(request: Request, token: Token):
    return {}


@pages.get("/office")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-office.html", render_as="html")
async def office_file(request: Request, token: Token):
    return {}


@pages.get("/m/storage")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-storages.html", render_as="html")
async def m_storage(request: Request, token: Token):
    return {}


@pages.get("/m/storage/add")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-storages-add.html", render_as="html")
async def m_storage_add(request: Request, token: Token):
    return {}


@pages.get("/m/storage/edit/<ident:int>")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-storages-edit.html", render_as="html")
async def m_storage_edit(request: Request, ident: int, token: Token):
    return {}


@pages.get("/m/share")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-shares.html", render_as="html")
async def m_share(request: Request, token: Token):
    return {}


@pages.get("/share/<mark:str>")
@render("ui/page-share-files.html", render_as="html")
async def view_share(request: Request, mark):
    return {}


@pages.get("/m/setting")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-setting.html", render_as="html")
async def m_setting(request: Request, token: Token):
    return {}


@pages.get("/m/auth")
@token_required(allow=[Role.Admin], html=True)
@render("ui/page-auth.html", render_as="html")
async def m_auth(request: Request, token: Token):
    return {}


@pages.get("/login")
@render("ui/login.html", render_as="html")
async def login(request: Request):
    return {}


@pages.get("/no_permission")
async def no_permission(request: Request):
    return {}
