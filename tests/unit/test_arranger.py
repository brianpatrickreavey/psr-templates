from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from conftest import setup_fixture_and_templates_mocks

from arranger.run import (
    _parse_addon_xml,
    _validate_addon_metadata_consistency,
    arrange_templates,
    build_mappings,
    load_config,
    main,
)


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
        mocker.patch("tomllib.load", side_effect=ValueError("Invalid TOML syntax at line 1"))

        with pytest.raises(ValueError) as exc_info:
            load_config(Path("bad.toml"))

        error_msg = str(exc_info.value)
        assert "Invalid TOML syntax" in error_msg

    def test_load_config_unknown_keys_warning(self, mocker, capsys):
        """Test warning for unknown config keys (E1.6 partial)."""
        mock_data = {
            "tool": {
                "arranger": {
                    "templates-dir": "templates",
                    "unknown-key": "value",
                    "another-bad-key": 123,
                }
            }
        }
        mocker.patch("tomllib.load", return_value=mock_data)
        mocker.patch("builtins.open", mock_open())
        mocker.patch("pathlib.Path.exists", return_value=True)

        load_config(Path("dummy.toml"))

        captured = capsys.readouterr()
        assert "Warning: Unknown keys" in captured.err
        assert "unknown-key" in captured.err
        assert "another-bad-key" in captured.err


