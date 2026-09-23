r"""
IITB Auto Internet
Version V.1.1.1

CREATED BY ABHISHEK KILANIYA
DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY
For IIT Bombay Community

Copyright (c) 2026 Abhishek Kilaniya
MIT License

Single-EXE IITB Internet authentication utility.

Modes:
- Normal launch: setup / connect / credential management / uninstall.
- --startup: silent automatic connection from Windows Startup.
"""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VERSION = "V.1.1.1"
APP_NAME = "IITB-Auto-Internet"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
APP_EXE = APP_DIR / "IITB Auto Internet.exe"
CONFIG_PATH = APP_DIR / "config.json"
APP_ICON_NAME = "iitb_auto_internetLogo.ico"
APP_ICON = APP_DIR / APP_ICON_NAME

STARTUP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
STARTUP_FILE = STARTUP_DIR / "IITB Auto Internet.lnk"

IITB_SSO_HOST = "internet-sso.iitb.ac.in"
IITB_HOST = "internet.iitb.ac.in"
IITB_IP = "10.201.250.201"
SSO_IP = "10.200.1.100"
LOGIN_URL = f"https://{IITB_SSO_HOST}/login.php"
TEST_URLS = [
    "https://www.google.com/generate_204",
    "https://www.gstatic.com/generate_204",
]

GREEN = "\033[92m"
WHITE = "\033[97m"
RED = "\033[91m"
RESET = "\033[0m"


def enable_ansi():
    try:
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            k.SetConsoleMode(h, mode.value | 0x0004)
    except Exception:
        pass


def powershell(command, env=None, timeout=15):
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def encrypt_token(token):
    command = "$s = ConvertTo-SecureString $env:IITB_TOKEN -AsPlainText -Force; ConvertFrom-SecureString $s"
    env = os.environ.copy()
    env["IITB_TOKEN"] = token
    r = powershell(command, env=env)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(r.stderr.strip() or "Could not encrypt token.")
    return r.stdout.strip()


def decrypt_token(encrypted):
    command = (
        "$s = ConvertTo-SecureString $env:IITB_ENCRYPTED_TOKEN; "
        "$b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); "
        "try {[Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)} "
        "finally {[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)}"
    )
    env = os.environ.copy()
    env["IITB_ENCRYPTED_TOKEN"] = encrypted
    r = powershell(command, env=env)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(r.stderr.strip() or "Could not decrypt token.")
    return r.stdout.strip()


def bundled_icon():
    if getattr(sys, "frozen", False):
        p = Path(sys._MEIPASS) / APP_ICON_NAME
        if p.exists():
            return p
    p = Path(__file__).resolve().parent / APP_ICON_NAME
    return p if p.exists() else None


def desktop_dir():
    """Return the real Windows Desktop directory, including redirected/OneDrive desktops."""
    try:
        CSIDL_DESKTOPDIRECTORY = 0x0010
        buf = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buf) == 0:
            return Path(buf.value)
    except Exception:
        pass
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def create_shortcut(path, target, description, arguments=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    command = (
        "$ws=New-Object -ComObject WScript.Shell; "
        "$sc=$ws.CreateShortcut($env:S); "
        "$sc.TargetPath=$env:T; "
        "$sc.Arguments=$env:A; "
        "$sc.WorkingDirectory=$env:W; "
        "$sc.Description=$env:D; "
        "$sc.IconLocation=$env:I; "
        "$sc.Save()"
    )
    env = os.environ.copy()
    env.update(
        {
            "S": str(path),
            "T": str(target),
            "A": arguments,
            "W": str(APP_DIR),
            "D": description,
            "I": f"{APP_ICON},0",
        }
    )
    r = powershell(command, env=env)
    if r.returncode != 0 or not path.exists():
        raise RuntimeError(r.stderr.strip() or f"Could not create shortcut: {path}")


def remove_file(path):
    try:
        p = Path(path)
        if p.exists() or p.is_symlink():
            p.unlink()
    except Exception:
        pass


def save_config(username, encrypted):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps({"username": username, "token_encrypted": encrypted}, indent=4),
        encoding="utf-8",
    )
    try:
        account = os.environ.get("USERDOMAIN", os.environ.get("COMPUTERNAME", "")) + "\\" + os.environ["USERNAME"]
        subprocess.run(
            ["icacls", str(CONFIG_PATH), "/inheritance:r", "/grant:r", f"{account}:R"],
            capture_output=True,
            text=True,
        )
    except Exception:
        pass


def load_credentials():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("Credentials are not configured yet.")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    username = str(config["username"]).strip()
    encrypted = config["token_encrypted"]
    if not username or not encrypted:
        raise RuntimeError("Saved credential data is incomplete.")
    return username, decrypt_token(encrypted)


