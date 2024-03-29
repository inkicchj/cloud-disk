
from datetime import datetime, timedelta
from contextlib import contextmanager

import shortuuid
from flatten_dict import flatten
from typing import Any, Optional
from .config import Config
from typing import Union
from src.utils.cache_store import MemCache


class Auth:
    config = None
    handler = None
    blacklist = None

    @classmethod
    @contextmanager
    def initialize(cls, app):
        cls.config = Config()

        yield Auth

        cls.config.read_only = True

    @classmethod
    async def create_access_token(
            cls,
            identity: int,
            role: Any = None,
            csrf: str = None,
            claims: Optional[dict] = None,
            expires_delta: Optional[timedelta] = None,
            ip: Optional[str] = None
    ):

        payload = {cls.config.identity_name: identity}

        if role and cls.config.use_acl:
            payload[cls.config.acl_claim] = role

        if ip and cls.config.check_login_ip:
            payload["ip"] = ip

        if csrf and cls.config.csrf_protect:
            payload["csrf"] = csrf

        if claims:
            claims = flatten(claims, reducer="path")
            for k, v in claims.items():
                payload[cls.config.claim_namespace + k] = v

        if expires_delta is None:
            expires_delta: Union[timedelta, bool] = cls.config.token_expires

        access_token = shortuuid.uuid(
            name=f"{str(identity)}_{str(datetime.now().timestamp())}"
        )

        if expires_delta:
            await MemCache.set_data(access_token, payload, ttl=int(expires_delta.total_seconds()))
        else:
            await MemCache.set_data(access_token, payload)
        return access_token
