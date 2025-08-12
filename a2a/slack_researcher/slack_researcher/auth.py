import logging
import os
import sys

from keycloak import KeycloakOpenID
from pydantic import AnyHttpUrl
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.provider import AccessToken, TokenVerifier

from slack_researcher.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s: %(message)s')

class SimpleTokenVerifier(TokenVerifier):
    """Simple token verifier for demonstration."""

    async def verify_token(self, token: str) -> AccessToken | None:
        print(token)
        return AccessToken(
                    token=token,
                    client_id="hard-coded-client-id",
                    scopes=[],
                    expires_at=None,
                    resource=None,  # Include resource in token
                )

def get_token_verifier():
    issuer = os.getenv("ISSUER")
    if issuer is None:
        return None
    else:
        return SimpleTokenVerifier()

def get_auth():
    issuer = os.getenv("ISSUER")
    if issuer is None:
        return None
    else:
        return AuthSettings(
                issuer_url=AnyHttpUrl(issuer),  # Authorization Server URL
                resource_server_url=AnyHttpUrl(f"http://localhost:{settings.SERVICE_PORT}"),  # TODO This server's URL
                required_scopes=[],
              )

#########
# A very hacky POC integration with Keycloak
#######
def get_keycloak_token() -> str:
    keycloak_url = os.getenv("KEYCLOAK_URL", "http://keycloak.localtest.me:8080")
    client_id = os.getenv("CLIENT_NAME", "NOTSET")
    realm_name = "master"
    client_secret = os.getenv("CLIENT_SECRET")

    user_username = "test-user"
    user_password = "test-password"

    logger.info(
          f"Using client_id='{client_id}' with realm={realm_name}"
    )

    try:
        keycloak_openid = KeycloakOpenID(server_url=keycloak_url,
                                        client_id=client_id,
                                        realm_name=realm_name,
                                        client_secret_key=client_secret)
    
        access_token = keycloak_openid.token(
                username=user_username,
                password=user_password)
    except Exception as e:
        raise Exception(f"Authorization error getting the access token: {e}")    

    logger.info(
          f"Received access token: {access_token}"
    )
    return access_token