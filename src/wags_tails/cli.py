"""Provide a CLI application for accessing basic wags-tails functions."""

import inspect
import logging

import click

import wags_tails
from wags_tails.utils.storage import get_data_dir


def _configure_logs(log_level: int = logging.INFO) -> None:
    """Configure logging.

    :param log_level: global log level to set
    """
    logging.basicConfig(
        filename="wags_tails.log",
        format="[%(asctime)s] - %(name)s - %(levelname)s : %(message)s",
    )
    logger = logging.getLogger(__package__)
    logger.setLevel(log_level)


@click.group()
def cli() -> None:
    """Manage genomic source data."""
    _configure_logs()


@cli.command()
def path() -> None:
    """Get path to wags-tails storage directory given current environment configuration."""
    click.echo(get_data_dir())


_DATA_SOURCES = {
    obj._src_name: obj  # noqa: SLF001
    for _, obj in inspect.getmembers(wags_tails, inspect.isclass)
    if obj.__name__ not in {"CustomData", "DataSource", "RemoteDataError"}
}


@cli.command
@click.argument("data", nargs=1, type=click.Choice(list(_DATA_SOURCES.keys())))
@click.option(
    "--silent",
    "-s",
    is_flag=True,
    default=False,
    help="if true, suppress intermediary output to console",
)
@click.option(
    "--from_local",
    is_flag=True,
    default=False,
    help="if true, use latest available local file",
)
@click.option(
    "--force_refresh",
    is_flag=True,
    default=False,
    help="if true, retrieve data from source regardless of local availability",
)
def get_latest(data: str, silent: bool, from_local: bool, force_refresh: bool) -> None:
    """Get latest version of specified dataset.

        % wags-tails get-version do

    Unless ``--from_local`` is declared, ``wags-tails`` will first make an API call
    against the resource to determine the most recent release version, and then either
    provide a local copy if already available, or first download from the data origin
    and then return a link.
    """
    data_class = _DATA_SOURCES[data]
    result, _ = data_class(silent=silent).get_latest(from_local, force_refresh)
    click.echo(result)


@cli.command
def list_sources() -> None:
    """List supported sources."""
    for source in _DATA_SOURCES:
        click.echo(source)
