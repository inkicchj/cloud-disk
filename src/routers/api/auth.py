import shortuuid
from passlib.hash import pbkdf2_sha256
from sanic import Request, json, Blueprint

from src.model.user import User, Role
from src.routers.resp import Resp
from src.schemas.auth import login_schema, LoginSchema
from src.schemas.auth import update_name_schema, UpdateNameSchema
from src.schemas.auth import update_pwd_schema, UpdatePWDSchema
# 数据校验
from src.schemas.validator import validate
from src.utils.authenticator import Auth, token_required
from src.utils.authenticator.tokens import Token
from src.utils.cache_store import MemCache

auth_b = Blueprint("Auth", url_prefix="/auth")


# 登录
@auth_b.post("/login")
@validate(json=(login_schema, LoginSchema))
async def login(request: Request, body: LoginSchema):
    user = await User.get_or_none(name=body.name).values()
    if not user:
        return json(Resp.err_msg(f"用户还未注册: {body.name}"))
    if not pbkdf2_sha256.verify(body.password, user["password"]):
        return json(Resp.err_msg(f"用户密码错误: {body.name}"))

    del user["password"]
    csrf = shortuuid.random(30)
    token = await Auth.create_access_token(identity=user["id"], role=user["role"], csrf=csrf)
    response = json(Resp.ok_data({"token": token, "csrf": csrf}))
    response.add_cookie(key="token", value=token, httponly=True)
    response.add_cookie(key="csrf", value=csrf, httponly=False)
    return response


# 登出
@auth_b.post("/logout")
@token_required(allow=[Role.Admin])
async def logout(request: Request, token: Token):
    await token.revoke()
    return json(Resp.ok_msg("登出成功"))


# 用户信息
@auth_b.post("/me")
@token_required(allow=[Role.Admin])
async def info(request: Request, token: Token):
    user = await User.get_or_none(id=token.identity).values()
    if not user:
        return json(Resp.err_msg("用户不存在"))
    del user["password"]
    return json(Resp.ok_data(user))


# 更新用户名
@auth_b.post("/update_name")
@token_required(allow=[Role.Admin])
@validate(json=(update_name_schema, UpdateNameSchema))
async def update_name(request: Request, body: UpdateNameSchema, token):
    has_name = await User.get_or_none(name=body.name, id__not_in=[token.identity])
    if has_name:
        return json(Resp.err_msg(f"用户名称已存在: {body.name}"))
    await User.filter(id=token.identity).update(name=body.name)
    return json(Resp.ok_msg("更改名称成功"))


# 更新密码
@auth_b.post("/update_pwd")
@token_required(allow=[Role.Admin])
@validate(json=(update_pwd_schema, UpdatePWDSchema))
async def update_pwd(request: Request, body: UpdatePWDSchema, token: Token):
    u_ = await User.get(id=token.identity)
    if not pbkdf2_sha256.verify(body.old_pwd, u_.password):
        return json(Resp.err_msg("原密码错误"))
    if body.new_pwd == body.old_pwd:
        return json(Resp.err_msg("新密码不能和旧密码相等"))

    hash_password = pbkdf2_sha256.using(
        rounds=10, salt=u_.salt.encode("utf-8")
    ).hash(body.new_pwd)

    await User.filter(id=token.identity).update(password=hash_password)
    await token.revoke()
    csrf = shortuuid.random(30)
    new_token = await Auth.create_access_token(identity=token.identity, role=token.role, csrf=csrf)
    response = json(Resp.ok_data({"token": token, "csrf": csrf}))
    response.add_cookie(key="token", value=new_token, httponly=True)
    response.add_cookie(key="csrf", value=csrf, httponly=False)
    return response

