"""
Module for A2A Agent.
"""

import logging
import sys
import httpx
import traceback
from typing import Callable

import uvicorn
from autogen.mcp.mcp_client import create_toolkit, Toolkit
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentSkill, TaskState, TextPart, SecurityScheme, HTTPAuthSecurityScheme
from a2a.utils import new_agent_text_message, new_task

from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.authentication import AuthCredentials, SimpleUser, AuthenticationBackend
from starlette.authentication import AuthenticationError as StarletteAuthenticationError
from starlette.middleware.authentication import AuthenticationMiddleware

from authlib.jose import jwt
from authlib.common.errors import AuthlibBaseError

from slack_researcher.config import settings, Settings
from slack_researcher.event import Event
from slack_researcher.main import SlackAgent

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
        if settings.AUDIENCE is None:
            raise Exception("AUDIENCE env var not set")
        if settings.ISSUER is None:
            raise Exception("ISSUER env var not set")
        if settings.JWKS_URL is None: # TODO implement oidc discovery in this case
            raise Exception("JWKS_URL env var not set. ")
        self.expected_audience = settings.AUDIENCE
        self.issuer = settings.ISSUER
        self.jwks_url = settings.JWKS_URL

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
            claims_options = {
                "iss": {"essential": True, "value": self.issuer},
                "aud": {"essential": True, "value": self.expected_audience},
            }
            claims = jwt.decode(s=token, key=jwks, claims_options=claims_options)
            claims.validate()
            logger.debug("Token successfully validated.")

            # return user
            user = SimpleUser(token)
            return AuthCredentials(["authenticated"]), user
        except AuthlibBaseError as e:
            logger.error(f"Token validation failed: {e}")
            raise AuthenticationError(f"Invalid token: {e}, status_code=401")

def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the AG2 Agent."""
    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
        id="slack_researcher",
        name="Slack research agent",
        description="Answer queries by searching through a given slack server",
        tags=["research", "slack", "search", "report"],
        examples=[
            "Find me the most popular channels for discussing AI agents",
            "Summarize what's been happening in the general channel lately",
        ],
    )
    return AgentCard(
        name="Web Research Agent",
        description="Answer queries by searching through a given slack server",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=capabilities,
        skills=[skill],
        securitySchemes={
            "Bearer": SecurityScheme(
                root=HTTPAuthSecurityScheme(
                    type="http",
                    scheme="bearer",
                    bearerFormat="JWT",
                    description="OAuth 2.0 JWT token"
                )
            )
        },
    )


class A2AEvent(Event):
    """
    A class to handle events for A2A Agent.

    Attributes:
        task_updater (TaskUpdater): The task updater instance.
    """

    def __init__(self, task_updater: TaskUpdater):
        """
        Initializes the A2AEvent instance.

        Args:
            task_updater (TaskUpdater): The task updater instance.
        """
        self.task_updater = task_updater

    async def emit_event(self, message: str, final: bool = False) -> None:
        """
        Emits an event with the given message.

        Args:
            message (str): The event message.
            final (bool): Whether the event is final. Defaults to False.
        """
        logger.info("Emitting event %s", message)

        if final:
            parts = [TextPart(text=message)]
            await self.task_updater.add_artifact(parts)
            await self.task_updater.complete()
        else:
            await self.task_updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    message,
                    self.task_updater.context_id,
                    self.task_updater.task_id,
                ),
            )


class ResearchExecutor(AgentExecutor):
    """
    A class to handle research execution for A2A Agent.
    """
    async def _run_agent(self,
        messages: dict,
        settings: Settings,
        event_emitter: Event,
        assistant_tool_map: dict[str, Callable],
        toolkit: Toolkit):

        slack_agent = SlackAgent(
            config=settings,
            eventer=event_emitter,
            assistant_tools=assistant_tool_map,
            mcp_toolkit=toolkit,
        )
        result = await slack_agent.execute(messages)
        await event_emitter.emit_event(result, True)

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """
        Executes the research task.

        Args:
            context (RequestContext): The request context.
            event_queue (EventQueue): The event queue instance.

        Returns:
            None
        """
        user_token = context.call_context.user.user_name
        user_input = [context.get_user_input()]
        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)
        task_updater = TaskUpdater(event_queue, task.id, task.context_id)
        event_emitter = A2AEvent(task_updater)
        messages = []
        for message in user_input:
            messages.append(
                {
                    "role": "User",
                    "content": message,
                }
            )

        # no internal tools right now, will add later
        assistant_tool_map = {}

        # Hook up MCP tools
        toolkit = None
        try:
            if settings.MCP_URL:
                logging.info("Connecting to MCP server at %s", settings.MCP_URL)

                headers={}
                if user_token:
                    headers={"Authorization": f"Bearer {user_token}"}

                async with streamablehttp_client(
                    url=settings.MCP_URL,
                    headers=headers
                )  as (
                    read_stream,
                    write_stream,
                    _,
                ), ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    toolkit = await create_toolkit(
                        session=session, use_mcp_resources=False
                    )
                    await self._run_agent(messages, settings,
                        event_emitter,
                        assistant_tool_map,
                        toolkit,)
            else:
                await self._run_agent(messages, settings,
                    event_emitter,
                    assistant_tool_map,
                    toolkit,)

        except Exception as e:
            traceback.print_exc()
            await event_emitter.emit_event(f"I'm sorry I was unable to fulfill your request. I encountered the following exception: {str(e)}", True)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Not implemented
        """
        raise Exception("cancel not supported")


def run():
    """
    Runs the A2A Agent application.
    """
    agent_card = get_agent_card(host="0.0.0.0", port=settings.SERVICE_PORT)

    request_handler = DefaultRequestHandler(
        agent_executor=ResearchExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    app = server.build()  # this returns a Starlette app
    app.add_middleware(AuthenticationMiddleware, backend=BearerAuthBackend(), on_error=on_auth_error)

    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
