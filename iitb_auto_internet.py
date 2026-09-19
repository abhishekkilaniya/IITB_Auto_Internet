r"""
IITB Auto Internet Login
Single-file Windows application

CREATED BY ABHISHEK KILANIYA
DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY
For IIT Bombay Community

Copyright (c) 2026 Abhishek Kilaniya

This project is open source and released under the MIT License.
You are free to use, modify, and distribute this software,
subject to the terms of the MIT License.

Please retain the original copyright and attribution.
"""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

APP_NAME = "IITB-Auto-Internet"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
APP_EXE = APP_DIR / "IITB-Auto-Internet.exe"
UNINSTALLER_NAME = "IITB-Auto-Internet-Uninstaller.exe"
CONFIG_PATH = APP_DIR / "config.json"
APP_ICON_NAME = "iitb_auto_internetLogo.ico"
APP_ICON = APP_DIR / APP_ICON_NAME

STARTUP_DIR = (
    Path(os.environ["APPDATA"])
    / "Microsoft"
    / "Windows"
    / "Start Menu"
    / "Programs"
    / "Startup"
)
STARTUP_FILE = STARTUP_DIR / "IITB Auto Internet Login.lnk"
DESKTOP_FILE = None

IITB_SSO_HOST = "internet-sso.iitb.ac.in"
IITB_HOST = "internet.iitb.ac.in"
IITB_IP = "10.201.250.201"

LOGIN_URL = f"https://{IITB_SSO_HOST}/login.php"
TEST_URL = "https://www.google.com/generate_204"

GREEN = "\033[92m"
WHITE = "\033[97m"
RED = "\033[91m"
RESET = "\033[0m"


def enable_ansi():
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def start_color():
    enable_ansi()
    print(GREEN, end="")


def stop_color():
    print(RESET, end="")


def powershell(command, env=None, timeout=15):
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def encrypt_token(token):
    command = (
        "$s = ConvertTo-SecureString $env:IITB_TOKEN -AsPlainText -Force; "
        "ConvertFrom-SecureString $s"
    )
    env = os.environ.copy()
    env["IITB_TOKEN"] = token

    result = powershell(command, env=env)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or "Could not encrypt token.")

    return result.stdout.strip()


def decrypt_token(encrypted_token):
    command = (
        "$s = ConvertTo-SecureString $env:IITB_ENCRYPTED_TOKEN; "
        "$b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); "
        "try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } "
        "finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }"
    )
    env = os.environ.copy()
    env["IITB_ENCRYPTED_TOKEN"] = encrypted_token

    result = powershell(command, env=env)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not decrypt token.")

    token = result.stdout.strip()
    if not token:
        raise RuntimeError("Decrypted token is empty.")

    return token

def install_icon():
    if not getattr(sys, "frozen", False):
        return

    bundled_icon = Path(sys._MEIPASS) / APP_ICON_NAME

    if not bundled_icon.exists():
        raise FileNotFoundError(
            f"Bundled icon not found: {bundled_icon}"
        )

    APP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled_icon, APP_ICON)

def create_shortcut(shortcut_path, target, arguments=""):
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)

    target_path = Path(target)
    actual_target = str(target_path)
    actual_arguments = arguments

    command = (
        "$ws = New-Object -ComObject WScript.Shell; "
        "$sc = $ws.CreateShortcut($env:IITB_SHORTCUT); "
        "$sc.TargetPath = $env:IITB_TARGET; "
        "$sc.Arguments = $env:IITB_ARGUMENTS; "
        "$sc.WorkingDirectory = $env:IITB_WORKDIR; "
        "$sc.Description = 'IITB Auto Internet Login - CREATED BY ABHISHEK KILANIYA'; "
        "$sc.IconLocation = $env:IITB_ICON; "
        "$sc.Save(); "
        "if (-not (Test-Path -LiteralPath $env:IITB_SHORTCUT)) { exit 2 }"
    )

    env = os.environ.copy()
    env["IITB_SHORTCUT"] = str(shortcut_path)
    env["IITB_TARGET"] = actual_target
    env["IITB_ARGUMENTS"] = actual_arguments
    env["IITB_WORKDIR"] = str(APP_DIR)
    env["IITB_ICON"] = f"{APP_ICON},0"

    result = powershell(command, env=env, timeout=15)
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or
            f"Could not create shortcut: {shortcut_path}"
        )

    if not shortcut_path.exists():
        raise RuntimeError(f"Shortcut was not created: {shortcut_path}")


