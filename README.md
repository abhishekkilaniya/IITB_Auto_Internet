# IITB Auto Internet

**Version V.1.1.1**

A lightweight Windows utility that automates IIT Bombay Internet authentication using your IITB LDAP ID and SSO Access Token.

> **For IIT Bombay Community**

## Features

- One standalone EXE.
- First-run credential setup.
- Visible SSO Access Token input for easy typing/pasting.
- Credentials are tested before they are saved.
- Verifies actual Internet access after IITB authentication.
- Saves the SSO token in encrypted form using Windows PowerShell SecureString functionality.
- Automatically creates a Desktop shortcut.
- Automatically creates a Windows Startup shortcut.
- Silent startup mode using `--startup`.
- Checks whether Internet is already available before authenticating.
- Update saved credentials without reinstalling.
- Test saved credentials.
- Delete saved credentials without removing the application.
- Complete uninstall from inside the application.
- Uses IITB-specific HTTPS host/IP mappings required by the current authentication flow.
- No installer and no separate uninstaller are required.

## Requirements

- Windows 10/11
- IITB network connection
- IITB LDAP ID
- IITB SSO Access Token
- `curl` available on the Windows system
- Windows PowerShell

The released EXE is intended to be used directly; Python is not required for end users.

## Download and use

The release package contains:

```text
IITB Auto Internet.exe
```

### First run

1. Run `IITB Auto Internet.exe`.
2. Choose **Set up credentials**.
3. Enter your IITB LDAP ID.
4. Enter your IITB SSO Access Token.
5. The program tests IITB authentication.
6. It then verifies real Internet access.
7. Only after both checks succeed are the credentials saved.
8. The application creates Desktop and Windows Startup shortcuts.

### Normal use

When the application is already configured, the menu provides:

```text
1. Connect to IITB Internet now
2. Update credentials
3. Test saved credentials
4. Delete saved credentials
5. Remove IITB Auto Internet
6. Exit
```

### Automatic startup

The application creates:

```text
IITB Auto Internet.lnk
```

inside the user's Windows Startup folder. The shortcut launches:

```text
IITB Auto Internet.exe --startup
```

Startup mode does not show the setup/menu. It waits for Wi-Fi, checks the IITB network path, checks whether Internet access already exists, and authenticates only when necessary.

## Authentication flow

```text
Windows starts
      |
      v
IITB Auto Internet.exe --startup
      |
      v
Wait for Wi-Fi
      |
      v
Wait for IITB network path
      |
      v
Is real Internet already available?
      |                 |
     YES               NO
      |                 |
      v                 v
    Exit         Load encrypted credentials
                        |
                        v
                Authenticate with IITB
                        |
                        v
                Verify real Internet
                        |
                        v
                       Exit
```

For first-time setup:

```text
LDAP + SSO Token
       |
       v
IITB authentication
       |
       v
Real Internet verification
       |
       v
Encrypt + save credentials
       |
       v
Create shortcuts
```

Credentials are **not saved** when authentication fails or when actual Internet access cannot be verified.

## Credential storage

The application stores its per-user files under:

```text
%LOCALAPPDATA%\IITB-Auto-Internet
```

The configuration file is:

```text
%LOCALAPPDATA%\IITB-Auto-Internet\config.json
```

The token is not stored as plain text by the application. It is converted to a Windows SecureString representation before being written to the configuration file. The application also attempts to restrict the configuration file's Windows ACL to the current user.

Do not share your `config.json`, SSO token, screenshots containing the token, or terminal output containing the token.

## Uninstall

Select:

```text
Remove IITB Auto Internet
```

and type:

```text
REMOVE
```

The application removes:

- Saved credentials
- Installed application files
- Desktop shortcut
- Windows Startup shortcut
- `%LOCALAPPDATA%\IITB-Auto-Internet`

Downloaded ZIP/release files are not deleted.

## Build from source

### 1. Install PyInstaller

```cmd
python -m pip install pyinstaller
```

### 2. Keep the source and icon together

```text
IITB Auto Internet V1.1.1.py
iitb_auto_internetLogo.ico
```

### 3. Build

```cmd
python -m PyInstaller --clean --noconfirm --onefile --console --name "IITB Auto Internet" --icon="iitb_auto_internetLogo.ico" --add-data "iitb_auto_internetLogo.ico;." "IITB Auto Internet V1.1.1.py"
```

The final executable will be:

```text
dist\IITB Auto Internet.exe
```

## Release package

The end-user release should contain only:

```text
IITB Auto Internet.exe
```

For example:

```text
IITB Auto Internet V1.1.1.zip
└── IITB Auto Internet.exe
```

## Troubleshooting

### Authentication returns HTTP 401

The IITB SSO server rejected the supplied credentials.

Use:

```text
IITB Auto Internet.exe
```

then:

```text
Update credentials
```

Do not share your SSO token in an issue or screenshot.

### Internet is not verified after authentication

The IITB authentication endpoint responded successfully, but the application could not receive the expected Internet connectivity response.

Try connecting to the IITB network again and run:

```text
Connect to IITB Internet now
```

### Startup does not connect

Check that the shortcut exists in:

```text
shell:startup
```

It should point to the permanently installed executable under:

```text
%LOCALAPPDATA%\IITB-Auto-Internet
```

### Reset the application

Use:

```text
Delete saved credentials
```

if you only want to remove the saved credentials.

Use:

```text
Remove IITB Auto Internet
```

for a complete application removal.

## Project structure

The project intentionally uses a single Python source file for V1.1.1:

```text
IITB Auto Internet V1.1.1.py
```

The same program handles:

- first-run setup
- automatic startup authentication
- manual connection
- credential management
- uninstall

Startup mode is selected using the `--startup` command-line argument.

## Credits

**CREATED BY ABHISHEK KILANIYA**  
**DEPARTMENT OF EARTH SCIENCES, IIT BOMBAY**  
**For IIT Bombay Community**

Copyright (c) 2026 Abhishek Kilaniya.

## License

MIT License. See `LICENSE`.
