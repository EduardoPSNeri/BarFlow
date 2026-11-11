import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

def load_launcher():
    p=Path(__file__).resolve().parents[1]/'scripts'/'iniciar_barflow.py'
    spec=importlib.util.spec_from_file_location('barflow_launcher_test',p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_app_mode_not_browser_tab():
    module=load_launcher()
    fake=Path(__file__).resolve()
    with patch.object(module,'find_app_browser',return_value=fake), patch.object(module.subprocess,'Popen') as process, patch.object(module,'log'):
        module.app_window()
    args=process.call_args.args[0]
    assert args[0]==str(fake)
    assert '--app='+module.URL in args
    assert '--new-window' in args

def test_missing_browser_explicit_error():
    module=load_launcher()
    with patch.object(module,'find_app_browser',return_value=None):
        try:module.app_window()
        except RuntimeError as exc:assert 'Edge ou Google Chrome' in str(exc)
        else:raise AssertionError('Deveria avisar que o navegador nao esta instalado')