def get_desktop_path():
    try:
        result = powershell(
            r"[Environment]::GetFolderPath('Desktop')",
            timeout=10,
        )
        desktop = result.stdout.strip()
        if result.returncode == 0 and desktop:
            return Path(desktop)
    except Exception:
        pass

    return Path(os.environ["USERPROFILE"]) / "Desktop"


def pause_before_exit():
    print()
    print(f"{WHITE}Press any key to exit...{GREEN}")
    try:
        os.system("pause >nul")
    except Exception:
        input()

def save_config(username, encrypted_token):
    APP_DIR.mkdir(parents=True, exist_ok=True)

    config = {
        "username": username,
        "token_encrypted": encrypted_token,
    }

    CONFIG_PATH.write_text(
        json.dumps(config, indent=4),
        encoding="utf-8",
    )

    try:
        account = (
            os.environ.get("USERDOMAIN", os.environ.get("COMPUTERNAME", ""))
            + "\\"
            + os.environ["USERNAME"]
        )
        subprocess.run(
            [
                "icacls",
                str(CONFIG_PATH),
                "/inheritance:r",
                "/grant:r",
                f"{account}:R",
            ],
            capture_output=True,
            text=True,
        )
    except Exception:
        pass


def create_standalone_uninstaller():
    if not getattr(sys, "frozen", False):
        raise RuntimeError("The standalone uninstaller can only be created from the compiled EXE.")

    current_exe = Path(sys.executable).resolve()
    uninstaller = current_exe.parent / UNINSTALLER_NAME

    if current_exe == uninstaller:
        return uninstaller

    shutil.copy2(current_exe, uninstaller)
    return uninstaller


def remove_path_quietly(path):
    try:
        p = Path(path)
        if p.exists() or p.is_symlink():
            p.unlink()
    except Exception:
        pass


def run_uninstaller():
    start_color()

    print()
    print("======================================================")
    print("          IITB AUTO INTERNET - UNINSTALL")
    print("======================================================")
    print()
    print(f"{WHITE}CREATED BY ABHISHEK KILANIYA{GREEN}")
    print(f"{WHITE}DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY{GREEN}")
    print(f"{WHITE}For IIT Bombay Community{GREEN}")
    print()
    print(f"{RED}WARNING: This will completely remove IITB Auto Internet.")
    print("It will delete the installed application and stored credentials.")
    print(f"{GREEN}")
    print("Application folder:")
    print(f"  {APP_DIR}")
    print()

    confirm = input("Type UNINSTALL to continue: ").strip()

    if confirm != "UNINSTALL":
        print(f"{RED}Uninstall cancelled.{GREEN}")
        pause_before_exit()
        return

    print()
    print("[1] Removing Desktop shortcut...")
    try:
        remove_path_quietly(
            get_desktop_path() / "IITB Auto Internet Login.lnk"
        )
    except Exception as exc:
        print(f"{RED}[WARNING] Could not remove Desktop shortcut: {exc}{GREEN}")

    print("[2] Removing Windows Startup shortcut...")
    try:
        remove_path_quietly(STARTUP_FILE)
    except Exception as exc:
        print(f"{RED}[WARNING] Could not remove Startup shortcut: {exc}{GREEN}")

    print("[3] Removing installed application and credentials...")

    try:
        if APP_DIR.exists():
            shutil.rmtree(APP_DIR)
    except Exception as exc:
        print(f"{RED}[ERROR] Could not delete application folder: {exc}{GREEN}")
        print("Make sure IITB-Auto-Internet.exe is not currently running.")
        pause_before_exit()
        return

    if APP_DIR.exists():
        print(f"{RED}[ERROR] Application folder still exists: {APP_DIR}{GREEN}")
        pause_before_exit()
        return

    print()
    print("======================================================")
    print("             UNINSTALL COMPLETE")
    print("======================================================")
    print()
    print("IITB Auto Internet has been completely removed.")
    print("Stored credentials have also been deleted.")
    print()
    print("The uninstaller itself remains in the release folder")
    print("so it can be used again if required.")
    pause_before_exit()


