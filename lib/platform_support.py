#
# This work is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/
# or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#

"""Platform helpers so Bethini Pie can run on Windows and Unix without OS-specific assumptions."""

from __future__ import annotations

import logging
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

IS_WINDOWS = os.name == "nt"
IS_UNIX = not IS_WINDOWS

# Exact Steam install folder names (case-sensitive on Unix filesystems).
GAME_STEAM_INSTALL_DIRS: dict[str, tuple[str, ...]] = {
    "Skyrim Special Edition": ("Skyrim Special Edition",),
    "Skyrim": ("Skyrim",),
    "Starfield": ("Starfield",),
    "Fallout 3": ("Fallout 3 goty", "Fallout 3"),
    "Fallout New Vegas": ("Fallout New Vegas",),
    "Fallout 4": ("Fallout 4",),
    "Enderal": ("Enderal Special Edition", "Enderal"),
    "Oblivion": ("Oblivion",),
}

# Steam app IDs used to locate Proton prefixes / compatdata.
GAME_STEAM_APP_IDS: dict[str, tuple[str, ...]] = {
    "Skyrim Special Edition": ("489830",),
    "Skyrim": ("72850",),
    "Starfield": ("1716740",),
    "Fallout 3": ("22370", "22300"),
    "Fallout New Vegas": ("22380",),
    "Fallout 4": ("377160",),
    "Enderal": ("976620",),
    "Oblivion": ("22330",),
}

_WINREG_KEY_NAMES: dict[str, str] = {
    "Skyrim Special Edition": "Skyrim Special Edition",
    "Skyrim": "skyrim",
    "Fallout 3": "fallout3",
    "Fallout New Vegas": "falloutnv",
    "Fallout 4": "Fallout4",
    "Enderal": "skyrim",
    "Oblivion": "oblivion",
}

_LIBRARYFOLDERS_PATH_RE = re.compile(r'"path"\s+"([^"]+)"')


def application_directory() -> Path:
    """Read-only install directory that contains Bethini.pyw / the frozen executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def directory_is_writable(path: Path) -> bool:
    """Return whether *path* exists and the current user can create files there."""
    try:
        if not path.exists() or not path.is_dir():
            return False
        return os.access(path, os.W_OK | os.X_OK)
    except OSError:
        return False


def _xdg_directory(env_var: str, default_subpath: Path) -> Path:
    configured = os.environ.get(env_var)
    if configured:
        return Path(configured).expanduser() / "bethini-pie"
    return Path.home() / default_subpath / "bethini-pie"


def user_config_directory() -> Path:
    """Writable directory for Bethini.ini.

    Portable installs keep config next to the app. Read-only installs (Nix,
    system packages) use XDG on Unix and %APPDATA% on Windows.
    """
    app_dir = application_directory()
    if directory_is_writable(app_dir):
        return app_dir
    if IS_WINDOWS:
        roaming = os.environ.get("APPDATA")
        if roaming:
            return Path(roaming) / "Bethini Pie"
        return Path.home() / "AppData" / "Roaming" / "Bethini Pie"
    return _xdg_directory("XDG_CONFIG_HOME", Path(".config"))


def user_state_directory() -> Path:
    """Writable directory for logs and other runtime state."""
    app_dir = application_directory()
    if directory_is_writable(app_dir):
        return app_dir
    if IS_WINDOWS:
        return user_config_directory()
    return _xdg_directory("XDG_STATE_HOME", Path(".local") / "state")


def resource_path(*parts: str) -> Path:
    """Build a path under the application directory using the given exact case."""
    return application_directory().joinpath(*parts)


def ui_font(size: int) -> tuple[str, int]:
    """Return a UI font that exists on the current platform."""
    if IS_WINDOWS:
        return ("Segoe UI", size)
    return ("Helvetica", size)


def directory_mtime(path: Path) -> float:
    """Modification time for sorting directories (portable; ctime is not creation time on Unix)."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def ensure_directory_suffix(path_value: str) -> str:
    """Append a trailing separator, preserving slash style already used in the value."""
    if not path_value:
        return path_value
    if path_value.endswith(("/", "\\")):
        return path_value
    separator = "\\" if "\\" in path_value else os.sep
    return path_value + separator


