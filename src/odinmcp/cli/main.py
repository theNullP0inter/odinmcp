
import importlib
import typer
import asyncio

app = typer.Typer(
    name="odinmcp",
    help="OdinMCP CLI",
    add_completion=False,
    no_args_is_help=True,  # Show help if no args provided
)

from typing import List

@app.command(name="run_web")
def run_web(app_path: str, params: List[str] = typer.Argument(None)):
    """
    Run a web app with uvicorn. 
    app_path should be in the format 'module:attr', e.g., 'test_app.main:web'
    Any additional CLI arguments will be passed as kwargs to uvicorn.Config, e.g.:
    odinmcp run_web test_app.main:web --host 0.0.0.0 --port 8080
    """
    import uvicorn

    if ':' not in app_path:
        raise typer.BadParameter("app_path must be in the format 'module:attr', e.g., 'test_app.main:web'")

    module_path, app_attr = app_path.split(':', 1)
    module = importlib.import_module(module_path)
    asgi_app = getattr(module, app_attr, None)
    if asgi_app is None:
        raise typer.BadParameter(f"Module '{module_path}' does not have attribute '{app_attr}'")

    # Parse params as key-value pairs
    extra_kwargs = {}
    if params:
        if len(params) % 2 != 0:
            raise typer.BadParameter("Additional arguments must be key value pairs, e.g., --host 0.0.0.0 --port 8080")
        for i in range(0, len(params), 2):
            key = params[i].lstrip('-')
            value = params[i + 1]
            # Try to convert value to int or float if possible
            if value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass
            extra_kwargs[key] = value

    # Default port to 80 if not provided
    if "port" not in extra_kwargs:
        extra_kwargs["port"] = 80

    config = uvicorn.Config(
        asgi_app,
        **extra_kwargs
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


@app.command(name="version")
def version():
    print("OdinMCP version 0.1.0")
    
