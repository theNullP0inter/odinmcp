
import importlib
from starlette.applications import Starlette
import typer
import asyncio
import importlib.resources as pkg_resources
from pathlib import Path
from typing import List
import os
import shutil


app = typer.Typer(
    name="odinmcp",
    help="OdinMCP CLI",
    add_completion=False,
    no_args_is_help=True,  # Show help if no args provided
)


@app.command(name="web")
def web(app_path: str, params: List[str] = typer.Argument(None)):
    """
    Run a web app with uvicorn. 
    app_path should be in the format 'module:attr', e.g., 'test_app.main:web'
    Any additional CLI arguments will be passed as kwargs to uvicorn.Config, e.g.:
    odinmcp web test_app.main:web --host 0.0.0.0 --port 8080
    """
    import uvicorn

    if ':' not in app_path:
        raise typer.BadParameter("app_path must be in the format 'module:attr', e.g., 'test_app.main:web'")

    import sys
    import os
    module_path, app_attr = app_path.split(':', 1)

    # Support file path or module path
    if module_path.endswith('.py') or os.path.isfile(module_path):
        file_path = os.path.abspath(module_path)
        module_dir = os.path.dirname(file_path)
        module_file = os.path.basename(file_path)
        module_name = os.path.splitext(module_file)[0]
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        module = importlib.import_module(module_name)
    else:
        module = importlib.import_module(module_path)

    asgi_app = getattr(module, app_attr, None)
    if asgi_app is None:
        raise typer.BadParameter(f"Module '{module_path}' does not have attribute '{app_attr}'")
    if not isinstance(asgi_app, Starlette):
        raise typer.BadParameter(f"Attribute '{app_attr}' is not a Starlette app")
    
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


def ensure_folder(path):
    """
    Create a folder if it does not exist.
    """
    os.makedirs(path, exist_ok=True)

@app.command(name="setup_asgard")
def setup_asgard(
    target_dir: str = typer.Argument(None, help="Target directory to copy asgard into. Defaults to ./asgard in the current project."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files.")
):
    """
    Copy the contents of the asgard folder (package data) into the specified target directory.
    By default, will not overwrite existing files unless --force is specified.
    If target_dir is not provided, defaults to ./asgard in the current working directory.
    """
    # Use importlib.resources to access the asgard directory inside the odinmcp package
    try:
        asgard_root = pkg_resources.files("odinmcp").joinpath("asgard")
    except Exception as e:
        typer.echo(f"Could not locate asgard package data: {e}")
        raise typer.Exit(code=1)

    if not asgard_root.exists():
        typer.echo(f"asgard directory not found in package resources: {asgard_root}")
        raise typer.Exit(code=1)

    if target_dir is None:
        target_dir = os.path.join(os.getcwd(), "asgard")
    target_dir = os.path.abspath(target_dir)
    ensure_folder(target_dir)

    def ignore_patterns(dir, files):
        return [f for f in files if f.startswith('.')]

    # Recursively copy asgard package data to target_dir
    for item in asgard_root.iterdir():
        s = item
        d = Path(target_dir) / item.name
        if s.is_dir():
            if d.exists():
                if force:
                    shutil.rmtree(d)
                else:
                    typer.echo(f"Directory exists and will not be overwritten: {d}")
                    continue
            shutil.copytree(s, d, ignore=ignore_patterns)
        else:
            if d.exists() and not force:
                typer.echo(f"File exists and will not be overwritten: {d}")
                continue
            shutil.copy2(s, d)
    typer.echo(f"Copied contents of {asgard_root} to {target_dir}")

    # Handle conf.example -> .conf and env.example -> .env
    for example_file, target_file in [("conf.example", ".conf"), ("env.example", ".env")]:
        example_path = Path(target_dir) / example_file
        target_path = Path(target_dir) / target_file
        if example_path.exists():
            if target_path.exists():
                if force:
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                else:
                    typer.echo(f"{target_file} exists and will not be overwritten: {target_path}")
                    continue
            if example_path.is_dir():
                shutil.copytree(example_path, target_path)
                typer.echo(f"Copied directory {example_file} to {target_file} in {target_dir}")
            else:
                shutil.copy2(example_path, target_path)
                typer.echo(f"Copied file {example_file} to {target_file} in {target_dir}")
        else:
            typer.echo(f"{example_file} not found in {target_dir}, skipping copy to {target_file}")

@app.command(name="worker")
def worker(app_path: str, params: List[str] = typer.Argument(None)):
    """
    Run a worker app with celery. 
    app_path should be in the format 'module:attr', e.g., 'test_app.main:worker'
    Any additional CLI arguments will be passed as kwargs to celery, e.g.:
    odinmcp worker test_app.main:worker --broker redis://localhost:6379/0 --result-backend redis://localhost:6379/0
    """

    from celery import Celery
    import importlib
    
    if ':' not in app_path:
        raise typer.BadParameter("app_path must be in the format 'module:attr', e.g., 'test_app.main:worker'")
    
    import sys
    import os
    module_path, app_attr = app_path.split(':', 1)

    # Support file path or module path
    if module_path.endswith('.py') or os.path.isfile(module_path):
        file_path = os.path.abspath(module_path)
        module_dir = os.path.dirname(file_path)
        module_file = os.path.basename(file_path)
        module_name = os.path.splitext(module_file)[0]
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        module = importlib.import_module(module_name)
    else:
        module = importlib.import_module(module_path)

    celery_app: Celery = getattr(module, app_attr, None)
    if celery_app is None:
        raise typer.BadParameter(f"Module '{module_path}' does not have attribute '{app_attr}'")
    if not isinstance(celery_app, Celery):
        raise typer.BadParameter(f"Attribute '{app_attr}' is not a Celery app")

    argv = ["worker"] + (params or [])
    celery_app.worker_main(argv=argv)

