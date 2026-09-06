# wifi-qr

Generate a QR code that encodes WiFi credentials — the kind you scan with a
phone camera to join a network — and decode such an image back into its
credentials.

## Setup

```sh
cd wifi-qr
pip install -r requirements.txt
```

## Generate

Manual mode — pass the credentials explicitly:

```sh
python generate.py --ssid "My Network" --password "hunter2" --auth WPA
```

Expected output:

```
Payload: WIFI:S:My Network;T:WPA;P:hunter2;H:false;;
Saved QR code to wifi-qr.png
```

Auto mode — detect the currently connected network instead:

```sh
python generate.py --auto
```

Expected output (on Linux, running with sudo):

```
Detected network: 'My Network'
Payload: WIFI:S:My Network;T:WPA;P:hunter2;H:false;;
Saved QR code to wifi-qr.png
```

If detection fails (missing privileges, no active connection, unsupported OS),
the script says why and falls back to prompting for manual input.

Other options: `--auth {WPA,WEP,nopass}`, `--hidden` for networks that don't
broadcast their SSID, `--output name.svg` for SVG instead of the default PNG,
`--scale` for the module size.

## Decode

```sh
python decode.py wifi-qr.png     # or: python decode.py --webcam
```

Expected output:

```
Raw payload: WIFI:S:My Network;T:WPA;P:hunter2;H:false;;
SSID:     My Network
Auth:     WPA
Password: hunter2
Hidden:   false
```

## The WIFI: payload format

The payload is a de-facto standard (popularized by the ZXing project) of the
form `WIFI:S:<ssid>;T:<auth>;P:<password>;H:<true|false>;;` — a flat list of
`key:value` fields terminated by `;`, where `S` is the network name, `T` the
authentication type (`WPA` covers WPA/WPA2/WPA3-personal, `WEP` is legacy,
`nopass` means an open network), `P` the password, and `H` whether the SSID is
hidden. Because `;`, `,`, `:` and `\` are structural characters, they must be
backslash-escaped when they appear inside the SSID or password — that escaping
(and undoing it when decoding) is most of what these two scripts actually do
beyond calling a QR library.

## `--auto` platform notes

Auto-detection reads the *stored* WiFi password from the OS, so each platform
imposes its own access rules — behavior is deliberately not identical:

- **Linux (NetworkManager)**: reading the PSK (via `nmcli -s` or the profiles
  under `/etc/NetworkManager/system-connections/`) requires elevated
  privileges. Without them the script tells you to re-run with `sudo`.
- **macOS**: the password lives in the Keychain; `security
  find-generic-password` triggers a Keychain access prompt unless it was
  pre-authorized. That prompt is macOS protecting the secret — the script does
  not (and should not) try to suppress it.
- **Windows**: `netsh wlan show profile name="<ssid>" key=clear` generally
  works without admin rights for profiles created by the current user.
- **WSL**: reports itself as Linux, but the WiFi adapter (and its stored
  credentials) belong to Windows — the script detects WSL and calls
  `netsh.exe` through the interop bridge instead of NetworkManager. Requires
  Windows interop enabled (it is by default).

On any failure the script falls back to manual input rather than crashing.