def split_config_path(path_value: str) -> tuple[str, str]:
    """Split a path from a config value that may use Windows or POSIX separators."""
    if not path_value:
        return "", ""
    normalized = path_value.replace("\\", "/")
    parent, separator, name = normalized.rpartition("/")
    if not separator:
        return "", path_value
    if "\\" in path_value:
        parent = parent.replace("/", "\\")
    return parent, name


def is_empty_directory_value(path_value: str) -> bool:
    """True when a directory field is only a bare separator."""
    return path_value in {"\\", "/", os.sep}


def path_exists_exact(path: Path) -> bool:
    """Return whether *path* exists using the filesystem's native case rules.

    This does not scan for differently cased names. On Unix that means the
    stored case must match the on-disk name.
    """
    try:
        return path.exists()
    except OSError:
        return False


def clear_write_protect(path: Path) -> int:
    """Allow the current user to write *path*. Returns the previous mode."""
    previous_mode = path.stat().st_mode
    os.chmod(path, previous_mode | stat.S_IWUSR)
    return previous_mode


def restore_file_mode(path: Path, mode: int) -> None:
    """Restore a mode previously returned by clear_write_protect."""
    os.chmod(path, mode)


def documents_directory() -> Path | None:
    """User Documents folder for the current OS, or None if it cannot be determined."""
    if IS_WINDOWS:
        return _windows_documents_directory()

    xdg = os.environ.get("XDG_DOCUMENTS_DIR")
    if xdg:
        documents = Path(xdg).expanduser()
        if path_exists_exact(documents):
            return documents

    xdg_user_dir = _xdg_user_dir("DOCUMENTS")
    if xdg_user_dir is not None:
        return xdg_user_dir

    for candidate in (
        Path.home() / "Documents",
        Path.home() / "My Documents",
    ):
        if path_exists_exact(candidate):
            return candidate
    return Path.home() / "Documents"


