"""Detect the SSID and password of the currently connected WiFi network.

Each operating system stores WiFi credentials differently, so there is one
clearly separated function per OS plus a `detect()` dispatcher. All three
shell out to the platform's own tooling rather than reading undocumented
formats:

- Linux:   nmcli (NetworkManager) — reading the PSK needs elevated privileges
- macOS:   networksetup + the `security` Keychain CLI — triggers a Keychain
           access prompt unless pre-authorized
- Windows: netsh — usually works without admin rights

Every failure path raises DetectionError with a human-readable reason, so the
caller can fall back to manual input instead of crashing.
"""

import platform
import subprocess
from pathlib import Path


class DetectionError(Exception):
    """Auto-detection failed; the message says why and what to try instead."""


def _run(cmd: list[str]) -> str:
    """Run a command and return stripped stdout, mapping every failure mode
    (missing binary, non-zero exit) to DetectionError."""
    try:
        # check=False: we turn a non-zero exit into DetectionError ourselves.
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15, check=False
        )
    except FileNotFoundError:
        raise DetectionError(f"`{cmd[0]}` is not available on this system") from None
    except subprocess.TimeoutExpired:
        raise DetectionError(f"`{' '.join(cmd)}` timed out") from None
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise DetectionError(f"`{' '.join(cmd)}` failed: {detail}")
    return result.stdout.strip()


def detect_linux() -> tuple[str, str]:
    """NetworkManager: SSID from `nmcli dev wifi`, PSK from the connection
    profile. Both PSK paths require elevated privileges."""
    # -t = terse (machine-readable, colon-separated, backslash-escaped).
    output = _run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
    ssid = ""
    for line in output.splitlines():
        if line.startswith("yes:"):
            ssid = line[len("yes:"):].replace("\\:", ":").replace("\\\\", "\\")
            break
    if not ssid:
        raise DetectionError("no active WiFi connection found (nmcli)")

    # -s = show secrets; without root/polkit authorization this returns an
    # empty string or an access error.
    try:
        password = _run(
            ["nmcli", "-s", "-g", "802-11-wireless-security.psk",
             "connection", "show", ssid]
        )
    except DetectionError:
        password = ""
    if password:
        return ssid, password

    # Fallback: the connection profiles on disk, readable by root only.
    try:
        for profile in Path("/etc/NetworkManager/system-connections").glob(
            "*.nmconnection"
        ):
            text = profile.read_text()
            if f"ssid={ssid}" in text:
                for line in text.splitlines():
                    if line.startswith("psk="):
                        return ssid, line[len("psk="):]
    except PermissionError:
        raise DetectionError(
            f"found network {ssid!r} but reading its password requires "
            "elevated privileges — re-run with sudo"
        ) from None
    raise DetectionError(
        f"found network {ssid!r} but could not read its password "
        "(open network, or missing privileges — try re-running with sudo)"
    )


def detect_macos() -> tuple[str, str]:
    """SSID via networksetup, password via the login Keychain. The `security`
    call pops a Keychain access prompt unless it was pre-authorized — that is
    macOS protecting the stored password, not a bug, and we don't suppress it."""
    output = _run(["networksetup", "-getairportnetwork", "en0"])
    # Expected: "Current Wi-Fi Network: <ssid>"
    prefix = "Current Wi-Fi Network: "
    if prefix not in output:
        raise DetectionError(f"no active WiFi connection found on en0: {output}")
    ssid = output.split(prefix, 1)[1].strip()

    password = _run(
        ["security", "find-generic-password",
         "-D", "AirPort network password", "-a", ssid, "-w"]
    )
    return ssid, password


def detect_windows() -> tuple[str, str]:
    """Both SSID and password via netsh; `key=clear` generally works without
    admin rights for profiles the current user created."""
    output = _run(["netsh", "wlan", "show", "interfaces"])
    ssid = ""
    for line in output.splitlines():
        stripped = line.strip()
        # Match "SSID : name" but not "BSSID : aa:bb:...".
        if stripped.startswith("SSID") and not stripped.startswith("BSSID"):
            ssid = stripped.split(":", 1)[1].strip()
            break
    if not ssid:
        raise DetectionError("no active WiFi connection found (netsh)")

    output = _run(["netsh", "wlan", "show", "profile", f"name={ssid}", "key=clear"])
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Key Content"):
            return ssid, stripped.split(":", 1)[1].strip()
    raise DetectionError(
        f"found network {ssid!r} but netsh did not reveal a key "
        "(open network, or the profile belongs to another user)"
    )


def detect() -> tuple[str, str]:
    """Dispatch to the right OS implementation; raises DetectionError when
    the OS is unsupported or detection fails."""
    system = platform.system()
    if system == "Linux":
        return detect_linux()
    if system == "Darwin":
        return detect_macos()
    if system == "Windows":
        return detect_windows()
    raise DetectionError(f"unsupported operating system: {system!r}")
