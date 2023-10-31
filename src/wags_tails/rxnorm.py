"""Provide source fetching for RxNorm."""
import datetime
import logging
import os
import zipfile
from pathlib import Path
from typing import Optional

import requests

from .base_source import DataSource, RemoteDataError
from .core_utils.downloads import download_http
from .core_utils.versioning import DATE_VERSION_PATTERN

_logger = logging.getLogger(__name__)


class RxNormData(DataSource):
    """Provide access to RxNorm database."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in, if specified. See
            ``get_data_dir()`` in the ``storage_utils`` module for further configuration
            details.
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "rxnorm"
        self._filetype = "RRF"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        url = "https://rxnav.nlm.nih.gov/REST/version.json"
        r = requests.get(url)
        r.raise_for_status()
        try:
            raw_version = r.json()["version"]
            return datetime.datetime.strptime(raw_version, "%d-%b-%Y").strftime(
                DATE_VERSION_PATTERN
            )
        except (ValueError, KeyError):
            raise RemoteDataError(
                f"Unable to parse latest RxNorm version from API endpoint: {url}."
            )

    def _zip_handler(self, dl_path: Path, outfile_path: Path) -> None:
        """Provide simple callback function to extract the largest file within a given
        zipfile and save it within the appropriate data directory.

        :param Path dl_path: path to temp data file
        :param Path outfile_path: path to save file within
        :raise RemoteDataError: if unable to locate RRF file
        """
        with zipfile.ZipFile(dl_path, "r") as zip_ref:
            for file in zip_ref.filelist:
                if file.filename == "rrf/RXNCONSO.RRF":
                    file.filename = outfile_path.name
                    target = file
                    break
            else:
                raise RemoteDataError("Unable to find RxNorm RRF in downloaded file")
            zip_ref.extract(target, path=outfile_path.parent)
        os.remove(dl_path)

    def _download_data(self, version: str, file_path: Path) -> None:
        """Download latest RxNorm data file.

        :param version: version of RxNorm to download
        :param file_path: path to save file to
        :raises DownloadException: if API Key is not defined in the environment.
        """
        api_key = os.environ.get("UMLS_API_KEY")
        if api_key is None:
            _logger.error("Could not find `UMLS_API_KEY` in environment variables.")
            raise RemoteDataError("`UMLS_API_KEY` not found.")

        fmt_version = datetime.datetime.strptime(
            version, DATE_VERSION_PATTERN
        ).strftime("%m%d%Y")
        dl_url = f"https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_{fmt_version}.zip"
        url = f"https://uts-ws.nlm.nih.gov/download?url={dl_url}&apiKey={api_key}"

        download_http(
            url, file_path, handler=self._zip_handler, tqdm_params=self._tqdm_params
        )
