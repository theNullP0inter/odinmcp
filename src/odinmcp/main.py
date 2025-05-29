from http import HTTPStatus
import json
from typing import Any, Generic, List, Optional, Type
from mcp.server.lowlevel.server import LifespanResultT
from uuid import uuid4
from mcp.server.fastmcp import FastMCP 
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.exceptions import HTTPException
from starlette.types import Receive, Scope, Send
from mcp.types import JSONRPCMessage, JSONRPCResponse, InitializeResult, JSONRPCRequest, JSONRPCError, ErrorData, PARSE_ERROR, INVALID_REQUEST, INVALID_PARAMS, INTERNAL_ERROR, LATEST_PROTOCOL_VERSION, LoggingCapability, PromptsCapability, ResourcesCapability, ToolsCapability, JSONRPCNotification
from mcp.server.lowlevel.server import Server as MCPServer, lifespan as default_lifespan
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from odinmcp.models.auth import CurrentUser
from odinmcp.web.middleware.heimdall import HeimdallCurrentUserMiddleware
from odinmcp.web.middleware.hermod import HermodStreamingMiddleware
from odinmcp.config import settings
from odinmcp.web.transports.http_streaming import OdinHttpStreamingTransport
from odinmcp.web import OdinWeb
from odinmcp.constants import (
    MCP_SESSION_ID_HEADER,
    LAST_EVENT_ID_HEADER,
    CONTENT_TYPE_HEADER,
    ACCEPT_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE,
    HERMOD_GRIP_HOLD_HEADER,
    HERMOD_GRIP_HOLD_MODE,
    HERMOD_GRIP_CHANNEL_HEADER
)

from odinmcp.config import settings
from celery import Celery
from celery.contrib.abortable import AbortableTask
from odinmcp.worker import OdinWorker
from mcp.server.fastmcp.server import FastMCP, Context
from mcp.server.fastmcp.server import ToolManager, ResourceManager, PromptManager, _convert_to_content
from mcp.types import Prompt as MCPPrompt
from mcp.types import PromptArgument as MCPPromptArgument
from mcp.types import Resource as MCPResource
from mcp.types import ResourceTemplate as MCPResourceTemplate
from mcp.types import Tool as MCPTool
from mcp.types import (
    AnyFunction,
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    TextContent,
    ToolAnnotations,
)
from odinmcp.worker.session import OdinWorkerSession
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Sequence
from pydantic.networks import AnyUrl
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.fastmcp.exceptions import ResourceError
from mcp.server.fastmcp.resources import Resource
from mcp.server.fastmcp.prompts import Prompt
from mcp.server.fastmcp.resources import FunctionResource
import pydantic_core

import inspect
import re

