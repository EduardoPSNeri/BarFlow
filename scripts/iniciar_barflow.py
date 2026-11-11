"""Inicializador local do BarFlow: FastAPI oculto + janela de aplicativo Chromium.

No Windows, abre Edge/Chrome em modo --app (sem abas ou barra de enderecos).
Nao altera o banco e nao abre abas no navegador por padrao.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
LOG = DATA / 'inicializacao.log'
URL = 'http://127.0.0.1:8000/login.html'
PYTHONW = ROOT / '.venv' / 'Scripts' / 'pythonw.exe'


def log(message: str) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' | ' + message + '\n')


def server_responding() -> bool:
    try:
        with urlopen(URL, timeout=1.2) as response:
            return response.status == 200 and b'BarFlow' in response.read(30000)
    except (OSError, HTTPError, URLError):
        return False


def find_app_browser() -> Path | None:
    # Windows typically has Edge, but Chrome can be used if Edge is missing.
    candidates = []
    for executable in ('msedge.exe', 'chrome.exe'):
        path = shutil.which(executable)
        if path:
            candidates.append(Path(path))
    for env in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA'):
        root = os.environ.get(env)
        if not root:
            continue
        folder = Path(root)
        candidates.extend([
            folder / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe',
            folder / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
        ])
    # Consult App Paths if browser installed to an unusual directory.
    if sys.platform == 'win32':
        try:
            import winreg
            for exe in ('msedge.exe', 'chrome.exe'):
                for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        with winreg.OpenKey(hive, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\' + exe) as key:
                            candidates.append(Path(winreg.QueryValueEx(key, None)[0]))
                    except OSError:
                        pass
        except ImportError:
            pass
    return next((p for p in candidates if p.is_file()), None)


def app_window() -> None:
    browser = find_app_browser()
    if browser is None:
        raise RuntimeError('Microsoft Edge ou Google Chrome nao encontrado. Instale um dos dois para abrir o BarFlow em janela de aplicativo.')
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0
    subprocess.Popen([str(browser), '--app=' + URL, '--window-size=1280,820', '--new-window'],
                     cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, creationflags=flags)
    log('Janela do aplicativo aberta em: ' + str(browser))


def main() -> None:
    if server_responding():
        log('Servidor BarFlow ja estava ativo.')
        app_window()
        return
    if not PYTHONW.is_file():
        raise RuntimeError('Ambiente Python nao encontrado. Execute instalar_windows.bat.')
    DATA.mkdir(parents=True, exist_ok=True)
    log('Iniciando servidor FastAPI em segundo plano.')
    stream = LOG.open('a', encoding='utf-8', buffering=1)
    try:
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0
        process = subprocess.Popen([str(PYTHONW), '-m', 'uvicorn', 'backend.main:app',
                                    '--host', '127.0.0.1', '--port', '8000'],
                                    cwd=str(ROOT), stdin=subprocess.DEVNULL,
                                    stdout=stream, stderr=subprocess.STDOUT,
                                    creationflags=flags)
    finally:
        stream.close()
    for _ in range(60):
        if server_responding():
            log('Servidor ativo; PID=' + str(process.pid))
            app_window()
            return
        if process.poll() is not None:
            raise RuntimeError('Servidor parou com codigo ' + str(process.returncode) + '. Confira ' + str(LOG))
        time.sleep(0.5)
    raise RuntimeError('Servidor nao respondeu em 30 segundos. Confira ' + str(LOG))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        log('ERRO: ' + type(exc).__name__ + ': ' + str(exc))
        print('Falha ao iniciar BarFlow: ' + str(exc), file=sys.stderr)
        sys.exit(1)
