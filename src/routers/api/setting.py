from sanic import Blueprint, Request, json

from config import AppConfig
from src.model.user import Role
from src.routers.resp import Resp
from src.utils.authenticator import token_required
from src.schemas.setting import update_setting
from src.schemas.validator import validate

setting_b = Blueprint("Setting", url_prefix="/setting")


@setting_b.post("/all")
async def get_all_setting(request: Request, token):
    return json(Resp.ok_data(AppConfig.config.model_dump()))


@setting_b.post("/edit")
@token_required(allow=[Role.Admin])
@validate(json=(update_setting, None))
async def edit_setting(request: Request, body: dict, token):
    AppConfig.set_config(body)
    return json(Resp.ok_msg("更改配置成功"))
