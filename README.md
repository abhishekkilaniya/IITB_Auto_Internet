# IITB Auto Internet

Automatically authenticates IIT Bombay Internet on Windows.

## Overview

IITB Auto Internet is a Windows utility created for the IIT Bombay community to simplify the IIT Bombay Internet authentication process.

After the initial setup, the application automatically:

- Detects Wi-Fi connectivity
- Checks whether Internet access is already available
- Authenticates through IIT Bombay SSO when required
- Stores the SSO token securely using Windows DPAPI
- Runs automatically through Windows Startup
- Creates a Desktop shortcut
- Provides a standalone uninstaller

## Features

- One-time setup
- Automatic IITB Internet authentication
- Windows Startup integration
- Desktop shortcut
- Secure local credential storage using Windows DPAPI
- No Python installation required for users
- Standalone uninstaller
- Open source under the MIT License

## Requirements

- Windows
- IIT Bombay network / Wi-Fi
- Valid IIT Bombay LDAP ID
- Valid IIT Bombay SSO Access Token

## Installation

1. Download `IITB_Auto_Internet_Setup.exe` from the Releases section.
2. Run the setup executable.
3. Enter your IIT Bombay LDAP ID.
4. Enter your IIT Bombay SSO Access Token.
5. The application will automatically install itself and create the required shortcuts.
6. Future runs are handled automatically through Windows Startup.

No Python installation or manual configuration is required.

## Uninstallation

Run:

`IITB-Auto-Internet-Uninstaller.exe`

Type:

`UNINSTALL`

The application will remove:

- Installed application files
- Stored credentials
- Desktop shortcut
- Windows Startup shortcut

The uninstaller itself remains in the release folder.

## Security

The IITB SSO token is not stored as plain text.

The token is encrypted using Windows DPAPI and stored locally on the user's Windows account.

The application does not require administrator privileges for normal installation.

## Open Source

This project is released under the MIT License.

You are free to use, modify, and distribute the software according to the terms of the license.

Please retain the original copyright and attribution.

## Attribution

Created by:

**Abhishek Kilaniya**  
**Department of Earth Sciences, IIT Bombay**

For the IIT Bombay Community.

## Disclaimer

This is an independent community project and is not an official IIT Bombay application.

The project is provided "as is" without warranty. Users are responsible for using the application with valid IIT Bombay credentials and in accordance with applicable IIT Bombay network policies.

## License

MIT License

Copyright (c) 2026 Abhishek Kilaniya

See the `LICENSE` file for the complete license text.