# codebrowse

Minimal file browser with syntax highlighting. Mobile-friendly.

## Quick Start

```bash
uvx codebrowse --root /path/to/code
```

Or install:

```bash
uv pip install codebrowse
codebrowse --root /path/to/code
```

## Options

| Flag | Env Var | Default | Description |
|------|---------|---------|-------------|
| `--root`, `-r` | `FB_ROOT` | `.` | Root directory to browse |
| `--port`, `-p` | `FB_PORT` | `8000` | Server port |
| `--title`, `-t` | `FB_TITLE` | `File Browser` | Page title |
| `--ignore`, `-i` | `FB_IGNORE` | | Extra dirs to ignore (comma-separated) |

## Deploy with systemd

```bash
# Clone and setup
git clone https://github.com/minikomi/codebrowse.git
cd codebrowse

# Edit service file with your settings
vim codebrowse.service

# Install
sudo cp codebrowse.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now codebrowse
```

## Features

- Tree-based file navigation (HTMX)
- Syntax highlighting (Pygments)
- Mobile-friendly with slide-out sidebar
- Configurable via CLI args or env vars
- Dark theme
