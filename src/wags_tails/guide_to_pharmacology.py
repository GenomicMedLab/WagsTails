"""Provide source fetching for Guide To Pharmacology."""
import logging
import re
from pathlib import Path
from typing import NamedTuple, Optional, Tuple

import requests

from wags_tails.version_utils import parse_file_version

from .base_source import DataSource, RemoteDataError

_logger = logging.getLogger(__name__)


class GtoPLigandPaths(NamedTuple):
    """Container for GuideToPharmacology file paths."""

    ligands: Path
    ligand_id_mapping: Path


class GToPLigandData(DataSource):
    """Provide access to Guide to Pharmacology data."""

    def __init__(self, data_dir: Optional[Path] = None, silent: bool = False) -> None:
        """Set common class parameters.

        :param data_dir: direct location to store data files in. If not provided, tries
            to find a "hemonc" subdirectory within the path at environment variable
            $WAGS_TAILS_DIR, or within a "wags_tails" subdirectory under environment
            variables $XDG_DATA_HOME or $XDG_DATA_DIRS, or finally, at
            ``~/.local/share/``
        :param silent: if True, don't print any info/updates to console
        """
        self._src_name = "guidetopharmacology"
        super().__init__(data_dir, silent)

    @staticmethod
    def _get_latest_version() -> str:
        """Retrieve latest version value

        :return: latest release value
        :raise RemoteDataError: if unable to parse version number from releases API
        """
        r = requests.get("https://www.guidetopharmacology.org/")
        r.raise_for_status()
        r_text = r.text.split("\n")
        pattern = re.compile(r"Current Release Version (\d{4}\.\d) \(.*\)")
        for line in r_text:
            if "Current Release Version" in line:
                matches = re.findall(pattern, line.strip())
                if matches:
                    return matches[0]
        else:
            raise RemoteDataError(
                "Unable to parse latest Guide to Pharmacology version number homepage HTML."
            )

    def get_latest(
        self, from_local: bool = False, force_refresh: bool = False
    ) -> Tuple[GtoPLigandPaths, str]:
        """Get path to latest version of data, and its version value

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Paths to data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            raise ValueError("Cannot set both `force_refresh` and `from_local`")

        if from_local:
            ligands_path = self._get_latest_local_file("gtop_ligands_*.tsv")
            ligand_id_mapping_path = self._get_latest_local_file(
                "gtop_ligand_id_mapping_*.tsv"
            )
            file_paths = GtoPLigandPaths(
                ligands=ligands_path, ligand_id_mapping=ligand_id_mapping_path
            )
            return file_paths, parse_file_version(
                ligands_path, r"gtop_ligands_(\d{4}\.\d+).tsv"
            )

        latest_version = self._get_latest_version()
        ligands_path = self._data_dir / f"gtop_ligands_{latest_version}.tsv"
        ligand_id_mapping_path = (
            self._data_dir / f"gtop_ligand_id_mapping_{latest_version}.tsv"
        )
        file_paths = GtoPLigandPaths(
            ligands=ligands_path, ligand_id_mapping=ligand_id_mapping_path
        )
        if not force_refresh:
            if ligands_path.exists() and ligand_id_mapping_path.exists():
                _logger.debug(
                    f"Found existing files, {file_paths}, matching latest version {latest_version}."
                )
                return file_paths, latest_version
            elif ligands_path.exists() or ligand_id_mapping_path.exists():
                _logger.warning(
                    f"Existing files, {file_paths}, not all available -- attempting full download."
                )
        self._download_files(file_paths)
        return file_paths, latest_version

    def _download_files(self, file_paths: GtoPLigandPaths) -> None:
        """Perform file downloads.

        :param file_paths: locations to save files at
        """
        self._http_download(
            "https://www.guidetopharmacology.org/DATA/ligands.tsv",
            file_paths.ligands,
            tqdm_params=self._tqdm_params,
        )
        self._http_download(
            "https://www.guidetopharmacology.org/DATA/ligand_id_mapping.tsv",
            file_paths.ligand_id_mapping,
            tqdm_params=self._tqdm_params,
        )