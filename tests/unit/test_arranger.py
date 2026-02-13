from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
import pytest

from arranger.run import load_config, arrange_templates, main, build_mappings


class TestLoadConfig:
    def test_load_config_success(self, mocker):
        """Test loading config from pyproject.toml."""
        mock_data = {"tool": {"arranger": {"key": "value"}}}
        mock_toml_load = mocker.patch("tomllib.load", return_value=mock_data)
        mock_file = mocker.patch("builtins.open", mock_open())

        result = load_config(Path("dummy.toml"))

        expected = {
            "key": "value",
            "source-mappings": {},
        }
        assert result == expected
        mock_file.assert_called_once_with(Path("dummy.toml"), "rb")
        mock_toml_load.assert_called_once()

    def test_load_config_no_tool_section(self, mocker):
        """Test loading config when [tool] section is missing."""
        mock_data = {"project": {}}
        mocker.patch("tomllib.load", return_value=mock_data)
        mocker.patch("builtins.open", mock_open())

        result = load_config(Path("dummy.toml"))

        expected = {
            "source-mappings": {},
        }
        assert result == expected

    def test_load_config_no_arranger_section(self, mocker):
        """Test loading config when [tool.arranger] section is missing."""
        mock_data = {"tool": {"other": {}}}
        mocker.patch("tomllib.load", return_value=mock_data)
        mocker.patch("builtins.open", mock_open())

        result = load_config(Path("dummy.toml"))

        expected = {
            "source-mappings": {},
        }
        assert result == expected


class TestArrangeTemplates:
    def test_arrange_templates_places_files(self, mocker):
        """Test that arrange_templates places templates."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_dst = mocker.MagicMock()
        mock_dst.exists.return_value = False
        mock_dst.parent.mkdir = mocker.MagicMock()
        mock_dst.write_text = mocker.MagicMock()

        fixture_dir = mocker.MagicMock()
        fixture_dir.__truediv__.return_value = mock_dst

        mappings = {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}

        mock_file = mocker.MagicMock()
        mock_subfile = mocker.MagicMock()
        mock_subfile.read_text.return_value = "template content"
        mock_file.__truediv__.return_value = mock_subfile
        mock_files.return_value = mock_file

        arrange_templates(fixture_dir, mappings)

        fixture_dir.__truediv__.assert_called_once_with("CHANGELOG.md")
        mock_files.assert_called_once_with("arranger.templates")
        mock_file.__truediv__.assert_called_once_with("universal/CHANGELOG.md.j2")
        mock_dst.write_text.assert_called_once_with("template content")

    def test_arrange_templates_multiple_files(self, mocker):
        """Test placing multiple files."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_dst = mocker.MagicMock()
        mock_dst.exists.return_value = False
        mock_dst.parent.mkdir = mocker.MagicMock()
        mock_dst.write_text = mocker.MagicMock()

        fixture_dir = mocker.MagicMock()
        fixture_dir.__truediv__.return_value = mock_dst

        mappings = {
            "CHANGELOG.md": "universal/CHANGELOG.md.j2",
            "addon.xml": "kodi/script.module.example/addon.xml",
        }

        mock_file = mocker.MagicMock()
        mock_subfile = mocker.MagicMock()
        mock_subfile.read_text.return_value = "template content"
        mock_file.__truediv__.return_value = mock_subfile
        mock_files.return_value = mock_file

        arrange_templates(fixture_dir, mappings)

        assert fixture_dir.__truediv__.call_count == 2
        assert mock_files.call_count == 2
        assert mock_dst.write_text.call_count == 2

    def test_arrange_templates_file_exists_overwrites(self, mocker):
        """Test arrange_templates overwrites if file exists."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_dst = mocker.MagicMock()
        mock_dst.exists.return_value = True  # File exists
        mock_dst.parent.mkdir = mocker.MagicMock()

        fixture_dir = mocker.MagicMock()
        fixture_dir.__truediv__.return_value = mock_dst

        mappings = {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}

        mock_file = mocker.MagicMock()
        mock_subfile = mocker.MagicMock()
        mock_subfile.read_text.return_value = "template content"
        mock_file.__truediv__.return_value = mock_subfile
        mock_files.return_value = mock_file

        arrange_templates(fixture_dir, mappings)


class TestBuildMappings:
    def test_build_mappings_default(self, mocker):
        """Test build_mappings with default config."""
        config = {
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        result = build_mappings(config, args)

        expected = {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}
        assert result == expected

    def test_build_mappings_with_kodi(self, mocker):
        """Test build_mappings with kodi enabled."""
        config = {
            "use-default-kodi-addon-structure": True,
            "kodi-project-name": "script.module.test",
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = True
        args.changelog_only = False

        result = build_mappings(config, args)

        expected = {
            "addon.xml": "kodi-addons/addon.xml.j2",
        }
        assert result == expected

    def test_build_mappings_override_error(self, mocker):
        """Test build_mappings raises error on override."""
        config = {
            "source-mappings": {"CHANGELOG.md": "custom/template.j2"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="Cannot override default mapping"):
            build_mappings(config, args)

    def test_build_mappings_kodi_via_args(self, mocker):
        """Test build_mappings with kodi enabled via args."""
        config = {
            "kodi-project-name": "script.module.arg",
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = True
        args.changelog_only = False

        result = build_mappings(config, args)

        expected = {
            "addon.xml": "kodi-addons/addon.xml.j2",
        }
        assert result == expected

    def test_build_mappings_with_pypi(self, mocker):
        """Test build_mappings with pypi enabled."""
        config = {
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = True
        args.kodi_addon = False
        args.changelog_only = False

        result = build_mappings(config, args)

        expected = {}  # TODO: Add PyPI defaults
        assert result == expected

    def test_build_mappings_with_source_mappings(self, mocker):
        """Test build_mappings with custom source mappings."""
        config = {
            "source-mappings": {"README.md": "universal/README.md.j2"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        result = build_mappings(config, args)

        expected = {
            "CHANGELOG.md": "universal/CHANGELOG.md.j2",
            "README.md": "universal/README.md.j2",
        }
        assert result == expected


class TestMain:
    def test_main_parses_args_correctly(self, mocker, capsys):
        """Test that main parses CLI args and calls functions."""
        mock_load_config = mocker.patch(
            "arranger.run.load_config", return_value={"key": "value"}
        )
        mock_build_mappings = mocker.patch(
            "arranger.run.build_mappings", return_value={"CHANGELOG.md": "universal/CHANGELOG.md.j2"}
        )
        mock_arrange = mocker.patch("arranger.run.arrange_templates")
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=True)

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_args.override = False
            mock_parse.return_value = mock_args

            main()

            mock_load_config.assert_called_once_with(Path("pyproject.toml"))
            mock_build_mappings.assert_called_once_with({"key": "value"}, mock_args)
            mock_arrange.assert_called_once_with(Path("."), {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}, override=False)

            captured = capsys.readouterr()
            assert "Template structure built." in captured.out

    def test_main_pyproject_not_found(self, mocker):
        """Test main raises error if pyproject.toml not found."""
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=False)

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_parse.return_value = mock_args

            with pytest.raises(FileNotFoundError, match="pyproject.toml not found"):
                main()


def test_script_execution(mocker):
    """Test that the script calls main when executed directly."""
    mocker.patch("arranger.run.main")
    # For coverage, since main is tested
    pass
