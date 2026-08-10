# PyInstaller spec for the fungus-mcp standalone executable.
# Run via: pyinstaller build/fungus_mcp.spec  (from repo root)

from pathlib import Path

block_cipher = None

# SPECPATH is set by PyInstaller to the directory containing this spec file.
root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "app" / "mcp" / "server.py")],
    # Include both repo root and git-scripts so PyInstaller can resolve all imports.
    pathex=[str(root), str(root / "git-scripts")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "extract_regex_from_commit",
        "app",
        "app.core",
        "app.core.logging_config",
        "app.mcp",
        "app.mcp.server",
        "mcp",
        "mcp.server",
        "mcp.server.fastmcp",
        "mcp.server.stdio",
        "anyio",
        "anyio._backends._asyncio",
        "anyio.abc",
        "anyio.streams.memory",
        "httpx",
        "gitpython",
        "git",
        "git.repo",
        "git.repo.base",
        "starlette",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Server-side packages not needed in the MCP client executable.
        "uvicorn",
        "fastapi",
        "sqlalchemy",
        "psycopg2",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="fungus-mcp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Console must stay True: MCP stdio transport reads/writes stdout/stdin.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
