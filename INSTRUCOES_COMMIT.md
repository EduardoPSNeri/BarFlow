# BarFlow v2.1 — pacote consolidado para commit

Esta pasta contem arquivos **ja atualizados** da v2.1; nao execute o aplicador antigo de v2.1 novamente.

## Aplicacao

1. Feche o BarFlow e copie `data/` para uma pasta segura (com servidor parado).
2. Copie o **conteudo desta pasta** sobre a raiz de seu repositorio BarFlow, substituindo arquivos de codigo (nunca a pasta `.git/`, `.venv/` ou `data/`).
3. Abra PowerShell na raiz do BarFlow e execute:
   ` .\.venv\Scripts\python.exe -m pip install -r requirements.txt `
4. Execute ` .\.venv\Scripts\python.exe -m pytest -q ` (se necessario instale `requirements-dev.txt`).
5. Execute `iniciar_bar_flow.bat`. Ele inicia o servidor oculto e abre **uma janela de aplicativo** do Edge ou Chrome, sem aba, barra de endereco ou terminal permanente.
6. Se falhar, execute `iniciar_diagnostico.bat` e veja `data/inicializacao.log`.

## Observacoes

- A janela usa Edge/Chrome em modo aplicativo `--app`. **Nao e um EXE nativo standalone**. O motor do navegador ainda e necessario, mas nao abre uma aba comum.
- O backend ainda usa SQLite local em `data/`; a tabela `cash_expenses` sera criada automaticamente.
- A dependencia `tzdata` no requirements evita o erro ZoneInfoNotFoundError no Windows.
- A versao antiga ja utilizava GitHub Actions; para publicar esta versao crie uma branch e PR.
- Em instalacoes existentes, as mesas antigas continuam cadastradas; podem ser ocultadas na tela.
- Nao envie `data/`, logs, `.venv/` ou pastas de backup para o GitHub.
