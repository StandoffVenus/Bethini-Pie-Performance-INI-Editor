import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lib import platform_support as ps


class SplitConfigPathTests(unittest.TestCase):
    def test_windows_style_directory(self):
        parent, name = ps.split_config_path(r"C:\Games\Skyrim\Data")
        self.assertEqual(parent, r"C:\Games\Skyrim")
        self.assertEqual(name, "Data")

    def test_posix_style_file(self):
        parent, name = ps.split_config_path("/home/user/games/skyrim.ini")
        self.assertEqual(parent, "/home/user/games")
        self.assertEqual(name, "skyrim.ini")

    def test_empty(self):
        self.assertEqual(ps.split_config_path(""), ("", ""))


class DirectorySuffixTests(unittest.TestCase):
    def test_preserves_windows_separator(self):
        self.assertEqual(ps.ensure_directory_suffix(r"C:\Games\Skyrim"), "C:\\Games\\Skyrim\\")

    def test_does_not_double_slash(self):
        self.assertEqual(ps.ensure_directory_suffix("/tmp/game/"), "/tmp/game/")

    def test_empty_directory_values(self):
        self.assertTrue(ps.is_empty_directory_value("\\"))
        self.assertTrue(ps.is_empty_directory_value("/"))
        self.assertTrue(ps.is_empty_directory_value(os.sep))
        self.assertFalse(ps.is_empty_directory_value("/tmp"))


class CaseSensitivePathTests(unittest.TestCase):
    def test_exact_case_required_on_unix(self):
        if os.name == "nt":
            self.skipTest("Windows filesystems are typically case-insensitive")
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "Icon.png"
            real.write_text("ok", encoding="utf-8")
            wrong_case = Path(tmp) / "icon.png"
            self.assertTrue(ps.path_exists_exact(real))
            self.assertFalse(ps.path_exists_exact(wrong_case))


class WriteProtectTests(unittest.TestCase):
    def test_clear_and_restore_keeps_other_mode_bits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "readonly.ini"
            path.write_text("[General]\n", encoding="utf-8")
            os.chmod(path, 0o440)
            previous = ps.clear_write_protect(path)
            self.assertTrue(path.stat().st_mode & stat.S_IWUSR)
            ps.restore_file_mode(path, previous)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o440)


class UnixDetectionTests(unittest.TestCase):
    def test_registry_lookup_is_skipped_on_unix(self):
        if os.name == "nt":
            self.skipTest("This assertion is for Unix")
        with mock.patch.object(ps, "steam_game_install_directory", return_value=None):
            self.assertIsNone(ps.windows_registry_install_path("Skyrim Special Edition"))
            self.assertIsNone(ps.detect_game_install_directory("Skyrim Special Edition"))

    def test_steam_install_uses_exact_folder_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "Steam"
            common = library / "steamapps" / "common"
            exact = common / "Skyrim Special Edition"
            wrong_case = common / "skyrim special edition"
            exact.mkdir(parents=True)
            wrong_case.mkdir()
            (library / "steamapps" / "libraryfolders.vdf").write_text(
                f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"path"\t\t"{library}"\n\t}}\n}}\n',
                encoding="utf-8",
            )
            with mock.patch.object(ps, "steam_root_candidates", return_value=[library]):
                found = ps.steam_game_install_directory("Skyrim Special Edition")
            self.assertEqual(found, exact.resolve())

    def test_proton_documents_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "Steam"
            docs = (
                library / "steamapps" / "compatdata" / "489830" / "pfx" / "drive_c"
                / "users" / "steamuser" / "Documents" / "My Games" / "Skyrim Special Edition"
            )
            docs.mkdir(parents=True)
            with mock.patch.object(ps, "iter_steam_libraries", return_value=[library]):
                found = ps.proton_documents_game_directory(
                    "Skyrim Special Edition", "Skyrim Special Edition")
            self.assertEqual(found, docs)

    def test_detect_config_prefers_existing_unix_paths(self):
        if os.name == "nt":
            self.skipTest("Unix autodetection")
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "Documents" / "My Games" / "Fallout4"
            docs.mkdir(parents=True)
            with mock.patch.object(ps, "proton_documents_game_directory", return_value=None), \
                    mock.patch.object(ps, "wine_documents_game_directory", return_value=None), \
                    mock.patch.object(ps, "documents_directory", return_value=Path(tmp) / "Documents"):
                found = ps.detect_game_config_directory("Fallout 4", "Fallout4")
            self.assertEqual(found, docs)


class ResourcePathTests(unittest.TestCase):
    def test_icon_resource_uses_icons_directory_case(self):
        icon = ps.resource_path("icons", "Icon.png")
        self.assertEqual(icon.name, "Icon.png")
        self.assertEqual(icon.parent.name, "icons")
        self.assertTrue(icon.is_file())


if __name__ == "__main__":
    unittest.main()
