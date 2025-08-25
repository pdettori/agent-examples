import os
import sys
import logging
import httpx
from pydantic import AnyHttpUrl
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.provider import AccessToken, TokenVerifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s: %(message)s')


class SimpleTokenVerifier(TokenVerifier):
    """Simple token verifier for demonstration."""
    def __init__(self, introspection_endpoint = None, 
                 client_id = None, 
                 client_secret = None,
                 validate_resource = False):
        self.introspection_endpoint = introspection_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.validate_resource = validate_resource

    def _validate_resource(self, data) -> bool:
        # check aud claim in data
        if client_id is None: 
            logger.warning(f"No CLIENT_ID env var not set - failing resource validation")
            return False
        if "aud" in data:
            # needs client id
            audiences = data["aud"]
            return client_id in audiences
        return False

    def _dummy_token(self, token: str) -> AccessToken | None:
        return AccessToken(
                token=token,
                client_id="hard-coded-client-id",
                scopes=[],
                expires_at=None,
                resource=None,
                )

    def _verify_token(self, token: str) -> AccessToken | None:
        timeout = httpx.Timeout(10.0, connect=5.0)
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
        with httpx.Client (
            timeout=timeout,
            limits=limits,
            verify=False,
        ) as client:
            try:
                response = client.post(
                    self.introspection_endpoint,
                    data={
                        "token": token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                logger.debug(f"Response to token introspection: {response}")

                if response.status_code != 200:
                    logger.error(f"Token introspection returned status {response.status_code}")
                    return None

                data = response.json()
                logger.debug(f"data: {data}")
                if not data.get("active", False):
                    return None

                # RFC 8707 resource validation (only when --oauth-strict is set)
                if self.validate_resource and not self._validate_resource(data):
                    logger.warning(f"Token resource validation failed. Expected: {self.resource_url}")
                    return None

                access_token = AccessToken(
                    token=token,
                    client_id=data.get("client_id", "unknown"),
                    scopes=data.get("scope", "").split() if data.get("scope") else [],
                    expires_at=data.get("exp"),
                    resource=data.get("aud"),  # Include resource in token
                )
                logger.debug(str(access_token))
                return access_token
            except Exception as e:
                logger.warning(f"Token introspection failed: {e}")
                return None



    async def verify_token(self, token: str) -> AccessToken | None:
        logger.info(f"Received Access Token: {token}")
        if self.client_id is None: # no verification
            return self._dummy_token(token)
        # if id and secret are defined, verify against issuer
        return self._verify_token(token)

def get_token_verifier():
    introspection_endpoint = os.getenv("INTROSPECTION_ENDPOINT")
    client_id = os.getenv("CLIENT_NAME")
    client_secret = os.getenv("CLIENT_SECRET")
    validate_resource = False
    if not client_id is None:
        validate_resource = True
    if introspection_endpoint is None:
        return None
    else:
        return SimpleTokenVerifier(introspection_endpoint=introspection_endpoint, 
                                   client_id=client_id,
                                   client_secret=client_secret,
                                   validate_resource=validate_resource)

def get_auth():
    issuer = os.getenv("ISSUER")
    if issuer is None:
        return None
    else:
        return AuthSettings(
                issuer_url=AnyHttpUrl(issuer),  # Authorization Server URL
                resource_server_url=AnyHttpUrl("http://0.0.0.0:8000"),  # TODO This server's URL
                required_scopes=[],
              )