def setup_first_run():
    global DESKTOP_FILE
    DESKTOP_FILE = get_desktop_path() / "IITB Auto Internet Login.lnk"
    print()
    print("======================================================")
    print("    IITB AUTO INTERNET LOGIN - SETUP (V.1.0 Beta)")
    print("======================================================")
    print()
    print(f"{WHITE}CREATED BY ABHISHEK KILANIYA{GREEN}")
    print(f"{WHITE}DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY{GREEN}")
    print(f"{WHITE}For IIT Bombay Community{GREEN}")
    print()

    username = input("Enter your IITB LDAP ID: ").strip()
    if not username:
        print(f"{RED}ERROR: LDAP ID cannot be empty.{GREEN}")
        return False

    print()
    print("Enter your IITB SSO Access Token.")
    print("The token is visible while you type/paste it.")
    print("It will be encrypted immediately after entry.")
    print()

    token = input("Enter your IITB SSO Access Token: ").strip()
    if not token:
        print(f"{RED}ERROR: Token cannot be empty.{GREEN}")
        return False

    print()
    print("Preparing IITB Auto Internet Login...")

    try:
        encrypted = encrypt_token(token)
    except Exception as exc:
        print(f"{RED}ERROR: Could not encrypt token: {exc}{GREEN}")
        return False

    current_exe = Path(sys.executable).resolve()

    if not getattr(sys, "frozen", False):
        print(f"{RED}ERROR: This single-file setup must be compiled to an EXE.")
        print("Run the Python source with Python only for development/testing.")
        print("For normal use, build/run the compiled EXE.{GREEN}")
        return False

    APP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        install_icon()
    except Exception as exc:
        print(f"{RED}ERROR: Could not install application icon: {exc}{GREEN}")
        return False

    if current_exe != APP_EXE:
        try:
            shutil.copy2(current_exe, APP_EXE)
        except Exception as exc:
            print(f"{RED}ERROR: Could not install the application: {exc}{GREEN}")
            return False

    try:
        uninstaller_path = create_standalone_uninstaller()
        print(f"[OK] Uninstaller created: {uninstaller_path}")
    except Exception as exc:
        print(f"{RED}ERROR: Could not create uninstaller: {exc}{GREEN}")
        return False

    save_config(username, encrypted)

    try:
        create_shortcut(
            DESKTOP_FILE,
            APP_EXE,
            "--run",
        )
        print(f"[OK] Desktop shortcut created: {DESKTOP_FILE}")
    except Exception as exc:
        print(f"{RED}ERROR: Could not create Desktop shortcut: {exc}{GREEN}")
        return False

    try:
        STARTUP_DIR.mkdir(parents=True, exist_ok=True)
        create_shortcut(
            STARTUP_FILE,
            APP_EXE,
            "--run",
        )
        print(f"[OK] Windows Startup shortcut created: {STARTUP_FILE}")
    except Exception as exc:
        print(f"{RED}ERROR: Could not create Startup shortcut: {exc}{GREEN}")
        return False

    print()
    print("======================================================")
    print("                 SETUP COMPLETE")
    print("======================================================")
    print()
    print("Desktop shortcut created.")
    print("Startup shortcut created.")
    print("Desktop and Startup shortcuts point directly to the installed EXE.")
    print("Standalone uninstaller was created beside the original EXE.")
    print()
    print("Starting the auto-login once now...")
    print()

    login_success = run_auto_login()
    if not login_success:
        print()
        print(f"{RED}[WARNING] Installation completed, but the initial IITB login did not succeed.{GREEN}")
        print("The application is installed and will retry automatically on its next run.")
    return True


