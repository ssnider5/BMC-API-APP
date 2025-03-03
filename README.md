# BMC API Application

## Overview

BMC API Application is a Python-based GUI tool for managing saved configurations on remote servers. Built with Tkinter, the application allows users to log in, select a server, and perform a variety of actions such as downloading, uploading, restoring, creating, and updating configurations. The interface features an intuitive banner with action buttons and a server drop‑down, and it automatically refreshes the configuration table when switching servers.

## Features

- **User Authentication:**  
  A login screen that verifies user credentials via the DR - Chandler server, but given that they're all under one ESS, it shouldn't matter.

- **Action Panel:**  
  Perform key operations:
  - **Download:** Retrieve a configuration as a ZIP file.
  - **Upload:** Upload a configuration file.
  - **Restore:** Restore a configuration on a server.
  - **Create:** Create a new configuration entry.
  - **Update:** Update configurations between servers.

- **Server Management:**  
  - Easily select from a list of servers using a drop‑down menu.
  - The current server is prominently displayed.
  - The configuration table refreshes automatically when a new server is selected.

- **Interactive Table:**  
  View and select saved configurations with an auto-updating table.

## Prerequisites

- **Python 3.x**  
  Ensure you have Python installed on your system.
  Code was written in Python 3.11.9 but other versions should work

## Installation

1. **Download Zip File:**
  - At the top of the page there's a green "<> Code" Button, click it
  - Select the option "Download ZIP" and choose your preferred location
  - Extract the files and just run the file called "launch_app.vbs"
  - It will create a venv and download all the dependencies for the program to run, not influencing your global installs

## Usage

1. **Launch the Application:**
   ```bash
   python main.py
   ```

2. **Login:**
   - Enter your username and password
   - Select the target server from the dropdown

3. **Managing Configurations:**
   - Use the action buttons in the banner to perform operations
   - Select configurations from the table for specific actions
   - The status of operations will be displayed in the status bar
  
## Error Handling

The application includes comprehensive error handling for:
- Network connectivity issues
- Invalid credentials
- File operation failures
- Server communication errors

Error messages are displayed to users through popup dialogs or the status bar.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the FISERV License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
- Open an issue in the GitHub repository
- Send me an email or message me on teams sean.snider@fiserv.com
- Check the documentation in the `docs` folder

## Acknowledgments

- BMC API documentation and team
- Created by: Sean Snider
- Kevin Lyles for helping test the UI

## Version History

- 1.0.0
  - Initial Release
  - Basic functionality implementation
- 1.1.0
  - Added configuration update feature
  - Improved error handling
  - Enhanced user interface
