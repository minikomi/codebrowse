#!/usr/bin/env python3
"""Minimal file browser with syntax highlighting.

Usage:
    python app.py [OPTIONS]

Options:
    --root PATH      Root directory to browse (default: current dir)
    --port PORT      Port to serve on (default: 8000)
    --title TITLE    Browser title (default: "File Browser")
    --ignore DIRS    Comma-separated dirs to ignore

Environment Variables:
    FB_ROOT          Root directory
    FB_PORT          Port number
    FB_TITLE         Browser title
    FB_IGNORE        Comma-separated ignore patterns
"""
import os
import argparse
from pathlib import Path
from flask import Flask, render_template_string, abort
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter

app = Flask(__name__)

# Configuration (set at startup)
CONFIG = {
    'root': Path('.').resolve(),
    'title': 'File Browser',
    'ignore_dirs': {'.venv', '__pycache__', '.git', 'node_modules', '.mypy_cache', '.pytest_cache'},
    'ignore_exts': {'.pyc', '.pyo', '.so', '.db', '.sqlite', '.wav', '.mp3', '.ogg', '.zip', '.tar', '.gz', '.jpg', '.png', '.gif'}
}


def should_ignore(path: Path) -> bool:
    if path.name.startswith('.') and path.is_dir():
        return True
    if path.is_dir() and path.name in CONFIG['ignore_dirs']:
        return True
    if path.is_file() and path.suffix in CONFIG['ignore_exts']:
        return True
    return False


def get_tree(root: Path, rel_path: str = '') -> list:
    items = []
    try:
        entries = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return items
    for entry in entries:
        if should_ignore(entry):
            continue
        item_rel = f"{rel_path}/{entry.name}" if rel_path else entry.name
        items.append({'name': entry.name, 'path': item_rel, 'is_dir': entry.is_dir()})
    return items


HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        :root {
            --bg: #1e1e1e;
            --sidebar-bg: #252526;
            --border: #3c3c3c;
            --text: #d4d4d4;
            --text-dim: #888;
            --hover: #2a2d2e;
            --selected: #094771;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: system-ui, -apple-system, sans-serif;
            background: var(--bg); 
            color: var(--text); 
            height: 100vh;
            height: 100dvh;
            overflow: hidden;
        }
        .container { display: flex; height: 100%; }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            min-width: 200px;
            max-width: 50vw;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border);
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        .sidebar-header {
            padding: 12px 15px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-dim);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            background: var(--sidebar-bg);
            z-index: 5;
        }
        #tree { flex: 1; overflow-y: auto; padding: 8px 0; }
        .item {
            padding: 6px 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            font-size: 13px;
            white-space: nowrap;
            user-select: none;
        }
        .item:hover { background: var(--hover); }
        .item.selected { background: var(--selected); }
        .item .icon { width: 18px; margin-right: 6px; text-align: center; flex-shrink: 0; }
        .dir > .icon::before { content: "📁"; }
        .dir.open > .icon::before { content: "📂"; }
        .file > .icon::before { content: "📄"; }
        .file[data-ext="py"] > .icon::before { content: "🐍"; }
        .file[data-ext="md"] > .icon::before { content: "📝"; }
        .file[data-ext="json"] > .icon::before { content: "{}"; font-size: 11px; }
        .file[data-ext="js"] > .icon::before { content: "📜"; }
        .file[data-ext="html"] > .icon::before { content: "🌐"; }
        .children { padding-left: 14px; display: none; }
        .folder.open > .children { display: block; }
        
        /* Content */
        .content { flex: 1; overflow: auto; display: flex; flex-direction: column; min-width: 0; }
        .code-header {
            padding: 10px 16px;
            background: #2d2d2d;
            border-bottom: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-dim);
            position: sticky;
            top: 0;
            z-index: 5;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .code-header .path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .code-content { flex: 1; overflow: auto; }
        .highlight { background: transparent !important; }
        .highlight pre {
            padding: 12px 16px;
            margin: 0;
            font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            overflow-x: auto;
        }
        .linenos { 
            color: #555; 
            padding-right: 16px;
            text-align: right;
            user-select: none;
            border-right: 1px solid var(--border);
            margin-right: 16px;
        }
        .empty {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #555;
        }
        
        /* Mobile */
        .mobile-toggle {
            display: none;
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--selected);
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        @media (max-width: 768px) {
            .sidebar {
                position: fixed;
                left: 0; top: 0; bottom: 0;
                width: 85vw;
                max-width: 320px;
                transform: translateX(-100%);
                transition: transform 0.2s ease;
                z-index: 50;
            }
            .sidebar.open { transform: translateX(0); }
            .content { width: 100%; }
            .mobile-toggle { display: block; }
            .overlay {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.5);
                z-index: 40;
            }
            .sidebar.open ~ .overlay { display: block; }
            .highlight pre { font-size: 11px; }
        }
        {{ css }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">📦 {{ title }}</div>
            <div id="tree">
                {% for item in tree %}
                    {% if item.is_dir %}
                    <div class="folder">
                        <div class="item dir" hx-get="/tree/{{ item.path }}" hx-target="next .children" hx-swap="innerHTML" hx-trigger="click once" onclick="toggleDir(this)">
                            <span class="icon"></span>{{ item.name }}
                        </div>
                        <div class="children"></div>
                    </div>
                    {% else %}
                    <div class="item file" data-ext="{{ item.name.rsplit('.', 1)[-1] if '.' in item.name else '' }}" hx-get="/file/{{ item.path }}" hx-target="#view" onclick="selectFile(this)">
                        <span class="icon"></span>{{ item.name }}
                    </div>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        <div class="overlay" onclick="closeSidebar()"></div>
        <div class="content" id="view">
            <div class="empty">Select a file</div>
        </div>
    </div>
    <button class="mobile-toggle" onclick="toggleSidebar()">☰</button>
    <script>
        function selectFile(el) {
            event.stopPropagation();
            document.querySelectorAll('.item').forEach(e => e.classList.remove('selected'));
            el.classList.add('selected');
            closeSidebar();
        }
        function toggleDir(el) {
            event.stopPropagation();
            el.parentElement.classList.toggle('open');
            el.classList.toggle('open');
        }
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
        }
        function closeSidebar() {
            document.getElementById('sidebar').classList.remove('open');
        }
    </script>