def wifi_connected():
    command = r"""
$wifi = Get-NetAdapter -Physical -ErrorAction SilentlyContinue |
    Where-Object { $_.Status -eq 'Up' -and ($_.NdisPhysicalMedium -eq 1 -or $_.NdisPhysicalMedium -eq 9) } |
    Select-Object -First 1
if ($null -ne $wifi) { 'CONNECTED' } else { 'DISCONNECTED' }
"""
    try:
        r = powershell(command, timeout=10)
        return r.stdout.strip().upper() == "CONNECTED"
    except Exception:
        return False


def iitb_network_ready():
    try:
        r = subprocess.run(
            [
                "curl", "-sS", "-o", "NUL", "-w", "%{http_code}",
                "--resolve", f"{IITB_SSO_HOST}:443:{IITB_IP}",
                "--connect-timeout", "1.5", "--max-time", "3", LOGIN_URL,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        code = r.stdout.strip()
        return code.startswith("2") or code.startswith("3")
    except Exception:
        return False


def wait_for_iitb_network_ready(max_wait=20):
    print("[INFO] Waiting for IITB network path to become ready...")
    deadline = time.monotonic() + max_wait
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        if iitb_network_ready():
            print("[OK] IITB network path is ready.")
            return True
        remaining = max(0, int(deadline - time.monotonic()))
        print(f"[INFO] Network is still initializing (attempt {attempt}, ~{remaining}s remaining)...")
        time.sleep(1)
    print(f"{RED}[ERROR] IITB network path did not become ready within {max_wait} seconds.{GREEN}")
    return False


def internet_available():
    # A real connectivity check must receive HTTP 204.
    # Do not follow redirects, so an IITB/login redirect is not mistaken for Internet access.
    for url in TEST_URLS:
        try:
            r = subprocess.run(
                [
                    "curl", "-sS", "-o", "NUL", "-w", "%{response_code}",
                    "--connect-timeout", "2", "--max-time", "4", url,
                ],
                capture_output=True,
                text=True,
                timeout=6,
            )
            if r.stdout.strip() == "204":
                return True
        except Exception:
            pass
    return False


def login_to_iitb(username, token, verbose=True):
    try:
        r = subprocess.run(
            [
                "curl", "-sS",
                "--resolve", f"{IITB_SSO_HOST}:443:{IITB_IP}",
                "--resolve", f"{IITB_HOST}:443:{IITB_IP}",
                "--resolve", f"sso.iitb.ac.in:443:{SSO_IP}",
                "--location-trusted", "-u", f"{username}:{token}", LOGIN_URL,
                "-o", "NUL", "-w", "%{response_code}\\n",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        code = r.stdout.strip()
        if not code:
            if verbose:
                print(f"{RED}[ERROR] No HTTP response from IITB authentication server.{GREEN}")
                if r.stderr:
                    print(r.stderr.strip())
            return False, code, "No HTTP response was received."
        if code.startswith("4"):
            if verbose:
                print(f"{RED}[ERROR] IITB authentication rejected the credentials (HTTP {code}).{GREEN}")
            return False, code, "The IITB SSO server did not accept the supplied LDAP ID / Access Token."
        if code.startswith("5"):
            if verbose:
                print(f"{RED}[ERROR] IITB authentication server returned HTTP {code}.{GREEN}")
            return False, code, "The IITB SSO server returned a server-side error."
        if not code.startswith("2"):
            if verbose:
                print(f"{RED}[ERROR] Unexpected IITB authentication response: HTTP {code}.{GREEN}")
            return False, code, "Unexpected HTTP response from IITB."
        if verbose:
            print(f"[OK] IITB authentication endpoint returned HTTP {code}.")
        return True, code, ""
    except subprocess.TimeoutExpired:
        if verbose:
            print(f"{RED}[ERROR] IITB authentication timed out.{GREEN}")
        return False, "", "IITB authentication timed out."
    except Exception as exc:
        if verbose:
            print(f"{RED}[ERROR] {exc}{GREEN}")
        return False, "", str(exc)


def verify_internet(max_attempts=10, delays=None):
    if delays is None:
        delays = [0, 0.5, 1, 1, 1, 2, 2, 2, 2, 2]
    for attempt, delay in enumerate(delays[:max_attempts], 1):
        if delay:
            time.sleep(delay)
        print(f"[INFO] Internet check {attempt}/{min(max_attempts, len(delays))}...")
        if internet_available():
            return True
    return False


def credentials_and_internet_test(username, token):
    """Authenticate and then verify actual Internet access before credentials are saved."""
    print("[1] Testing IITB credentials...")
    ok, code, message = login_to_iitb(username, token)
    if not ok:
        print(f"{RED}[ERROR] IITB authentication was not accepted.{GREEN}")
        print(f"HTTP status: {code or 'N/A'}")
        print(message)
        return False

    print("[2] Verifying actual Internet access...")
    if verify_internet():
        print(f"{GREEN}[OK] Actual Internet access confirmed.{GREEN}")
        return True

    print(f"{RED}[ERROR] IITB endpoint accepted the request, but actual Internet access could not be verified.{GREEN}")
    print("Credentials were NOT saved.")
    return False


def ensure_installed():
    """Copy this EXE and its bundled icon into the permanent per-user install directory."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Installation requires the compiled EXE.")

    source_exe = Path(sys.executable).resolve()
    icon = bundled_icon()
    if icon is None:
        raise FileNotFoundError("iitb_auto_internetLogo.ico was not found in the EXE.")

    APP_DIR.mkdir(parents=True, exist_ok=True)
    if source_exe != APP_EXE.resolve():
        shutil.copy2(source_exe, APP_EXE)
    shutil.copy2(icon, APP_ICON)


def create_app_shortcuts():
    desktop = desktop_dir()
    desktop_shortcut = desktop / "IITB Auto Internet.lnk"
    create_shortcut(desktop_shortcut, APP_EXE, f"IITB Auto Internet {VERSION}")
    STARTUP_DIR.mkdir(parents=True, exist_ok=True)
    create_shortcut(
        STARTUP_FILE,
        APP_EXE,
        f"IITB Auto Internet {VERSION} - Windows Startup",
        "--startup",
    )
    print(f"{GREEN}[OK] Desktop shortcut created.{GREEN}")
    print(f"{GREEN}[OK] Windows Startup shortcut created.{GREEN}")


def prompt_credentials():
    print()
    print("Enter your IITB LDAP ID.")
    username = input("LDAP ID: ").strip()
    if not username:
        print(f"{RED}[ERROR] LDAP ID cannot be empty.{GREEN}")
        return None
    print()
    print("Enter your IITB SSO Access Token.")
    print("The token will be visible while you type/paste it.")
    token = input("SSO Access Token: ").strip()
    if not token:
        print(f"{RED}[ERROR] Token cannot be empty.{GREEN}")
        return None
    return username, token


def setup_credentials():
    pair = prompt_credentials()
    if not pair:
        return False
    username, token = pair
    print()

    # Test first. Do not write config.json until both authentication and real Internet access succeed.
    if not credentials_and_internet_test(username, token):
        return False

    try:
        print("[3] Encrypting credentials...")
        encrypted = encrypt_token(token)
        ensure_installed()
        save_config(username, encrypted)
        create_app_shortcuts()
    except Exception as exc:
        print(f"{RED}[ERROR] Could not complete installation: {exc}{GREEN}")
        return False

    print(f"{GREEN}[OK] Credentials saved securely.{GREEN}")
    print()
    print("IITB Auto Internet is now installed and configured.")
    return True


def update_credentials():
    print()
    print("Updating credentials will replace the currently saved credentials only after a successful test.")
    pair = prompt_credentials()
    if not pair:
        return False
    username, token = pair
    print()
    if not credentials_and_internet_test(username, token):
        return False
    try:
        print("[3] Encrypting and replacing saved credentials...")
        encrypted = encrypt_token(token)
        ensure_installed()
        save_config(username, encrypted)
        create_app_shortcuts()
        print(f"{GREEN}[OK] Credentials updated successfully.{GREEN}")
        return True
    except Exception as exc:
        print(f"{RED}[ERROR] Could not update credentials: {exc}{GREEN}")
        return False


def test_saved_credentials():
    try:
        username, token = load_credentials()
    except Exception as exc:
        print(f"{RED}[ERROR] {exc}{GREEN}")
        return False

    print()
    print("[1] Testing saved credentials with IITB...")
    ok, code, message = login_to_iitb(username, token)
    if not ok:
        print(f"{RED}[ERROR] Saved credentials rejected.{GREEN}")
        print(f"HTTP status: {code or 'N/A'}")
        print(message)
        return False

    print("[2] Verifying actual Internet access...")
    if verify_internet():
        print(f"{GREEN}[OK] Saved credentials passed the Internet verification.{GREEN}")
        return True

    print(f"{RED}[ERROR] Authentication endpoint responded successfully, but Internet access was not verified.{GREEN}")
    return False


def delete_credentials():
    if CONFIG_PATH.exists():
        remove_file(CONFIG_PATH)
        print(f"{GREEN}[OK] Saved credentials deleted.{GREEN}")
    else:
        print("[INFO] No saved credentials were found.")
    print("The application remains installed. You can configure it again anytime.")


def schedule_complete_uninstall():
    desktop = desktop_dir()
    desktop_shortcut = desktop / "IITB Auto Internet.lnk"
    script = Path(tempfile.gettempdir()) / f"iitb_auto_internet_cleanup_{os.getpid()}.cmd"
    lines = [
        "@echo off",
        "timeout /t 2 /nobreak >nul",
        f'del /f /q "{STARTUP_FILE}" >nul 2>&1',
        f'del /f /q "{desktop_shortcut}" >nul 2>&1',
        f'rmdir /s /q "{APP_DIR}" >nul 2>&1',
        'del /f /q "%~f0" >nul 2>&1',
    ]
    script.write_text("\n".join(lines), encoding="utf-8")
    subprocess.Popen(
        ["cmd.exe", "/c", str(script)],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        close_fds=True,
    )


def uninstall():
    print()
    print("======================================================")
    print("          REMOVE IITB AUTO INTERNET")
    print("======================================================")
    print()
    print("This will remove:")
    print("  - Saved LDAP ID / encrypted SSO token")
    print("  - Installed IITB Auto Internet files")
    print("  - Desktop shortcut")
    print("  - Windows Startup shortcut")
    print(f"  - {APP_DIR}")
    print()
    print("Your downloaded ZIP/release files are NOT deleted.")
    print()
    confirm = input("Type REMOVE to continue: ").strip()
    if confirm != "REMOVE":
        print("Removal cancelled.")
        return False
    schedule_complete_uninstall()
    print()
    print("Removal scheduled. This window will close now.")
    return True


def run_auto_login(startup_mode=False):
    print()
    print("======================================================")
    print(f"             IITB AUTO INTERNET ({VERSION})")
    print("======================================================")
    print()
    print("CREATED BY ABHISHEK KILANIYA")
    print("DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY")
    print("For IIT Bombay Community")
    print()

    print("[1] Waiting for Wi-Fi connection...")
    while not wifi_connected():
        time.sleep(5)
    print("[OK] Wi-Fi connected.")
    print()

    if not wait_for_iitb_network_ready():
        return False

    print()
    print("[2] Checking Internet...")
    if internet_available():
        print("[OK] Internet is already available. No IITB authentication required.")
        return True
    print("[INFO] Internet is unavailable.")

    try:
        username, token = load_credentials()
    except Exception as exc:
        if startup_mode:
            print("[INFO] IITB Auto Internet is not configured yet. Run the app manually once to set it up.")
        else:
            print(f"{RED}[ERROR] {exc}{GREEN}")
        return False

    print()
    print("[3] Authenticating with IITB...")
    ok, _, _ = login_to_iitb(username, token)
    if not ok:
        if startup_mode:
            print("[INFO] Authentication failed. Run IITB Auto Internet manually to update/test credentials.")
        return False

    print()
    print("[4] Verifying Internet access...")
    if verify_internet():
        print()
        print("======================================================")
        print("                INTERNET IS READY")
        print("======================================================")
        return True

    print()
    print("======================================================")
    print(f"{RED}              INTERNET CONNECTION FAILED{GREEN}")
    print("======================================================")
    print()
    print("[ERROR] IITB authentication was accepted, but actual Internet access could not be verified.")
    return False


def menu():
    configured = CONFIG_PATH.exists()
    print()
    print("======================================================")
    print(f"             IITB AUTO INTERNET ({VERSION})")
    print("======================================================")
    print()
    print("CREATED BY ABHISHEK KILANIYA")
    print("DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY")
    print("For IIT Bombay Community")
    print()
    print(f"Status: {'CONFIGURED' if configured else 'NOT CONFIGURED'}")
    print()

    if not configured:
        print("1. Set up credentials")
        print("2. Exit")
        choice = input("\nChoose an option: ").strip()
        if choice == "1":
            setup_credentials()
        return False

    print("1. Connect to IITB Internet now")
    print("2. Update credentials")
    print("3. Test saved credentials")
    print("4. Delete saved credentials")
    print("5. Remove IITB Auto Internet")
    print("6. Exit")
    choice = input("\nChoose an option: ").strip()

    if choice == "1":
        run_auto_login(startup_mode=False)
        return False
    elif choice == "2":
        update_credentials()
        return False
    elif choice == "3":
        test_saved_credentials()
        return False
    elif choice == "4":
        delete_credentials()
        return False
    elif choice == "5":
        return uninstall()
    return False


def main():
    enable_ansi()
    startup_mode = "--startup" in sys.argv[1:]
    skip_pause = False
    try:
        if startup_mode:
            # Startup is intentionally silent about setup/menu. If not configured, simply exit.
            run_auto_login(startup_mode=True)
        else:
            uninstall_scheduled = menu()
            if uninstall_scheduled:
                skip_pause = True
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as exc:
        print(f"{RED}[ERROR] {exc}{GREEN}")
    finally:
        if not startup_mode and not skip_pause:
            print()
            input("Press Enter to exit...")


if __name__ == "__main__":
    main()
