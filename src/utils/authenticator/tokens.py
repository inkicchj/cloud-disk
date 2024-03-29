
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from flatten_dict import unflatten

from .auth_manager import Auth
from .exceptions import NoAuthorizationError
from src.utils.cache_store import MemCache


@dataclass
class Token:
    raw_token: str
    raw_data: Dict[str, Any] = field(init=False)

    # Metadata
    role: Optional[str] = field(init=False, default=None)
    identity: int = field(init=False)
    csrf: str = field(init=False, default=None)
    ip: str = field(init=False, default=None)

    # Additional claims
    claims: Dict[str, Any] = field(init=False, default=None)

    async def init(self):
        self.raw_data = await self._decode_token()
        self.identity = self.raw_data.get(Auth.config.identity_name)
        self.role = (
            self.raw_data.get(Auth.config.acl_claim) if Auth.config.use_acl else None
        )
        self.ip = (
            self.raw_data.get("ip") if Auth.config.check_login_ip else None
        )
        self.csrf = self.raw_data.get("csrf")

        self.claims = (
            self._get_claims() if Auth.config.claim_namespace else {}
        )
        return self

    def _get_claims(self):
        claims = {
            k.replace(Auth.config.claim_namespace, ""): v
            for k, v in self.raw_data.items()
            if k.startswith(Auth.config.claim_namespace)
        }

        return unflatten(claims, splitter="path")

    async def _decode_token(self):
        token_data = await MemCache.get_data(self.raw_token)
        if not token_data:
            raise NoAuthorizationError("User is not login.")
        return token_data

    async def revoke(self):
        await MemCache.del_data(self.raw_token)
