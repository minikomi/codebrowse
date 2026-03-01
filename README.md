# File Browser

Minimal file browser with syntax highlighting. Mobile-friendly.

## Quick Start

```bash
pip install flask pygments
python app.py --root /path/to/code --port 8000 --title "My Code"
```

## Options

| Flag | Env Var | Default | Description |
|------|---------|---------|-------------|
| `--root`, `-r` | `FB_ROOT` | `.` | Root directory to browse |
| `--port`, `-p` | `FB_PORT` | `8000` | Server port |
| `--title`, `-t` | `FB_TITLE` | `File Browser` | Page title |
| `--ignore`, `-i` | `FB_IGNORE` | | Extra dirs to ignore (comma-separated) |

## Deploy with systemd

1. Create virtualenv and install deps:
   ```bash
   python -m venv .venv
   .venv/bin/pip install flask pygments
   ```

2. Edit `filebrowser.service` with your settings

3. Install and start:
   ```bash
   sudo cp filebrowser.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now filebrowser
   ```

## Features

- Tree-based file navigation (HTMX)
- Syntax highlighting (Pygments)
- Mobile-friendly with slide-out sidebar
- Configurable via CLI args or env vars
- Dark theme
