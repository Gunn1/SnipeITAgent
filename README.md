# SnipeITAgent

SnipeITAgent is a lightweight, cross-platform agent for gathering device information and automatically syncing it to your Snipe-IT asset management system.

## Features

- Collects device information (hostname, serial number, user, model, etc.)
- Sends data to Snipe-IT via the API
- Designed for silent background operation
- Compiles to a standalone executable for easy deployment
- Works on macOS, Windows, and Linux

## Requirements

- Python 3.11+
- A valid Snipe-IT API token
- The following environment variables or `.env` file values:

```env
SNIPEIT_API_URL=https://your-snipeit-instance/api/v1
SNIPEIT_API_KEY=your_api_key_here
```

## Setup (Development)

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/SnipeITAgent.git
    cd SnipeITAgent
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the script:

    ```bash
    python main.py
    ```

## Packaging for macOS

Use [PyInstaller](https://pyinstaller.org/) to create a `.app` or `.pkg`:

```bash
pyinstaller --onefile --windowed --name SnipeITAgent --icon icon.icns main.py
```

You can then deploy the resulting `.app` or `.pkg` using Mosyle or other MDM systems.

## Packaging for Windows (Optional)

To build on Windows or cross-compile, use a Windows machine or a VM:

```bash
pyinstaller --onefile --name SnipeITAgent.exe main.py
```

## Deployment Tips

- For managed devices, deploy using your MDM (Mosyle, Intune, etc.)
- Consider running on a schedule using Task Scheduler (Windows) or `launchd`/cron (macOS/Linux)

## License

MIT License. See [LICENSE](LICENSE) for details.