</body>
</html>
'''

TREE_HTML = '''
{% for item in tree %}
    {% if item.is_dir %}
    <div class="folder">
        <div class="item dir" hx-get="/tree/{{ item.path }}" hx-target="next .children" hx-swap="innerHTML" hx-trigger="click once" onclick="toggleDir(this)">
            <span class="icon"></span>{{ item.name }}
        </div>
        <div class="children"></div>
    </div>
    {% else %}
    <div class="item file" data-ext="{{ item.name.rsplit('.', 1)[-1] if '.' in item.name else '' }}" hx-get="/file/{{ item.path }}" hx-target="#view" onclick="selectFile(this)">
        <span class="icon"></span>{{ item.name }}
    </div>
    {% endif %}
{% endfor %}
'''

FILE_HTML = '''
<div class="code-header"><span class="path">{{ path }}</span></div>
<div class="code-content">{{ code|safe }}</div>
'''


@app.route('/')
def index():
    tree = get_tree(CONFIG['root'])
    fmt = HtmlFormatter(style='monokai')
    return render_template_string(HTML, tree=tree, title=CONFIG['title'], css=fmt.get_style_defs('.highlight'))


@app.route('/tree/<path:subpath>')
def tree_view(subpath):
    full = CONFIG['root'] / subpath
    if not full.exists() or not full.is_dir():
        abort(404)
    if not str(full.resolve()).startswith(str(CONFIG['root'])):
        abort(403)
    return render_template_string(TREE_HTML, tree=get_tree(full, subpath))


@app.route('/file/<path:subpath>')
def file_view(subpath):
    full = CONFIG['root'] / subpath
    if not full.exists() or not full.is_file():
        abort(404)
    if not str(full.resolve()).startswith(str(CONFIG['root'])):
        abort(403)
    try:
        content = full.read_text(errors='replace')
    except Exception as e:
        return render_template_string(FILE_HTML, path=subpath, code=f'<pre>Error: {e}</pre>')
    try:
        lexer = get_lexer_for_filename(full.name)
    except:
        lexer = TextLexer()
    fmt = HtmlFormatter(style='monokai', linenos=True, cssclass='highlight')
    return render_template_string(FILE_HTML, path=subpath, code=highlight(content, lexer, fmt))


def main():
    parser = argparse.ArgumentParser(description='File Browser')
    parser.add_argument('--root', '-r', default=os.environ.get('FB_ROOT', '.'))
    parser.add_argument('--port', '-p', type=int, default=int(os.environ.get('FB_PORT', '8000')))
    parser.add_argument('--title', '-t', default=os.environ.get('FB_TITLE', 'File Browser'))
    parser.add_argument('--ignore', '-i', default=os.environ.get('FB_IGNORE', ''))
    args = parser.parse_args()
    
    CONFIG['root'] = Path(args.root).resolve()
    CONFIG['title'] = args.title
    if args.ignore:
        CONFIG['ignore_dirs'].update(args.ignore.split(','))
    
    print(f"Serving {CONFIG['root']} at http://0.0.0.0:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False)


if __name__ == '__main__':
    main()
