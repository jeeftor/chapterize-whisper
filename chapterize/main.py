"""Main File - prompts user for what they actually want to do"""

import os
import asyncio
import click
import functools
from rich.console import Console
from typing import Optional

from chapterize.transcribe import BookTranscriber

console = Console()

def validate_directory(ctx, param, value: Optional[str]) -> str:
    """Validate and return the directory path from either CLI or ENV."""
    directory = value or os.getenv('BOOK_DIRECTORY')
    if not directory:
        raise click.BadParameter('Directory must be provided via --dir or BOOK_DIRECTORY environment variable')
    if not os.path.isdir(directory):
        raise click.BadParameter(f'Directory does not exist: {directory}')
    return directory

@click.group()
def cli():
    """Book processing CLI application."""
    pass

@cli.command()
@click.option(
    '--dir',
    help='Directory containing books to process (or set BOOK_DIRECTORY env var)',
    callback=validate_directory
)
def detect(dir: str):
    """Detect and process books in the specified directory."""
    asyncio.run(async_detect(dir))

async def async_detect(dir: str):
    """Async implementation of detect command."""
    console.print(f"[green]Running detection mode on directory:[/green] {dir}")
    bt = BookTranscriber(dir)
    await bt.transcribe()

@cli.command()
@click.option(
    '--dir',
    help='Directory containing books to process (or set BOOK_DIRECTORY env var)',
    callback=validate_directory
)
@click.option(
    '--api-key',
    envvar='API_KEY',
    help='API key for upload (or set API_KEY env var)',
    required=True
)
@click.option(
    '--abs-url',
    envvar='ABS_URL',
    help='Absolute URL for upload (or set ABS_URL env var)',
    required=True
)
@click.option(
    '--id',
    'book_id',  # Use book_id as the parameter name to avoid conflict with Python's id()
    envvar='BOOK_ID',
    help='Book ID for upload (or set BOOK_ID env var)',
    required=True
)
def upload(dir: str, api_key: str, abs_url: str, book_id: str):
    """Upload books from the specified directory."""
    asyncio.run(async_upload(dir, api_key, abs_url, book_id))

async def async_upload(dir: str, api_key: str, abs_url: str, book_id: str):
    """Async implementation of upload command."""
    console.print("[green]Running upload mode with the following configuration:[/green]")
    console.print(f"Directory: {dir}")
    console.print(f"API Key: {api_key[:4]}{'*' * (len(api_key) - 4)}")  # Mask the API key
    console.print(f"URL: {abs_url}")
    console.print(f"Book ID: {book_id}")
    # Your async upload logic here

if __name__ == '__main__':
    cli()