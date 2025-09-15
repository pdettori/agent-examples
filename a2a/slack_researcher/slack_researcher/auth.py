import httpx
import logging
import sys

from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.authentication import AuthCredentials, SimpleUser, AuthenticationBackend
from starlette.authentication import AuthenticationError as StarletteAuthenticationError

from authlib.jose import jwt
from authlib.common.errors import AuthlibBaseError

from slack_researcher.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s: %(message)s')

def on_auth_error(request: Request, e: Exception):
    status_code = 401
    message = "Authentication failed"
    headers = {"WWW-Authenticate": "Bearer"}

    if isinstance(e, AuthenticationError):
        status_code = e.status_code
    message = str(e)

    return JSONResponse(
        {"error": message},
        status_code = status_code,
        headers=headers if status_code == 401 else None
    )

class AuthenticationError(StarletteAuthenticationError):
    def __init__(self, message: str, status_code: int = 401):
        self.status_code = status_code
        super().__init__(message)

class BearerAuthBackend(AuthenticationBackend):
    def __init__(self):
        if settings.JWKS_URL is None: # TODO implement oidc discovery in this case
            raise Exception("JWKS_URL env var not set. ")
        settings.jwks_url = settings.JWKS_URL

        self.claims_options = {}
        if settings.AUDIENCE is None:
            logger.debug(f"AUDIENCE env var not set. No audience check will be performed. ")
        else:
            self.claims_options["aud"] = {"essential": True, "value": settings.AUDIENCE}
        if settings.ISSUER is None:
            logger.debug(f"ISSUER env var no set. No issuer check will be performed")
        else:
            self.claims_options["iss"] = {"essential": True, "value": settings.ISSUER}

    async def get_jwks(self):
        logger.debug(f"Fetching JWKS from {self.jwks_url}")
        jwks = None
        try: 
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                jwks = response.json() # TODO should probably use caching
                return jwks
        except httpx.HTTPStatusError as e:
            logger.debug(f"Could not retrieve JWKS from {self.jwks_url}: {e}")
            return None

    async def get_token(self, conn):
        logger.debug("Obtaining bearer token...")
        headers = conn.headers
        logger.debug(f"Headers obtained: {headers}")
        auth = headers.get("authorization")
        if not auth or not auth.lower().startswith("bearer "):
            logger.error("Expected `Authorization: Bearer` access token; None provided. ")
            return None
        token = auth.split(" ", 1)[1]
        return token

    """This is run upon every received request"""
    async def authenticate(self, conn):
        # bypass authentication for agent card
        if conn.scope.get("path") == "/.well-known/agent.json":
            logger.debug("Bypassing authentication for public agent card path")
            return None
        
        # extract token
        token = await self.get_token(conn)
        if token is None:
            raise AuthenticationError(message = "Bearer token not found in Authorization header.")

        # fetch jwks
        jwks = await self.get_jwks()

        try: 
            # decode and validate claims
            claims = jwt.decode(s=token, key=jwks, claims_options=self.claims_options)
            claims.validate()
            logger.debug("Token successfully validated.")

            # return user
            user = SimpleUser(token)
            return AuthCredentials(["authenticated"]), user
        except AuthlibBaseError as e:
            logger.error(f"Token validation failed: {e}")
            raise AuthenticationError(f"Invalid token: {e}, status_code=401")