def _windows_documents_directory() -> Path | None:
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        logger.exception("Windows shell APIs are unavailable.")
        return None

    CSIDL_PERSONAL = 5
    SHGFP_TYPE_CURRENT = 0
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    result = ctypes.windll.shell32.SHGetFolderPathW(
        None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
    if result != 0 or not buf.value:
        logger.error("SHGetFolderPathW did not return a Documents path.")
        return None
    return Path(buf.value)


def _xdg_user_dir(user_dir: str) -> Path | None:
    try:
        completed = subprocess.run(
            ["xdg-user-dir", user_dir],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    if not value:
        return None
    path = Path(value)
    return path if path_exists_exact(path) else None


def steam_root_candidates() -> list[Path]:
    """Possible Steam install roots on Unix (exact names, no case folding)."""
    home = Path.home()
    env_roots: list[Path] = []
    for key in ("STEAM_DIR", "STEAMROOT", "STEAM_ROOT"):
        value = os.environ.get(key)
        if value:
            env_roots.append(Path(value).expanduser())

    return [
        *env_roots,
        home / ".steam" / "steam",
        home / ".steam" / "root",
        home / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        home / "Library" / "Application Support" / "Steam",
        Path("/usr/share/steam"),
    ]


def iter_steam_libraries() -> list[Path]:
    """Steam library folders discovered from libraryfolders.vdf."""
    libraries: list[Path] = []
    seen: set[Path] = set()
    for root in steam_root_candidates():
        if not path_exists_exact(root):
            continue
        resolved = root
        try:
            resolved = root.resolve()
        except OSError:
            pass
        if resolved in seen:
            continue
        seen.add(resolved)
        libraries.append(resolved)
        vdf = resolved / "steamapps" / "libraryfolders.vdf"
        if not path_exists_exact(vdf):
            continue
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            logger.exception("Unable to read %s", vdf)
            continue
        for match in _LIBRARYFOLDERS_PATH_RE.finditer(text):
            library = Path(match.group(1).replace("\\\\", "/"))
            if path_exists_exact(library) and library.resolve() not in seen:
                seen.add(library.resolve())
                libraries.append(library.resolve())
    return libraries


def windows_registry_install_path(game_name: str) -> str | None:
    """Read Bethesda's install path from the Windows registry. Never called on Unix."""
    if not IS_WINDOWS:
        return None

    key_name = _WINREG_KEY_NAMES.get(game_name)
    if not key_name:
        logger.error("%s is not in the list of known registry locations.", game_name)
        return None

    try:
        import winreg
    except ImportError:
        logger.exception("winreg is unavailable on this Windows Python.")
        return None

    registry_path = rf"SOFTWARE\WOW6432Node\Bethesda Softworks\{key_name}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as reg_handle:
            value, value_type = winreg.QueryValueEx(reg_handle, "Installed Path")
    except OSError:
        logger.exception(
            "Game path not found in the registry. Run the %s launcher to set it.",
            game_name,
        )
        return None

    if value and value_type == winreg.REG_SZ and isinstance(value, str):
        return value
    return None


def steam_game_install_directory(game_name: str) -> Path | None:
    """Locate a Steam common/ install directory using exact folder names."""
    install_dirs = GAME_STEAM_INSTALL_DIRS.get(game_name, (game_name,))
    for library in iter_steam_libraries():
        common = library / "steamapps" / "common"
        if not path_exists_exact(common):
            continue
        for folder_name in install_dirs:
            candidate = common / folder_name
            if path_exists_exact(candidate):
                return candidate
    return None


def proton_documents_game_directory(game_name: str, documents_folder_name: str) -> Path | None:
    """Locate Documents/My Games/<game> inside a Steam Proton prefix."""
    if not documents_folder_name:
        return None
    app_ids = GAME_STEAM_APP_IDS.get(game_name, ())
    relative = Path("pfx") / "drive_c" / "users" / "steamuser" / "Documents" / "My Games" / documents_folder_name
    for library in iter_steam_libraries():
        compatdata = library / "steamapps" / "compatdata"
        if not path_exists_exact(compatdata):
            continue
        for app_id in app_ids:
            candidate = compatdata / app_id / relative
            if path_exists_exact(candidate):
                return candidate
    return None


def wine_documents_game_directory(documents_folder_name: str) -> Path | None:
    """Locate Documents/My Games/<game> in a default Wine prefix."""
    if not documents_folder_name:
        return None
    wineprefix = Path(os.environ.get("WINEPREFIX", Path.home() / ".wine")).expanduser()
    users_dir = wineprefix / "drive_c" / "users"
    if not path_exists_exact(users_dir):
        return None
    try:
        user_names = [p.name for p in users_dir.iterdir() if p.is_dir()]
    except OSError:
        return None
    preferred = []
    username = os.environ.get("USER") or os.environ.get("USERNAME")
    if username:
        preferred.append(username)
    preferred.extend(["steamuser", "user"])
    ordered = [name for name in preferred if name in user_names]
    ordered.extend(name for name in user_names if name not in ordered)
    for name in ordered:
        candidate = users_dir / name / "Documents" / "My Games" / documents_folder_name
        if path_exists_exact(candidate):
            return candidate
    return None


def native_documents_game_directory(documents_folder_name: str) -> Path | None:
    """Documents/My Games/<game> under the user's native Documents folder."""
    if not documents_folder_name:
        return None
    documents = documents_directory()
    if documents is None:
        return None
    candidate = documents / "My Games" / documents_folder_name
    if path_exists_exact(candidate):
        return candidate
    return candidate if path_exists_exact(documents) else None


def detect_game_config_directory(game_name: str, documents_folder_name: str) -> Path | None:
    """Autodetect the INI/config folder without using the Windows registry on Unix."""
    if IS_WINDOWS:
        documents = documents_directory()
        if documents is None or not documents_folder_name:
            return None
        return documents / "My Games" / documents_folder_name

    for detected in (
        proton_documents_game_directory(game_name, documents_folder_name),
        wine_documents_game_directory(documents_folder_name),
        native_documents_game_directory(documents_folder_name),
    ):
        if detected is not None and path_exists_exact(detected):
            return detected
    return native_documents_game_directory(documents_folder_name)


def detect_game_install_directory(game_name: str) -> str | None:
    """Autodetect the game install folder. Registry is Windows-only."""
    if IS_WINDOWS:
        return windows_registry_install_path(game_name)

    steam_dir = steam_game_install_directory(game_name)
    if steam_dir is not None:
        return str(steam_dir)
    return None
