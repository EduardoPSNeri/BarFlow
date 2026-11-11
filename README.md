# BarFlow — MVP local (FastAPI + SQLite)

Sistema web local para a operação de **mesas, comandas, pedidos, pagamentos, estoque, caixa e relatórios** de um pequeno bar. Foi desenvolvido como continuação do protótipo acadêmico BarFlow. A instalação é **offline** após baixar as dependências, usando um único computador Windows.

> **Importante:** esta é uma versão de testes. Não processa pagamentos reais por Pix ou cartão, não emite documentos fiscais e **não deve ser utilizada em produção sem testes de aceitação, backups e revisão de segurança**. Os valores digitados são registros manuais de pagamentos já recebidos por outros meios.

## Requisitos

- Windows 10/11 (ou Linux/macOS para desenvolvimento)
- Navegador atualizado; **o instalador Windows detecta e pode baixar automaticamente o Python 3.12** (com sua autorizacao)
- Porta local 8000 disponível

## Instalar no Windows (automatico)

1. Extraia todo o ZIP para uma pasta local (por exemplo, `C:\BarFlow`).
2. Clique duas vezes em **`instalar_windows.bat`**.
3. Caso Python 3.12 nao esteja presente, o assistente pedira autorizacao e baixara **Python 3.12.10 (x64)** diretamente de `python.org`. O download e verificado pela assinatura digital da **Python Software Foundation**, antes de instalar para o usuario atual. Nao e necessario instalar Python manualmente.
4. O instalador criara `.venv`, instalara as bibliotecas de `requirements.txt` e criara o administrador inicial com usuario e senha provisoria admin/admin, quando ainda nao houver administrador.
5. Para iniciar, execute **`iniciar_windows.bat`**, depois abra `http://127.0.0.1:8000/login.html`.

**Internet e necessaria na primeira instalacao** para baixar Python (se ausente) e dependencias. Depois, o BarFlow opera localmente sem internet. A instalacao automatica destina-se a **Windows 10/11 x64**; outras arquiteturas devem usar o Python 3.12 oficial correspondente. O script **nao** altera o PATH global e nao instala o Python sem a confirmacao do usuario. Se uma instalacao do Python falhar, reinicie o terminal antes de tentar novamente.

Para instalar manualmente em ambiente de desenvolvimento:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\criar_admin.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## Primeiro uso

1. Entre como administrador.
2. Em **Estoque**, cadastre alguns produtos, preços em reais e quantidades.
3. Abra o módulo **Caixa** e informe o saldo inicial (pode ser zero).
4. Em **Painel de mesas**, abra uma comanda para qualquer uma das dez mesas.
5. Em **Pedidos**, adicione um ou mais produtos e confira o total.
6. Em **Pagamentos**, registre o recebimento manual (Pix, cartão ou dinheiro), inclusive pagamentos parciais.
7. Quite o saldo e encerre a comanda. O estoque controlado é baixado **uma única vez, no encerramento**.
8. Consulte **Relatórios** e **Estoque** para conferir o histórico. O administrador pode fechar o caixa.

## Regras principais

- Uma única comanda aberta por mesa; novas comandas recebem novo ID.
- Pedidos preservam preço e nome do produto no momento do registro.
- Total, pagamentos aplicados e troco calculados em centavos inteiros.
- Pix e cartão não permitem recebimento acima do saldo; dinheiro pode gerar troco.
- Nenhuma comanda com saldo pendente ou sem itens pode ser encerrada.
- Sem estoque suficiente, a baixa bloqueia o encerramento; o administrador pode optar pela configuração geral de estoque negativo.
- Cancelamento de comanda **vazia** é restrito ao administrador via API; exige justificativa.
- Perfis: `ADMINISTRADOR` (acesso à gestão) e `CAIXA` (mesas, pedidos, pagamentos, abertura de caixa e leitura de estoque).
- Pagamentos exigem caixa aberto.

## Estrutura

