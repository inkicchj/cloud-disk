from voluptuous import Schema, All, Strip, Length, Object, Required, Match
from voluptuous.error import Invalid

pwd_rule = All(
    str,
    Strip,
    Length(min=6, max=20, msg="密码长度为6~20"),
    Match(pattern=r"^(?![0-9]+$)(?![a-zA-Z]+$)[a-zA-Z0-9]{1,50}$", msg="密码需包含数字和字母")
)

name_rule = All(
    str,
    Strip,
    Length(min=2, max=20, msg="名称长度为2~20")
)


class LoginSchema:
    def __init__(self, name=None, password=None):
        self.name = name
        self.password = password


login_schema = Schema(Object({
    Required("name", "名称不能为空"): name_rule,
    Required("password", "密码不能为空"): pwd_rule
}, cls=LoginSchema))


class UpdateNameSchema:
    def __init__(self, name=None):
        self.name = name


update_name_schema = Schema(
    Object(
        {
            Required("name", "名称不能为空"): name_rule
        },
        cls=UpdateNameSchema
    )
)


class UpdatePWDSchema:
    def __init__(self, new_pwd=None, old_pwd=None):
        self.new_pwd = new_pwd
        self.old_pwd = old_pwd


def passwords_not_match(a: UpdatePWDSchema):
    if a.new_pwd == a.old_pwd:
        raise Invalid('新密码不能和旧密码相同')
    return a


update_pwd_schema = Schema(
    All(
        Object(
            {
                Required("new_pwd", msg="新密码不能为空"): pwd_rule,
                Required("old_pwd", msg="原密码不能为空"): pwd_rule
            },
            cls=UpdatePWDSchema
        ),
        passwords_not_match
    )
)
