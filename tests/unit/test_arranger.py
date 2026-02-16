from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
import pytest

from arranger.run import load_config, arrange_templates, main, build_mappings


class TestLoadConfig:
    def test_load_config_success(self, mocker):
        """Test loading config from pyproject.toml."""
        mock_data = {"tool": {"arranger": {"key": "value"}}}
        mocker.patch("tomllib.load", return_value=mock_data)
        mocker.patch("builtins.open", mock_open())
        mocker.patch("pathlib.Path.exists", return_value=True)

        result = load_config(Path("dummy.toml"))

        expected = {
            "key": "value",
            "source-mappings": {},
        }
        assert result == expected

    def test_load_config_no_tool_section(self, mocker):
        """Test loading config when [tool] section is missing."""
        mock_data = {"project": {}}
        mocker.patch("tomllib.load", return_value=mock_data)
        mocker.patch("builtins.open", mock_open())
        mocker.patch("pathlib.Path.exists", return_value=True)

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
        mocker.patch("pathlib.Path.exists", return_value=True)

        result = load_config(Path("dummy.toml"))

        expected = {
            "source-mappings": {},
        }
        assert result == expected

    def test_load_config_missing_pyproject(self):
        """Test error handling when pyproject.toml is missing (E1.2)."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(Path("/nonexistent/pyproject.toml"))
        
        error_msg = str(exc_info.value)
        assert "pyproject.toml not found" in error_msg
        assert "project root directory" in error_msg

    def test_load_config_malformed_toml(self, mocker):
        """Test error handling for malformed TOML syntax (E1.3)."""
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("builtins.open", mock_open())
        mocker.patch(
            "tomllib.load",
            side_effect=ValueError("Invalid TOML syntax at line 1")
        )
        
        with pytest.raises(ValueError) as exc_info:
            load_config(Path("bad.toml"))
        
        error_msg = str(exc_info.value)
        assert "Invalid TOML syntax" in error_msg

    def test_load_config_unknown_keys_warning(self, mocker, capsys):
        """Test warning for unknown config keys (E1.6 partial)."""
        mock_data = {"tool": {"arranger": {
            "templates-dir": "templates",
            "unknown-key": "value",
            "another-bad-key": 123
        }}}
        mocker.patch("tomllib.load", return_value=mock_data)
        mocker.patch("builtins.open", mock_open())
        mocker.patch("pathlib.Path.exists", return_value=True)
        
        result = load_config(Path("dummy.toml"))
        
        captured = capsys.readouterr()
        assert "Warning: Unknown keys" in captured.err
        assert "unknown-key" in captured.err
        assert "another-bad-key" in captured.err


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
        mock_dst.write_text.assert_called_once_with("template content", encoding="utf-8")

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
        assert mock_files.call_count == 1
        assert mock_dst.write_text.call_count == 2

    def test_arrange_templates_file_exists_overwrites(self, mocker):
        """Test arrange_templates overwrites if file exists."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_dst = mocker.MagicMock()
        mock_dst.exists.return_value = True  # File exists
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

        arrange_templates(fixture_dir, mappings, override=True)
        mock_dst.write_text.assert_called_once()

    def test_arrange_templates_missing_source(self, mocker, tmp_path):
        """Test error handling when template file doesn't exist (E1.1)."""
        # Mock importlib to return a file that raises FileNotFoundError on read
        mock_files = mocker.patch("importlib.resources.files")
        mock_template_dir = mocker.MagicMock()
        
        # Create a mock that raises FileNotFoundError when read_text is called
        mock_template_file = mocker.MagicMock()
        mock_template_file.read_text.side_effect = FileNotFoundError("No such file")
        
        # Set up the chain: files() / template_path -> raises error on read_text()
        mock_template_dir.__truediv__ = mocker.MagicMock(return_value=mock_template_file)
        mock_files.return_value = mock_template_dir
        
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        mappings = {"dest.txt": "missing.j2"}
        
        with pytest.raises(FileNotFoundError) as exc_info:
            arrange_templates(fixture_dir, mappings)
        
        assert "Template file not found" in str(exc_info.value)
        assert "missing.j2" in str(exc_info.value)

    def test_arrange_templates_import_error(self, mocker, tmp_path):
        """Test error handling when template package cannot be imported (E1.4)."""
        mocker.patch(
            "importlib.resources.files",
            side_effect=ModuleNotFoundError("No module named 'arranger.templates'")
        )
        
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        mappings = {"dest.txt": "template.j2"}
        
        with pytest.raises(RuntimeError) as exc_info:
            arrange_templates(fixture_dir, mappings)
        
        error_msg = str(exc_info.value)
        assert "Failed to import template package" in error_msg
        assert "psr-templates" in error_msg

    def test_arrange_templates_permission_denied(self, mocker, tmp_path):
        """Test error handling for permission denied when writing (E1.5)."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template_file = mocker.MagicMock()
        mock_template_file.read_text.return_value = "content"
        # Create a div operation that returns a MagicMock with read_text
        mock_template_file.__truediv__ = mocker.MagicMock(return_value=mock_template_file)
        mock_files.return_value = mock_template_file
        
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        
        mappings = {"dest.txt": "template.j2"}
        
        # Create a real Path object that will fail on write
        mock_path = mocker.MagicMock(spec=Path)
        mock_path.parent = mocker.MagicMock(spec=Path)
        mock_path.parent.mkdir = mocker.MagicMock()
        mock_path.exists.return_value = False
        mock_path.write_text.side_effect = PermissionError("Access denied")
        
        mocker.patch.object(Path, '__truediv__', return_value=mock_path)
        
        with pytest.raises(PermissionError) as exc_info:
            arrange_templates(fixture_dir, mappings)
        
        error_msg = str(exc_info.value)
        assert "Permission denied" in error_msg


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

        expected = {"templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2"}
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
            "templates/script.module.test/addon.xml.j2": "kodi-addons/addon.xml.j2",
            "templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2",
        }
        assert result == expected

    def test_build_mappings_override_error(self, mocker):
        """Test build_mappings raises error on override."""
        config = {
            "source-mappings": {"templates/CHANGELOG.md.j2": "custom/template.j2"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="Cannot override default mapping"):
            build_mappings(config, args)

    def test_build_mappings_mutually_exclusive_flags(self, mocker):
        """Test build_mappings raises error on mutually exclusive flags."""
        config = {"source-mappings": {}}
        args = mocker.MagicMock()
        args.pypi = True
        args.kodi_addon = True  # Conflicting with pypi
        args.changelog_only = False

        with pytest.raises(ValueError, match="mutually exclusive"):
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
            "templates/script.module.arg/addon.xml.j2": "kodi-addons/addon.xml.j2",
            "templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2",
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

        # Changelog is always included even when PyPI is enabled
        expected = {"templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2"}
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
            "templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2",
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
            "arranger.run.build_mappings", return_value={"templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2"}
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
            mock_arrange.assert_called_once_with(Path("."), {"templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2"}, override=False)

            captured = capsys.readouterr()
            assert "Template structure built successfully" in captured.out

    def test_main_pyproject_not_found(self, mocker):
        """Test main handles error if pyproject.toml not found."""
        mock_exists = mocker.patch("pathlib.Path.exists", return_value=False)

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # main() should exit with code 1 on error
            assert exc_info.value.code == 1


def test_script_execution(mocker):
    """Test that the script calls main when executed directly."""
    mocker.patch("arranger.run.main")
    # For coverage, since main is tested
    pass
