"""Tests for Celesto version consistency."""

import importlib.metadata
import inspect

import celesto
from celesto.cli.main import main


class TestVersion:
    """Verify version is consistent across all surfaces."""

    def test_init_version_matches_metadata(self) -> None:
        """celesto.__version__ should match importlib.metadata."""
        metadata_version = importlib.metadata.version("celesto")
        assert celesto.__version__ == metadata_version

    def test_only_celesto_console_entry_point(self) -> None:
        distribution = importlib.metadata.distribution("celesto")
        commands = {
            entry.name: entry.value
            for entry in distribution.entry_points
            if entry.group == "console_scripts"
        }
        assert commands == {"celesto": "celesto.cli.main:main"}

    def test_cli_version_flag(self, capsys) -> None:
        """celesto --version should print the package version."""
        assert main(["--version"]) == 0
        assert celesto.__version__ in capsys.readouterr().out

    def test_cli_short_version_flag(self, capsys) -> None:
        """celesto -V should also trigger version output."""
        assert main(["-V"]) == 0
        assert celesto.__version__ in capsys.readouterr().out

    def test_version_not_hardcoded_in_init(self) -> None:
        """__version__ should come from package metadata, not a hardcoded string."""
        source = inspect.getsource(celesto)
        assert '__version__ = "' not in source, (
            "__version__ should be read from importlib.metadata, not hardcoded"
        )
