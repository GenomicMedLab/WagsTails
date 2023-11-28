"""Test Ensembl data source."""
from pathlib import Path

import pytest

from wags_tails import EnsemblData


@pytest.fixture(scope="function")
def ensembl_data_dir(base_data_dir: Path):
    """Provide Ensembl data directory."""
    dir = base_data_dir / "ensembl"
    dir.mkdir(exist_ok=True, parents=True)
    return dir


@pytest.fixture(scope="function")
def ensembl(ensembl_data_dir: Path):
    """Provide ChemblData fixture"""
    return EnsemblData(ensembl_data_dir, silent=True)


def test_get_latest_local(
    ensembl: EnsemblData,
    ensembl_data_dir: Path,
):
    """Test local file management in EnsemblData.get_latest()"""
    with pytest.raises(ValueError):
        ensembl.get_latest(from_local=True, force_refresh=True)

    with pytest.raises(FileNotFoundError):
        ensembl.get_latest(from_local=True)

    file_path = ensembl_data_dir / "ensembl_GRCh38_110.gff"
    file_path.touch()
    path, version = ensembl.get_latest(from_local=True)
    assert path == file_path
    assert version == "GRCh38_110"