class OdinMCP:
    
    
    def __init__(
        self,
        name: str,
        instructions: Optional[str] = None,
        version: Optional[str] = None,
        current_user_model: Type[CurrentUser] = CurrentUser,
        lifespan: Optional[Callable[
            [MCPServer[LifespanResultT]], AbstractAsyncContextManager[LifespanResultT]
        ]] = default_lifespan,
        extra_middleware:List[Middleware] = []
    ):  
        self.mcp_server = MCPServer(
            name=name,
            instructions=instructions,
            version=version,
            lifespan=lifespan,
        )

        self._setup_handlers()


        self.worker = OdinWorker(
            self.mcp_server,
            current_user_model,
        )
        self.web = OdinWeb(
            self.mcp_server,
            current_user_model,
            self.worker,
        )

        self.current_user_model = current_user_model

        self._tool_manager = ToolManager()
        self._resource_manager = ResourceManager()
        self._prompt_manager = PromptManager()
        
        self.extra_middleware = extra_middleware

    @property
    def name(self) -> str:
        return self.mcp_server.name

    @property
    def instructions(self) -> str | None:
        return self.mcp_server.instructions

    def sse_app(
        self  
    ) -> Starlette:
        return self.web.build(extra_middleware=self.extra_middleware), self.worker.get_worker()
        

    def _setup_handlers(self) -> None:
        """Set up core MCP protocol handlers."""
        self.mcp_server.list_tools()(self.list_tools)
        self.mcp_server.call_tool()(self.call_tool)
        self.mcp_server.list_resources()(self.list_resources)
        self.mcp_server.read_resource()(self.read_resource)
        self.mcp_server.list_prompts()(self.list_prompts)
        self.mcp_server.get_prompt()(self.get_prompt)
        self.mcp_server.list_resource_templates()(self.list_resource_templates)



    async def list_tools(self) -> list[MCPTool]:
        """List all available tools."""
        tools = self._tool_manager.list_tools()
        return [
            MCPTool(
                name=info.name,
                description=info.description,
                inputSchema=info.parameters,
                annotations=info.annotations,
            )
            for info in tools
        ]

    def get_context(self) -> Context[OdinWorkerSession, object]:
        """
        Returns a Context object. Note that the context will only be valid
        during a request; outside a request, most methods will error.
        """
        try:
            request_context = self.mcp_server.request_context
        except LookupError:
            request_context = None
        return Context(request_context=request_context, fastmcp=self)

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool by name with arguments."""
        context = self.get_context()
        result = await self._tool_manager.call_tool(name, arguments, context=context)
        converted_result = _convert_to_content(result)
        return converted_result

    async def list_resources(self) -> list[MCPResource]:
        """List all available resources."""

        resources = self._resource_manager.list_resources()
        return [
            MCPResource(
                uri=resource.uri,
                name=resource.name or "",
                description=resource.description,
                mimeType=resource.mime_type,
            )
            for resource in resources
        ]

    async def list_resource_templates(self) -> list[MCPResourceTemplate]:
        templates = self._resource_manager.list_templates()
        return [
            MCPResourceTemplate(
                uriTemplate=template.uri_template,
                name=template.name,
                description=template.description,
            )
            for template in templates
        ]

    async def read_resource(self, uri: AnyUrl | str) -> Iterable[ReadResourceContents]:
        """Read a resource by URI."""

        resource = await self._resource_manager.get_resource(uri)
        if not resource:
            raise ResourceError(f"Unknown resource: {uri}")

        try:
            content = await resource.read()
            return [ReadResourceContents(content=content, mime_type=resource.mime_type)]
        except Exception as e:
            raise ResourceError(str(e))

    def add_tool(
        self,
        fn: AnyFunction,
        name: str | None = None,
        description: str | None = None,
        annotations: ToolAnnotations | None = None,
    ) -> None:
        """Add a tool to the server.

        The tool function can optionally request a Context object by adding a parameter
        with the Context type annotation. See the @tool decorator for examples.

        Args:
            fn: The function to register as a tool
            name: Optional name for the tool (defaults to function name)
            description: Optional description of what the tool does
            annotations: Optional ToolAnnotations providing additional tool information
        """
        self._tool_manager.add_tool(
            fn, name=name, description=description, annotations=annotations
        )

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
        annotations: ToolAnnotations | None = None,
    ) -> Callable[[AnyFunction], AnyFunction]:
        """Decorator to register a tool.

        Tools can optionally request a Context object by adding a parameter with the
        Context type annotation. The context provides access to MCP capabilities like
        logging, progress reporting, and resource access.

        Args:
            name: Optional name for the tool (defaults to function name)
            description: Optional description of what the tool does
            annotations: Optional ToolAnnotations providing additional tool information

        Example:
            @server.tool()
            def my_tool(x: int) -> str:
                return str(x)

            @server.tool()
            def tool_with_context(x: int, ctx: Context) -> str:
                ctx.info(f"Processing {x}")
                return str(x)

            @server.tool()
            async def async_tool(x: int, context: Context) -> str:
                await context.report_progress(50, 100)
                return str(x)
        """
        # Check if user passed function directly instead of calling decorator
        if callable(name):
            raise TypeError(
                "The @tool decorator was used incorrectly. "
                "Did you forget to call it? Use @tool() instead of @tool"
            )

        def decorator(fn: AnyFunction) -> AnyFunction:
            self.add_tool(
                fn, name=name, description=description, annotations=annotations
            )
            return fn

        return decorator

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the server.

        Args:
            resource: A Resource instance to add
        """
        self._resource_manager.add_resource(resource)

    def resource(
        self,
        uri: str,
        *,
        name: str | None = None,
        description: str | None = None,
        mime_type: str | None = None,
    ) -> Callable[[AnyFunction], AnyFunction]:
        """Decorator to register a function as a resource.

        The function will be called when the resource is read to generate its content.
        The function can return:
        - str for text content
        - bytes for binary content
        - other types will be converted to JSON

        If the URI contains parameters (e.g. "resource://{param}") or the function
        has parameters, it will be registered as a template resource.

        Args:
            uri: URI for the resource (e.g. "resource://my-resource" or "resource://{param}")
            name: Optional name for the resource
            description: Optional description of the resource
            mime_type: Optional MIME type for the resource

        Example:
            @server.resource("resource://my-resource")
            def get_data() -> str:
                return "Hello, world!"

            @server.resource("resource://my-resource")
            async get_data() -> str:
                data = await fetch_data()
                return f"Hello, world! {data}"

            @server.resource("resource://{city}/weather")
            def get_weather(city: str) -> str:
                return f"Weather for {city}"

            @server.resource("resource://{city}/weather")
            async def get_weather(city: str) -> str:
                data = await fetch_weather(city)
                return f"Weather for {city}: {data}"
        """
        # Check if user passed function directly instead of calling decorator
        if callable(uri):
            raise TypeError(
                "The @resource decorator was used incorrectly. "
                "Did you forget to call it? Use @resource('uri') instead of @resource"
            )

        def decorator(fn: AnyFunction) -> AnyFunction:
            # Check if this should be a template
            has_uri_params = "{" in uri and "}" in uri
            has_func_params = bool(inspect.signature(fn).parameters)

            if has_uri_params or has_func_params:
                # Validate that URI params match function params
                uri_params = set(re.findall(r"{(\w+)}", uri))
                func_params = set(inspect.signature(fn).parameters.keys())

                if uri_params != func_params:
                    raise ValueError(
                        f"Mismatch between URI parameters {uri_params} "
                        f"and function parameters {func_params}"
                    )

                # Register as template
                self._resource_manager.add_template(
                    fn=fn,
                    uri_template=uri,
                    name=name,
                    description=description,
                    mime_type=mime_type,
                )
            else:
                # Register as regular resource
                resource = FunctionResource.from_function(
                    fn=fn,
                    uri=uri,
                    name=name,
                    description=description,
                    mime_type=mime_type,
                )
                self.add_resource(resource)
            return fn

        return decorator

    def add_prompt(self, prompt: Prompt) -> None:
        """Add a prompt to the server.

        Args:
            prompt: A Prompt instance to add
        """
        self._prompt_manager.add_prompt(prompt)

    def prompt(
        self, name: str | None = None, description: str | None = None
    ) -> Callable[[AnyFunction], AnyFunction]:
        """Decorator to register a prompt.

        Args:
            name: Optional name for the prompt (defaults to function name)
            description: Optional description of what the prompt does

        Example:
            @server.prompt()
            def analyze_table(table_name: str) -> list[Message]:
                schema = read_table_schema(table_name)
                return [
                    {
                        "role": "user",
                        "content": f"Analyze this schema:\n{schema}"
                    }
                ]

            @server.prompt()
            async def analyze_file(path: str) -> list[Message]:
                content = await read_file(path)
                return [
                    {
                        "role": "user",
                        "content": {
                            "type": "resource",
                            "resource": {
                                "uri": f"file://{path}",
                                "text": content
                            }
                        }
                    }
                ]
        """
        # Check if user passed function directly instead of calling decorator
        if callable(name):
            raise TypeError(
                "The @prompt decorator was used incorrectly. "
                "Did you forget to call it? Use @prompt() instead of @prompt"
            )

        def decorator(func: AnyFunction) -> AnyFunction:
            prompt = Prompt.from_function(func, name=name, description=description)
            self.add_prompt(prompt)
            return func

        return decorator

    async def list_prompts(self) -> list[MCPPrompt]:
        """List all available prompts."""
        prompts = self._prompt_manager.list_prompts()
        return [
            MCPPrompt(
                name=prompt.name,
                description=prompt.description,
                arguments=[
                    MCPPromptArgument(
                        name=arg.name,
                        description=arg.description,
                        required=arg.required,
                    )
                    for arg in (prompt.arguments or [])
                ],
            )
            for prompt in prompts
        ]

    async def get_prompt(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> GetPromptResult:
        """Get a prompt by name with arguments."""
        try:
            messages = await self._prompt_manager.render_prompt(name, arguments)

            return GetPromptResult(messages=pydantic_core.to_jsonable_python(messages))
        except Exception as e:
            raise ValueError(str(e))


        