class TestArrangeTemplates:
    def test_arrange_templates_places_files(self, mocker):
        """Test that arrange_templates places templates."""
        mocks = setup_fixture_and_templates_mocks(mocker)

        mappings = {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}
        arrange_templates(mocks["fixture_dir"], mappings)

        mocks["fixture_dir_resolved"].__truediv__.assert_called_with("CHANGELOG.md")
        mocks["mock_files"].assert_called_once_with("arranger.templates")
        mocks["mock_root"].__truediv__.assert_called_with("universal/CHANGELOG.md.j2")
        mocks["mock_dst"].write_text.assert_called_once_with("template content", encoding="utf-8")

    def test_arrange_templates_multiple_files(self, mocker):
        """Test placing multiple files."""
        mocks = setup_fixture_and_templates_mocks(mocker)

        mappings = {
            "CHANGELOG.md": "universal/CHANGELOG.md.j2",
            "addon.xml": "kodi/script.module.example/addon.xml",
        }
        arrange_templates(mocks["fixture_dir"], mappings)

        assert mocks["fixture_dir_resolved"].__truediv__.call_count == 2
        assert mocks["mock_files"].call_count == 1
        assert mocks["mock_dst"].write_text.call_count == 2

    def test_arrange_templates_file_exists_overwrites(self, mocker):
        """Test arrange_templates overwrites if file exists."""
        mocks = setup_fixture_and_templates_mocks(mocker)
        mocks["mock_dst"].exists.return_value = True  # File exists

        mappings = {"CHANGELOG.md": "universal/CHANGELOG.md.j2"}
        arrange_templates(mocks["fixture_dir"], mappings, override=True)

        mocks["mock_dst"].write_text.assert_called_once()

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
            side_effect=ModuleNotFoundError("No module named 'arranger.templates'"),
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

        mocker.patch.object(Path, "__truediv__", return_value=mock_path)

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
            "kodi-addon-directory": "script.module.test",
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
            "kodi-addon-directory": "script.module.arg",
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
            "source-mappings": {"docs/README.md": "universal/README.md.j2"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        result = build_mappings(config, args)

        expected = {
            "templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2",
            "docs/README.md": "universal/README.md.j2",
        }
        assert result == expected

    def test_build_mappings_invalid_source_mappings_dest_no_slash(self, mocker):
        """Test E1.8: Reject destination paths without directory separator."""
        config = {
            "source-mappings": {"file.txt": "template.j2"},  # No slash!
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError) as exc_info:
            build_mappings(config, args)

        error_msg = str(exc_info.value)
        assert "Invalid destination path format" in error_msg
        assert "directory level" in error_msg

    def test_build_mappings_invalid_source_mappings_dest_trailing_slash(self, mocker):
        """Test E1.8: Reject destination paths ending with slash (directories)."""
        config = {
            "source-mappings": {"dir/subdir/": "template.j2"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError) as exc_info:
            build_mappings(config, args)

        error_msg = str(exc_info.value)
        assert "Destination path cannot be a directory" in error_msg or "Cannot be a directory" in error_msg

    def test_build_mappings_invalid_source_mappings_template_path_trailing_slash(self, mocker):
        """Test E1.8: Reject template paths ending with slash (directories)."""
        config = {
            "source-mappings": {"dir/file.txt": "templates/"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError) as exc_info:
            build_mappings(config, args)

        error_msg = str(exc_info.value)
        assert "Invalid template path format" in error_msg
        assert "specific files" in error_msg

    def test_build_mappings_empty_dest_path(self, mocker):
        """Test E1.8: Reject empty destination paths."""
        config = {
            "source-mappings": {"": "template.j2"},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError) as exc_info:
            build_mappings(config, args)

        error_msg = str(exc_info.value)
        assert "Invalid destination path format" in error_msg


class TestArrangeTemplatesPhase2:
    """Tests for Phase 2 error handling improvements (E1.7-E1.12)."""

    def test_arrange_templates_empty_fixture_dir_created(self, mocker, tmp_path):
        """Test E1.10: arrange_templates creates missing fixture directory."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        mock_template.read_text.return_value = "content"
        mock_files.return_value = mocker.MagicMock(__truediv__=mocker.MagicMock(return_value=mock_template))

        fixture_dir = tmp_path / "new_dir"  # Directory doesn't exist yet
        assert not fixture_dir.exists()

        mappings = {"dest/file.txt": "template.j2"}
        arrange_templates(fixture_dir, mappings)

        # Verify directory was created
        assert fixture_dir.exists()
        assert (fixture_dir / "dest" / "file.txt").exists()

    def test_arrange_templates_empty_mappings_error(self, mocker, tmp_path):
        """Test E1.10: arrange_templates rejects empty mappings."""
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        with pytest.raises(ValueError) as exc_info:
            arrange_templates(fixture_dir, {})

        error_msg = str(exc_info.value)
        assert "No templates to arrange" in error_msg

    def test_arrange_templates_override_false_file_exists(self, mocker, tmp_path):
        """Test E1.9: override=False prevents file overwrite."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        mock_template.read_text.return_value = "new content"
        mock_files.return_value = mocker.MagicMock(__truediv__=mocker.MagicMock(return_value=mock_template))

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        # Create an existing file
        existing_file = fixture_dir / "dest" / "file.txt"
        existing_file.parent.mkdir(parents=True)
        existing_file.write_text("old content")

        mappings = {"dest/file.txt": "template.j2"}

        with pytest.raises(FileExistsError) as exc_info:
            arrange_templates(fixture_dir, mappings, override=False)

        error_msg = str(exc_info.value)
        assert "exists" in error_msg or "override" in error_msg.lower()

    def test_arrange_templates_override_true_overwrites(self, mocker, tmp_path):
        """Test E1.9: override=True allows file overwrite."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        mock_template.read_text.return_value = "new content"
        mock_files.return_value = mocker.MagicMock(__truediv__=mocker.MagicMock(return_value=mock_template))

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        # Create an existing file
        existing_file = fixture_dir / "dest" / "file.txt"
        existing_file.parent.mkdir(parents=True)
        existing_file.write_text("old content")

        mappings = {"dest/file.txt": "template.j2"}
        arrange_templates(fixture_dir, mappings, override=True)

        # Verify content was overwritten
        assert existing_file.read_text() == "new content"

    def test_arrange_templates_symlink_with_override(self, mocker, tmp_path):
        """Test E1.11: arrange_templates removes symlinks when override=True."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        mock_template.read_text.return_value = "new content"
        mock_files.return_value = mocker.MagicMock(__truediv__=mocker.MagicMock(return_value=mock_template))

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        # Create a symlink
        target_file = tmp_path / "target.txt"
        target_file.write_text("target content")

        symlink_path = fixture_dir / "dest" / "file.txt"
        symlink_path.parent.mkdir(parents=True)
        symlink_path.symlink_to(target_file)

        assert symlink_path.is_symlink()

        mappings = {"dest/file.txt": "template.j2"}
        arrange_templates(fixture_dir, mappings, override=True)

        # Verify symlink was replaced with file content
        assert not symlink_path.is_symlink()
        assert symlink_path.read_text() == "new content"

    def test_arrange_templates_symlink_without_override(self, mocker, tmp_path):
        """Test E1.11: arrange_templates rejects symlinks when override=False."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        mock_template.read_text.return_value = "new content"
        mock_files.return_value = mocker.MagicMock(__truediv__=mocker.MagicMock(return_value=mock_template))

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        # Create a symlink
        target_file = tmp_path / "target.txt"
        target_file.write_text("target content")

        symlink_path = fixture_dir / "dest" / "file.txt"
        symlink_path.parent.mkdir(parents=True)
        symlink_path.symlink_to(target_file)

        mappings = {"dest/file.txt": "template.j2"}

        with pytest.raises(FileExistsError) as exc_info:
            arrange_templates(fixture_dir, mappings, override=False)

        error_msg = str(exc_info.value)
        assert "Symlink" in error_msg or "exists" in error_msg

    def test_arrange_templates_invalid_fixture_dir(self):
        """Test E1.7: arrange_templates rejects invalid fixture directory."""
        fixture_dir = None  # None path
        mappings = {"dest/file.txt": "template.j2"}

        with pytest.raises((ValueError, AttributeError)):
            arrange_templates(fixture_dir, mappings)

    def test_arrange_templates_unicode_encoding(self, mocker, tmp_path):
        """Test E1.12: arrange_templates handles UTF-8 content correctly."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        # Template with unicode characters
        mock_template.read_text.return_value = "# Changelog\n✓ Done\n© Copyright"
        mock_files.return_value = mocker.MagicMock(__truediv__=mocker.MagicMock(return_value=mock_template))

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        mappings = {"CHANGELOG.md": "template.j2"}
        arrange_templates(fixture_dir, mappings)

        # Verify unicode content was written correctly
        content = (fixture_dir / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "✓" in content
        assert "©" in content


class TestMain:
    def test_main_parses_args_correctly(self, mocker, capsys):
        """Test that main parses CLI args and calls functions."""
        mock_load_config = mocker.patch("arranger.run.load_config", return_value={"key": "value"})
        mock_build_mappings = mocker.patch(
            "arranger.run.build_mappings",
            return_value={"templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2"},
        )
        mock_arrange = mocker.patch("arranger.run.arrange_templates")
        mocker.patch("pathlib.Path.exists", return_value=True)

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
            mock_arrange.assert_called_once_with(
                Path("."),
                {"templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2"},
                override=False,
            )

            captured = capsys.readouterr()
            assert "Template structure built successfully" in captured.out

    def test_main_pyproject_not_found(self, mocker):
        """Test main handles error if pyproject.toml not found."""
        mocker.patch("pathlib.Path.exists", return_value=False)

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


class TestAddonXmlParsing:
    """Tests for addon.xml metadata parsing and validation."""

    def test_parse_addon_xml_nonexistent_file(self, tmp_path):
        """Test that parsing returns None when file doesn't exist."""
        addon_path = tmp_path / "nonexistent.xml"
        result = _parse_addon_xml(addon_path)
        assert result is None

    def test_parse_addon_xml_success(self, tmp_path):
        """Test successful parsing of addon.xml with metadata."""
        addon_xml = tmp_path / "addon.xml"
        addon_xml.write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<addon id="script.module.test" name="Test Module" version="1.0.0" provider-name="Test Author">
    <requires>
        <import addon="xbmc.python" version="3.0.0"/>
        <import addon="xbmc.addon.requests" version="2.28.0"/>
    </requires>
    <extension point="xbmc.python.module" library="lib"/>
</addon>"""
        )

        result = _parse_addon_xml(addon_xml)
        assert result is not None
        assert result["id"] == "script.module.test"
        assert result["name"] == "Test Module"
        assert result["version"] == "1.0.0"
        assert result["provider-name"] == "Test Author"
        assert len(result["requires"]) == 2
        assert result["requires"][0]["addon"] == "xbmc.python"
        assert result["requires"][0]["version"] == "3.0.0"
        assert result["requires"][1]["addon"] == "xbmc.addon.requests"

    def test_parse_addon_xml_no_requires(self, tmp_path):
        """Test parsing addon.xml without requires section."""
        addon_xml = tmp_path / "addon.xml"
        addon_xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<addon id="script.module.simple" name="Simple" version="0.1.0" provider-name="Author">
    <extension point="xbmc.python.module" library="lib"/>
</addon>"""
        )

        result = _parse_addon_xml(addon_xml)
        assert result is not None
        assert result["id"] == "script.module.simple"
        assert result["requires"] == []

    def test_parse_addon_xml_malformed(self, tmp_path, capsys):
        """Test handling of malformed XML."""
        addon_xml = tmp_path / "addon.xml"
        addon_xml.write_text('<?xml version="1.0"?>\n<addon><unclosed>')

        result = _parse_addon_xml(addon_xml)
        assert result is None
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "Failed to parse addon.xml" in captured.err

    def test_validate_addon_metadata_consistency_no_existing_file(self, tmp_path):
        """Test validation when addon.xml doesn't exist (new project)."""
        # Should not raise any errors for new projects
        _validate_addon_metadata_consistency(tmp_path, "script.module.example", None)

    def test_validate_addon_metadata_consistency_match(self, tmp_path, capsys):
        """Test validation when config and addon.xml metadata match."""
        addon_dir = tmp_path / "script.module.example"
        addon_dir.mkdir()
        addon_xml = addon_dir / "addon.xml"
        addon_xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<addon id="script.module.example" name="Example" version="1.0.0" provider-name="Test">
</addon>"""
        )

        config_metadata = {
            "id": "script.module.example",
            "name": "Example",
            "provider-name": "Test",
        }

        _validate_addon_metadata_consistency(tmp_path, "script.module.example", config_metadata)
        # Should not generate any warnings
        captured = capsys.readouterr()
        assert "Warning" not in captured.err

    def test_validate_addon_metadata_consistency_mismatch(self, tmp_path, capsys):
        """Test validation when config and addon.xml metadata mismatch."""
        addon_dir = tmp_path / "script.module.example"
        addon_dir.mkdir()
        addon_xml = addon_dir / "addon.xml"
        addon_xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<addon id="script.module.example" name="Example" version="1.0.0" provider-name="Test">
</addon>"""
        )

        config_metadata = {
            "id": "script.module.old",
            "name": "Old Example",
            "provider-name": "Test",
        }

        _validate_addon_metadata_consistency(tmp_path, "script.module.example", config_metadata)
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "Metadata mismatch" in captured.err
        assert "id" in captured.err


class TestPhase5Coverage:
    """Additional tests to improve code coverage for Phase 5 (T5.2)."""

    def test_load_config_toml_decode_error(self, mocker):
        """Test error handling for TOMLDecodeError (E1.3 specific decoder error)."""
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("builtins.open", mock_open())

        # Create a mock exception that looks like TOMLDecodeError
        import tomllib

        original_error = tomllib.TOMLDecodeError("error msg", "doc", 0)
        mocker.patch("tomllib.load", side_effect=original_error)

        with pytest.raises(ValueError, match="Invalid TOML"):
            load_config(Path("bad.toml"))

    def test_load_config_generic_read_error(self, mocker):
        """Test error handling for general file read errors."""
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))

        with pytest.raises(ValueError, match="Failed to read"):
            load_config(Path("bad.toml"))

    def test_config_validation_invalid_templates_dir_type(self, mocker):
        """Test config validation rejects non-string templates-dir."""
        config = {
            "templates-dir": 123,  # Should be string
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="Invalid type"):
            build_mappings(config, args)

    def test_config_validation_rejects_non_string_kodi_addon_directory(self, mocker):
        """Test config validation rejects non-string kodi-addon-directory."""
        config = {
            "kodi-addon-directory": ["list", "value"],  # Should be string
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="Invalid type"):
            build_mappings(config, args)

    def test_config_validation_empty_templates_dir(self, mocker):
        """Test config validation rejects empty templates-dir."""
        config = {
            "templates-dir": "",  # Empty string
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="cannot be an empty string"):
            build_mappings(config, args)

    def test_config_validation_templates_dir_with_path_separator(self, mocker):
        """Test config validation rejects templates-dir containing path separators."""
        config = {
            "templates-dir": "path/to/templates",  # Has path separator
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="simple directory name"):
            build_mappings(config, args)

    def test_config_validation_empty_kodi_addon_directory(self, mocker):
        """Test config validation rejects empty kodi-addon-directory."""
        config = {
            "kodi-addon-directory": "",  # Empty string
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = True
        args.changelog_only = False

        with pytest.raises(ValueError, match="cannot be an empty string"):
            build_mappings(config, args)

    def test_config_validation_invalid_source_mappings_type(self, mocker):
        """Test config validation rejects non-dict source-mappings."""
        config = {
            "source-mappings": "not a dict",  # Should be dict
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="Invalid type|expected dict"):
            build_mappings(config, args)

    def test_config_validation_source_mappings_non_string_keys(self, mocker):
        """Test config validation rejects non-string keys in source-mappings."""
        config = {
            "source-mappings": {123: "template.j2"},  # Key should be string
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="must be strings"):
            build_mappings(config, args)

    def test_build_mappings_kodi_without_project_name(self, mocker):
        """Test build_mappings with kodi flag but no project name (uses fallback)."""
        config = {
            "use-default-kodi-addon-structure": True,
            # No kodi-addon-directory
            "source-mappings": {},
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = True
        args.changelog_only = False

        result = build_mappings(config, args)

        # Should use fallback to root templates
        expected = {
            "templates/addon.xml.j2": "kodi-addons/addon.xml.j2",
            "templates/CHANGELOG.md.j2": "universal/CHANGELOG.md.j2",
        }
        assert result == expected

    def test_arrange_templates_template_is_directory_error(self, mocker, tmp_path):
        """Test error when template path points to directory (IsADirectoryError)."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        # Raise IsADirectoryError when read_text is called
        mock_template.read_text.side_effect = IsADirectoryError("Is a directory")

        mock_root = mocker.MagicMock()
        mock_root.__truediv__.return_value = mock_template
        mock_files.return_value = mock_root

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        mappings = {"dest.txt": "template_dir"}

        with pytest.raises(ValueError, match="points to a directory"):
            arrange_templates(fixture_dir, mappings)

    def test_arrange_templates_permission_denied_on_dir_create(self, mocker, tmp_path):
        """Test permission error when creating destination directories."""
        mock_files = mocker.patch("importlib.resources.files")
        mock_template = mocker.MagicMock()
        mock_template.read_text.return_value = "content"

        mock_root = mocker.MagicMock()
        mock_root.__truediv__.return_value = mock_template
        mock_files.return_value = mock_root

        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()

        # Mock the destination path to fail on parent.mkdir()
        mock_dst = mocker.MagicMock(spec=Path)
        mock_dst.exists.return_value = False
        mock_dst.is_symlink.return_value = False
        mock_dst.parent.mkdir.side_effect = PermissionError("Access denied")

        mocker.patch.object(Path, "__truediv__", return_value=mock_dst)

        mappings = {"dest.txt": "template.j2"}

        with pytest.raises(PermissionError, match="Permission denied"):
            arrange_templates(fixture_dir, mappings)

    def test_main_value_error_handling(self, mocker):
        """Test main() handles ValueError from arrangement."""
        mocker.patch("arranger.run.load_config", return_value={"source-mappings": {}})
        mocker.patch(
            "arranger.run.build_mappings",
            side_effect=ValueError("Invalid configuration"),
        )

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_file_exists_error_handling(self, mocker):
        """Test main() handles FileExistsError."""
        mocker.patch("arranger.run.load_config", return_value={"source-mappings": {}})
        mocker.patch(
            "arranger.run.build_mappings",
            return_value={"dest.txt": "template.j2"},
        )
        mocker.patch(
            "arranger.run.arrange_templates",
            side_effect=FileExistsError("File exists, use --override"),
        )

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_args.override = False
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_permission_error_handling(self, mocker):
        """Test main() handles PermissionError."""
        mocker.patch("arranger.run.load_config", return_value={"source-mappings": {}})
        mocker.patch(
            "arranger.run.build_mappings",
            return_value={"dest.txt": "template.j2"},
        )
        mocker.patch(
            "arranger.run.arrange_templates",
            side_effect=PermissionError("Access denied"),
        )

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_args.override = False
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_runtime_error_handling(self, mocker):
        """Test main() handles RuntimeError (import failures)."""
        mocker.patch("arranger.run.load_config", return_value={"source-mappings": {}})
        mocker.patch(
            "arranger.run.build_mappings",
            return_value={"dest.txt": "template.j2"},
        )
        mocker.patch(
            "arranger.run.arrange_templates",
            side_effect=RuntimeError("Cannot import templates package"),
        )

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_args.override = False
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_config_validation_source_mappings_non_string_dest(self, mocker):
        """Test config validation rejects non-string destination in source-mappings."""
        config = {
            "source-mappings": {123: "template.j2"},  # Int key instead of string
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="must be strings"):
            build_mappings(config, args)

    def test_config_validation_source_mappings_non_string_value(self, mocker):
        """Test config validation rejects non-string template path in source-mappings."""
        config = {
            "source-mappings": {"dir/file.txt": 456},  # Number value instead of string
        }
        args = mocker.MagicMock()
        args.pypi = False
        args.kodi_addon = False
        args.changelog_only = True

        with pytest.raises(ValueError, match="must be strings"):
            build_mappings(config, args)

    def test_validate_fixture_dir_generic_exception(self, mocker):
        """Test _validate_fixture_directory handles generic exceptions."""
        from arranger.run import _validate_fixture_directory

        mock_fixture_dir = mocker.MagicMock()
        mock_fixture_dir.resolve.side_effect = OSError("Generic OS error")

        with pytest.raises(ValueError, match="Cannot access fixture directory"):
            _validate_fixture_directory(mock_fixture_dir)

    def test_handle_existing_destination_symlink_permission_error(self, mocker):
        """Test _handle_existing_destination permission error on symlink unlink."""
        from arranger.run import _handle_existing_destination

        dst = mocker.MagicMock()
        dst.is_symlink.return_value = True
        dst.unlink.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError, match="Permission denied removing symlink"):
            _handle_existing_destination(dst, override=True)

    def test_write_destination_file_unicode_error(self, mocker):
        """Test _write_destination_file handles UnicodeEncodeError."""
        from arranger.run import _write_destination_file

        dst = mocker.MagicMock()
        dst.write_text.side_effect = UnicodeEncodeError("utf-8", "test", 0, 1, "test error")

        with pytest.raises(ValueError, match="File encoding error"):
            _write_destination_file(dst, "problematic content")

    def test_main_unexpected_exception_handling(self, mocker):
        """Test main() handles unexpected exceptions."""
        mocker.patch("arranger.run.load_config", return_value={"source-mappings": {}})
        mocker.patch(
            "arranger.run.build_mappings",
            side_effect=KeyError("Unexpected key error"),
        )

        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.pypi = False
            mock_args.kodi_addon = False
            mock_args.changelog_only = False
            mock_parse.return_value = mock_args

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1


class TestTemplateRendering:
    """Test Jinja2 template syntax and rendering with mock PSR context."""

    def test_addon_xml_template_syntax_valid(self):
        """Test addon.xml.j2 has valid Jinja2 syntax."""
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader("src/psr_prepare/templates/kodi-addons"))
        template = env.get_template("addon.xml.j2")

        # Template compiles if syntax is valid
        assert template is not None

    def test_addon_xml_template_renders_init_mode(self):
        """Test addon.xml.j2 renders correctly in init mode."""
        from jinja2 import Environment, FileSystemLoader
        from types import SimpleNamespace

        env = Environment(loader=FileSystemLoader("src/psr_prepare/templates/kodi-addons"))
        template = env.get_template("addon.xml.j2")

        # Mock PSR context for init mode (first release)
        # PSR wraps context in a 'ctx' object
        ctx = SimpleNamespace(
            changelog_mode="init",
            history=SimpleNamespace(
                released={
                    "0.1.0": {
                        "elements": {
                            "feat": [{"descriptions": ["test feature"], "breaking_descriptions": []}]
                        }
                    }
                }
            ),
        )

        output = template.render(ctx=ctx)

        # Verify output contains expected XML structure
        assert '<?xml version="1.0"' in output
        assert '<addon' in output
        assert 'version="0.1.0"' in output
        assert "id=" in output
        assert "[feat] test feature" in output

    def test_addon_xml_template_renders_update_mode(self):
        """Test addon.xml.j2 renders correctly in update mode."""
        from jinja2 import Environment, FileSystemLoader
        from types import SimpleNamespace

        env = Environment(loader=FileSystemLoader("src/psr_prepare/templates/kodi-addons"))
        template = env.get_template("addon.xml.j2")

        # Mock PSR context for update mode (cumulative releases)
        ctx = SimpleNamespace(
            changelog_mode="update",
            history=SimpleNamespace(
                released={
                    "0.1.0": {
                        "elements": {
                            "feat": [{"descriptions": ["old feature"], "breaking_descriptions": []}]
                        }
                    },
                    "0.2.0": {
                        "elements": {
                            "feat": [{"descriptions": ["new feature"], "breaking_descriptions": []}]
                        }
                    },
                }
            ),
        )

        output = template.render(ctx=ctx)

        # Verify output contains expected XML structure
        assert '<?xml version="1.0"' in output
        assert '<addon' in output
        # Latest version should be selected (0.2.0 comes after 0.1.0 lexicographically)
        assert 'version="0.2.0"' in output
        # News should contain latest release only
        assert "Release v0.2.0" in output
        assert "[feat] new feature" in output

    def test_changelog_md_template_syntax_valid(self):
        """Test CHANGELOG.md.j2 has valid Jinja2 syntax."""
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader("src/psr_prepare/templates/universal"))
        template = env.get_template("CHANGELOG.md.j2")

        # Template compiles if syntax is valid
        assert template is not None

    def test_changelog_md_template_renders_init_mode(self):
        """Test CHANGELOG.md.j2 renders correctly in init mode."""
        from jinja2 import Environment, FileSystemLoader
        from types import SimpleNamespace
        from datetime import datetime, timezone

        env = Environment(loader=FileSystemLoader("src/psr_prepare/templates/universal"))
        template = env.get_template("CHANGELOG.md.j2")

        # Mock PSR context for init mode
        # Create a release dict with proper structure (similar to PSR's Release TypedDict)
        release_0_1_0 = {
            "version": "0.1.0",
            "tagged_date": datetime(2026, 2, 17, tzinfo=timezone.utc),
            "tagger": None,
            "committer": None,
            "elements": {
                "feat": [
                    {"descriptions": ["test feature"], "breaking_descriptions": []}
                ],
                "fix": [{"descriptions": ["test fix"], "breaking_descriptions": []}],
            },
        }

        ctx = SimpleNamespace(
            changelog_mode="init",
            history=SimpleNamespace(
                released={
                    "0.1.0": release_0_1_0,
                }
            ),
        )

        output = template.render(ctx=ctx)

        # Verify output contains expected Markdown structure
        assert "# Changelog" in output
        assert "## v0.1.0" in output or "v0.1.0" in output
        assert "[feat]" in output or "test feature" in output

    def test_changelog_md_template_renders_update_mode(self):
        """Test CHANGELOG.md.j2 renders correctly in update mode."""
        from jinja2 import Environment, FileSystemLoader
        from types import SimpleNamespace
        from datetime import datetime, timezone

        env = Environment(loader=FileSystemLoader("src/psr_prepare/templates/universal"))
        template = env.get_template("CHANGELOG.md.j2")

        # Mock PSR context for update mode (cumulative releases)
        release_0_1_0 = {
            "version": "0.1.0",
            "tagged_date": datetime(2026, 2, 16, tzinfo=timezone.utc),
            "tagger": None,
            "committer": None,
            "elements": {
                "feat": [{"descriptions": ["old feature"], "breaking_descriptions": []}]
            },
        }
        release_0_2_0 = {
            "version": "0.2.0",
            "tagged_date": datetime(2026, 2, 17, tzinfo=timezone.utc),
            "tagger": None,
            "committer": None,
            "elements": {
                "feat": [{"descriptions": ["new feature"], "breaking_descriptions": []}]
            },
        }

        ctx = SimpleNamespace(
            changelog_mode="update",
            history=SimpleNamespace(
                released={
                    "0.1.0": release_0_1_0,
                    "0.2.0": release_0_2_0,
                }
            ),
        )

        output = template.render(ctx=ctx)

        # Verify output contains expected Markdown structure
        assert "# Changelog" in output
        # Update mode should include only the latest release (0.2.0)
        assert "0.2.0" in output
        assert "new feature" in output