def wifi_connected():
    try:
        command = r"""
$wifi = Get-NetAdapter -Physical -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Status -eq 'Up' -and
        ($_.NdisPhysicalMedium -eq 1 -or $_.NdisPhysicalMedium -eq 9)
    } |
    Select-Object -First 1

if ($null -ne $wifi) { 'CONNECTED' } else { 'DISCONNECTED' }
"""
        result = powershell(command, timeout=10)
        return result.stdout.strip().upper() == "CONNECTED"
    except Exception:
        return False


def internet_available():
    test_urls = [
        TEST_URL,
        "https://www.gstatic.com/generate_204",
    ]

    for url in test_urls:
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "-L",
                    "-o",
                    "NUL",
                    "-w",
                    "%{http_code}",
                    "--max-time",
                    "8",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=12,
            )

            code = result.stdout.strip()
            if code == "204" or code.startswith("2") or code.startswith("3"):
                return True

        except Exception:
            continue

    return False


def load_credentials():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "Credentials are not configured. Run the application once to set them up."
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    username = config["username"]
    token = decrypt_token(config["token_encrypted"])

    return username, token


def login_to_iitb(username, token):
    try:
        result = subprocess.run(
            [
                "curl",
                "--resolve",
                f"{IITB_SSO_HOST}:443:{IITB_IP}",
                "--resolve",
                f"{IITB_HOST}:443:{IITB_IP}",
                "--location-trusted",
                "-u",
                f"{username}:{token}",
                LOGIN_URL,
                "-o",
                "NUL",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"{RED}[ERROR] IITB authentication request failed.{GREEN}")
            if result.stderr:
                print(f"{RED}{result.stderr.strip()}{GREEN}")
            return False

        print("[OK] IITB authentication request completed.")
        return True

    except subprocess.TimeoutExpired:
        print(f"{RED}[ERROR] IITB authentication timed out.{GREEN}")
        return False
    except Exception as exc:
        print(f"{RED}[ERROR] {exc}{GREEN}")
        return False


def run_auto_login():
    print()
    print("======================================================")
    print("        IITB AUTO INTERNET LOGIN (V.1.0 Beta)")
    print("======================================================")
    print()
    print(f"{WHITE}CREATED BY ABHISHEK KILANIYA{GREEN}")
    print(f"{WHITE}DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY{GREEN}")
    print(f"{WHITE}For IIT Bombay Community{GREEN}")
    print()

    print("[1] Waiting for Wi-Fi connection...")

    while not wifi_connected():
        time.sleep(5)

    print("[OK] Wi-Fi connected.")
    print()

    print("[2] Checking Internet...")

    if internet_available():
        print("[OK] Internet is already available.")
        print("No IITB authentication required.")
        return True

    print("[INFO] Internet is unavailable.")
    print()

    try:
        username, token = load_credentials()
    except Exception as exc:
        print(f"{RED}[ERROR] {exc}{GREEN}")
        return False

    print("[3] Authenticating with IITB...")

    if not login_to_iitb(username, token):
        return False

    print()
    print("[4] Waiting for authentication...")
    time.sleep(5)

    print("[5] Checking Internet again...")

    if internet_available():
        print()
        print("======================================================")
        print("                INTERNET IS READY")
        print("======================================================")
    else:
        print()
        print(f"{RED}[WARNING] Authentication request completed,")
        print(f"{RED}but the external Internet check did not succeed.{GREEN}")
        print("Please verify Internet access manually.")
        return False

    return True


def main():
    start_color()

    try:
        if (
            len(sys.argv) == 1
            and getattr(sys, "frozen", False)
            and Path(sys.executable).name.lower() == UNINSTALLER_NAME.lower()
        ):
            run_uninstaller()

        elif len(sys.argv) == 1:
            if CONFIG_PATH.exists() and APP_EXE.exists():
                run_auto_login()
            else:
                setup_first_run()
                pause_before_exit()

        elif sys.argv[1].lower() == "--setup":
            setup_first_run()
            pause_before_exit()

        elif sys.argv[1].lower() == "--run":
            run_auto_login()

        else:
            print(f"{RED}Unknown argument: {sys.argv[1]}{GREEN}")
            pause_before_exit()

    finally:
        stop_color()


if __name__ == "__main__":
    main()