```text
backend/
  database.py    # engine SQLite, sessões SQLAlchemy
  models.py      # entidades e relacionamentos
  schemas.py     # validações de entrada Pydantic
  security.py    # Argon2id, cookie HttpOnly e CSRF
  services.py    # regras de comandas e pagamentos
  main.py        # rotas FastAPI + arquivos estáticos
Frontend/
  index.html, pedidos.html, pagamentos.html
  estoque.html, caixa.html, relatorios.html, usuarios.html, login.html
  css/global.css, js/app.js
scripts/
  criar_admin.py, backup.py
```

O banco é criado em `data/barflow.db` na inicialização. A pasta `data/` fica fora do Git pelo `.gitignore`.

### Backup

Feche o servidor ou faça o backup consistente com:

```powershell
python scripts/backup.py
```

Um arquivo `.db` com data e horário será criado em `data/backups/`. Teste periodicamente a restauração em outro diretório.

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Segurança e limitações

- Senhas protegidas com Argon2id. Cookies de sessão HttpOnly, SameSite Strict e expiração de 8 horas; operações de escrita exigem token CSRF.
- Inicialização em `127.0.0.1` para acesso exclusivamente local. **Não exponha essa aplicação à internet.** A configuração `Secure` dos cookies foi mantida desativada para `http://127.0.0.1`; publicação em HTTPS requer ajuste.
- Limitador de login básico em memória (não distribuído).
- SQLite: adequado a um caixa local, não a múltiplos terminais simultâneos sem revisão.
- Ainda não há relatórios fiscais, impressão de comandas, integração bancária ou interface de cancelamento administrativo.
- O modelo de estoque é simples (quantidade por produto); não calcula ingredientes/fichas técnicas de receitas.
- Revisões de CSRF, cookies, regras de estoque, concorrência, recuperação de falhas e testes de usabilidade são necessárias antes de uso real.

## ODS

Alinhamento acadêmico ao **ODS 8 — Trabalho Decente e Crescimento Econômico**, meta 8.2, ao buscar organização e produtividade no contexto local do estabelecimento.


## Correcao do instalador v1.2 (Windows)

Esta revisao corrige a deteccao de Python 3.12 no Windows PowerShell 5.1, inclusive quando instalado somente para o usuario atual. O instalador procura o executavel no diretorio padrao, no Registro do Windows (PEP 514) e via launcher `py`.

Se a instalacao v1.1 ja baixou o Python, execute **instalar_windows.bat** novamente usando esta versao. O instalador deve reaproveitar a instalacao existente, sem novo download. Caso o Windows tenha bloqueado a instalacao ou o executavel nao exista, o script voltara a solicitar o download. Nao apague o banco de dados nem as pastas de projeto para corrigir esse erro.

Para diagnosticar manualmente no PowerShell: `py -3.12 --version` ou `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" --version`.

## Acesso inicial (v1.3)

Na **primeira instalação em banco vazio**, o instalador cria automaticamente o usuário provisório `admin` com senha `admin`. Essa senha é **temporária e insegura**: no primeiro login o BarFlow exige a definição de uma senha exclusiva de 4 a 20 caracteres e impede qualquer operação até a troca. Após alterar a senha, todas as sessões são invalidadas e será necessário entrar novamente.

Em instalações existentes, o instalador **preserva o administrador e sua senha**; não redefine credenciais nem remove dados. Nunca exponha o serviço à rede ou à internet com a senha provisória.

O administrador não precisa mais informar nome e senha durante a instalação.

Após a configuração inicial, qualquer usuário autenticado poderá alterar sua senha pela opção **Minha senha** do menu, informando a senha atual.

## Política de senhas (v1.4)

- Novas senhas e senhas alteradas: **4 a 20 caracteres**. O requisito é verificado no backend (Pydantic) e nos formulários.
- Credenciais previamente criadas com mais de 20 caracteres **continuam válidas para login e autenticação da senha atual**; a nova senha escolhida deve seguir o limite de 4 a 20.
- A senha provisória `admin` continua exigindo troca obrigatória no primeiro acesso e não pode ser escolhida novamente.
- **Aviso:** senhas de 4 caracteres são fracas. Esta configuração é adequada apenas para testes locais controlados; recomenda-se senha longa e exclusiva em qualquer implantação real.
