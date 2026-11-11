# BarFlow v2.0 — Sistema de Gerenciamento de Bares

[![BarFlow CI v2](https://github.com/EduardoPSNeri/BarFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/EduardoPSNeri/BarFlow/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![SQLite](https://img.shields.io/badge/Banco-SQLite-003B57)
![Versão](https://img.shields.io/badge/versão-2.0.0-informational)

O **BarFlow** é uma aplicação web local para auxiliar a operação de pequenos bares e estabelecimentos similares. Organiza **mesas, comandas, pedidos, pagamentos, estoque, caixa, usuários e relatórios**, substituindo parte dos registros manuais por um fluxo digital integrado.

O projeto surgiu de uma experiência prática do curso de **Análise e Desenvolvimento de Sistemas**, a partir de necessidades identificadas em um estabelecimento parceiro em Patos de Minas (MG). O objetivo é reduzir falhas de registro, facilitar a conferência das comandas e apoiar a organização operacional.

> [!IMPORTANT]
> **Versão de testes / MVP acadêmico.** O BarFlow v2.0 ainda precisa de validação completa em Windows, testes de aceitação, revisão de segurança e testes de recuperação de dados antes de uma implantação comercial. Os pagamentos são **registrados manualmente**: o sistema não processa transações bancárias, não emite notas fiscais e não se integra a maquininhas ou instituições financeiras.

## Funcionalidades

| Módulo | Recursos disponíveis |
| --- | --- |
| **Mesas** | Painel com dez mesas, identificação de disponibilidade e abertura de comandas. |
| **Comandas e pedidos** | Registro de produtos e quantidades, consulta de itens e cálculo automático dos valores. |
| **Pagamentos** | Registro de dinheiro, Pix e cartão; pagamentos parciais; cálculo de saldo e troco. |
| **Estoque** | Cadastro de produtos, quantidades e movimentações; controle configurável de estoque negativo. |
| **Caixa** | Abertura com saldo inicial e fechamento da operação. |
| **Relatórios** | Consulta de vendas e valores registrados no sistema. |
| **Usuários** | Perfis `ADMINISTRADOR` e `CAIXA`, autenticação e alteração de senha. |
| **Backup** | Script para gerar cópia consistente do banco SQLite. |

### Regras de negócio principais

- Cada mesa pode ter **uma única comanda aberta** por vez.
- Uma comanda aberta pode receber diversos pedidos; o valor total é recalculado a partir dos itens registrados.
- Os valores monetários são tratados em **centavos inteiros** nas regras de negócio.
- Os pagamentos podem ser parciais e combinar diferentes formas de recebimento.
- **Pix e cartão** não aceitam valor superior ao saldo devido. **Dinheiro** pode gerar troco.
- O encerramento exige uma comanda com itens e **saldo integralmente quitado**.
- Para produtos com controle de estoque, a baixa é realizada **uma única vez no encerramento** da comanda.
- Quando não há estoque suficiente, o encerramento é bloqueado, exceto se o administrador habilitar a configuração geral de **estoque negativo**.
- O cancelamento de uma comanda vazia exige justificativa e é restrito ao administrador **pela API**; não há interface administrativa dedicada para essa operação nesta versão.
- O registro de pagamentos exige **caixa aberto**.

## Tecnologias e arquitetura

- **Backend:** Python 3.12, FastAPI e Uvicorn.
- **Persistência:** SQLite e SQLAlchemy.
- **Validação:** Pydantic.
- **Autenticação e segurança:** Argon2id, cookies de sessão `HttpOnly`, proteção CSRF e controle de permissões no servidor.
- **Frontend:** HTML5, CSS3 e JavaScript puro (*Vanilla JS*), sem framework de interface.
- **Qualidade:** Pytest, FastAPI TestClient, Node.js para verificação de sintaxe JavaScript e GitHub Actions para integração contínua.

A aplicação é executada em um **único computador**, com servidor local acessível pelo navegador em `127.0.0.1:8000`. O frontend consome a API FastAPI; a API aplica as regras de negócio e persiste as informações no SQLite. **Não é necessária conexão com a internet para a operação local depois de instalada.**

## Requisitos

- **Windows 10/11 x64**, para o instalador automatizado; Linux/macOS podem ser usados no desenvolvimento com instalação manual.
- Navegador atualizado.
- Porta TCP local **8000** disponível.
- Internet **na primeira instalação** para obter o Python, se necessário, e as dependências.

## Instalação no Windows

1. Baixe o código-fonte pela opção **Code → Download ZIP** no [repositório](https://github.com/EduardoPSNeri/BarFlow) ou obtenha a versão desejada pelas tags.
2. Extraia todos os arquivos para uma pasta, por exemplo `C:\BarFlow`.
3. Execute **`instalar_windows.bat`**.
4. Se o **Python 3.12** não for encontrado, o instalador solicitará autorização para baixar o **Python 3.12.10 (Windows x64)** do site oficial. O instalador verifica a assinatura digital antes da instalação.
5. O assistente prepara o ambiente virtual `.venv`, instala as dependências e configura o administrador inicial **somente quando ainda não existe um administrador**.
6. Execute **`iniciar_windows.bat`**.
7. Abra **http://127.0.0.1:8000/login.html** no navegador.

> [!NOTE]
> O instalador foi projetado para reaproveitar uma instalação compatível do Python e não exige alterar o `PATH` global. As etapas de instalação automática dependem das permissões e configurações do Windows e devem ser verificadas no computador de destino.

### Primeiro acesso

Em um banco novo, o instalador cria uma conta provisória:

| Campo | Valor inicial |
| --- | --- |
| Usuário | `admin` |
| Senha provisória | `admin` |

**A alteração da senha é obrigatória no primeiro acesso.** Enquanto a senha provisória não for substituída, o sistema impede operações de negócio. Depois da alteração, é necessário entrar novamente.

A política atual de novas senhas é de **4 a 20 caracteres**. Senhas antigas de versões anteriores com mais de 20 caracteres continuam aceitas para autenticação, mas alterações devem respeitar o novo limite.

> [!WARNING]
> Uma senha de quatro caracteres é fraca. Use uma senha longa e exclusiva, mesmo em ambiente local. Não exponha o BarFlow à rede ou à internet com as credenciais provisórias.

O administrador pode gerenciar contas e perfis. Usuários autenticados podem alterar a própria senha pela opção **Minha senha**.

### Instalação manual para desenvolvimento (Windows PowerShell)

Na raiz do projeto, com Python 3.12 disponível:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\criar_admin.py
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Acesse **http://127.0.0.1:8000/login.html**.

## Roteiro de teste funcional

1. Entre como administrador e, se solicitado, altere a senha provisória.
2. No **Estoque**, cadastre um produto, seu preço e sua quantidade inicial.
3. Abra o **Caixa** com saldo inicial de R$ 0,00.
4. No painel de mesas, abra uma comanda e registre produtos em **Pedidos**.
5. Em **Pagamentos**, registre parte do valor por Pix ou cartão e o restante em dinheiro; confira o saldo e o troco.
6. Tente encerrar uma comanda ainda não quitada para conferir o bloqueio.
7. Quite o saldo, encerre a comanda e confira a liberação da mesa e a baixa do estoque controlado.
8. Consulte **Relatórios** e encerre o caixa conforme o fluxo operacional.

Considere esses passos um **roteiro de validação**, não evidência de homologação da aplicação.

## Organização do projeto

```text
BarFlow/
├── .github/
│   └── workflows/
│       └── ci.yml               # Integração contínua v2
├── backend/
│   ├── database.py              # Conexão SQLite / sessões SQLAlchemy
│   ├── models.py                # Entidades do domínio
│   ├── schemas.py               # Validação de entradas
│   ├── security.py              # Hash, sessão e CSRF
│   ├── services.py              # Regras de negócio
│   └── main.py                  # API e disponibilização do frontend
├── Frontend/
│   ├── index.html               # Painel de mesas
│   ├── pedidos.html
│   ├── pagamentos.html
│   ├── estoque.html
│   ├── caixa.html
│   ├── relatorios.html
│   ├── usuarios.html
│   ├── login.html
│   ├── alterar-senha.html
│   ├── css/global.css
│   └── js/
│       ├── app.js
│       └── store.js
├── scripts/
│   ├── instalar_windows.ps1
│   ├── criar_admin.py
│   └── backup.py
├── tests/
│   ├── test_api.py
│   ├── test_initial_admin.py
│   └── test_password_policy.py
├── instalar_windows.bat
├── iniciar_windows.bat
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

O banco local é criado em **`data/barflow.db`**. Essa pasta contém dados operacionais e está excluída do versionamento no `.gitignore`.

## Testes automatizados

Instale as dependências de desenvolvimento e execute:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests/
```

Para conferir a sintaxe dos arquivos JavaScript, com Node.js instalado:

```powershell
node --check Frontend/js/app.js
node --check Frontend/js/store.js
```

Os testes Python abrangem cenários de autenticação, regras de senhas, permissões, pedidos, pagamentos, fechamento de comandas e estoque. A suíte **não substitui** testes manuais de interface, instalação Windows, concorrência, backup/restauração e aceitação pelo estabelecimento.

### GitHub Actions

O workflow **[BarFlow CI v2](.github/workflows/ci.yml)** executa automaticamente:

- **Backend:** Python 3.12, instalação a partir de `requirements-dev.txt`, compilação de sintaxe e execução de `pytest` com banco isolado.
- **Frontend:** Node.js 22 e verificação de sintaxe dos módulos JavaScript.

A execução é acionada em *pushes* para `main`, `feat/**`, `fix/**` e `test/**`, em *Pull Requests* para `main` e manualmente pela interface do GitHub.

Consulte o [histórico de execuções](https://github.com/EduardoPSNeri/BarFlow/actions/workflows/ci.yml). **Um pipeline verde confirma esses testes automatizados, não que o sistema está homologado para produção.**

## Backup e proteção dos dados

O SQLite armazena os dados localmente. Para criar um backup consistente, utilize o script:

```powershell
.\.venv\Scripts\python.exe scripts\backup.py
```

Os arquivos são gravados em `data/backups/` com identificação de data e hora. Guarde cópias fora da pasta do projeto e **teste periodicamente a restauração** antes de confiar no procedimento.

Não publique no GitHub a pasta `data/`, bancos `.db`, arquivos de ambiente `.env`, credenciais ou o diretório `.venv/`.

## Segurança e limitações atuais

- Senhas são armazenadas por **hash Argon2id**, não em texto puro.
- As sessões utilizam cookie `HttpOnly`, `SameSite=Strict` e expiração configurada; operações de escrita exigem token CSRF.
- O servidor é iniciado em `127.0.0.1`, sem exposição planejada à rede externa.
- O limitador de tentativas de login é básico e mantido em memória.
- O SQLite foi adotado para um **único terminal local**; o projeto não foi preparado para múltiplos caixas simultâneos.
- Os registros de Pix e cartão **não realizam transferências**; apenas anotam valores recebidos externamente.
- Não há emissão de documentos fiscais, integração com adquirentes, impressão de comandas ou controle de ingredientes por ficha técnica.
- O cancelamento administrativo de comanda vazia existe na API, mas não tem tela própria nesta versão.
- Ainda são necessários testes de recuperação, segurança, concorrência, instalação, usabilidade e aceitação para qualquer implantação real.

## Histórico de evolução

| Etapa | Evolução |
| --- | --- |
| Protótipo inicial | Interface de mesas, pedidos e pagamentos em HTML, CSS e JavaScript, com dados demonstrativos no navegador. |
| v1.2 | Correção da localização do Python 3.12 no instalador Windows. |
| v1.3 | Conta inicial `admin/admin` com troca obrigatória de senha. |
| v1.4 | Política de senhas de 4 a 20 caracteres. |
| **v2.0** | Backend FastAPI, SQLite, autenticação e módulos operacionais integrados, com testes automatizados e GitHub Actions. |

> As etapas anteriores descrevem a evolução do projeto; **a versão principal documentada neste README é a v2.0**.

## Contexto acadêmico e ODS

O BarFlow foi desenvolvido no contexto de uma atividade prática de **Análise e Desenvolvimento de Sistemas**, a partir do diagnóstico de problemas no registro manual de pedidos e comandas de um pequeno estabelecimento parceiro.

A proposta está alinhada ao **Objetivo de Desenvolvimento Sustentável 8 — Trabalho Decente e Crescimento Econômico**, especialmente à **meta 8.2**, por buscar apoiar a produtividade e a modernização tecnológica de um pequeno empreendimento. Esse alinhamento descreve a intenção do projeto; resultados efetivos dependem de validação e uso posterior.

## Repositório

Código-fonte: **https://github.com/EduardoPSNeri/BarFlow**  
Versão de referência: **`v2.0.0`**
