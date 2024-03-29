from dataclasses import dataclass
from datetime import timedelta
from typing import Tuple, Union, Optional


@dataclass
class Config:
    read_only: bool = False

    identity_name: str = "identity"
    # secrets
    # secret_key: Optional[str] = None

    # General configs
    token_location: Tuple[str] = ("header",)
    token_expires: Union[timedelta, bool] = timedelta(minutes=15)

    # JWT in headers configs
    token_header_key: str = "Authorization"
    token_header_prefix: str = "Bearer"

    # JWT in cookies configs
    token_cookie: str = 'access_token'
    csrf_protect: bool = False

    # CSRF configs
    csrf_request_methods: Tuple[str] = ('POST', 'PUT', 'PATCH', 'DELETE')
    csrf_header: str = 'X-CSRF-Token'

    # JWT in query params option
    token_query_param_name: str = "jwt"

    # ACL config
    use_acl: bool = False
    acl_claim: str = "role"

    claim_namespace: str = "claim_"

    check_login_ip: bool = False

    def __setattr__(self, key, value):
        if self.read_only:
            raise RuntimeError("Can not set attribute after app initialized.")
        super().__setattr__(key, value)
