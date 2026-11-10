# BarFlow

**BarFlow** é um projeto acadêmico de gerenciamento de bares e pequenos restaurantes. Seu objetivo é reduzir pedidos esquecidos ou não registrados por meio do controle de **mesas, comandas, pedidos e pagamentos**, com foco no operador de caixa.

## Estado atual

**Frontend semifuncional demonstrativo (v0.3), ainda sem backend.** As telas utilizam somente dados fictícios. As operações são mantidas no armazenamento local do navegador (`localStorage`), e não em um banco de dados. **Não utilize para cobrança real, produção ou armazenamento de dados pessoais.**

### Funcionalidades demonstráveis

- **RF-001:** visualizar dez mesas e os estados livre/ocupada.
- **RF-002:** abrir ou consultar uma comanda por mesa, sem duplicar comandas abertas.
- **RF-003:** adicionar produtos fictícios e quantidades a qualquer comanda aberta.
- **RF-004:** acompanhar itens e total acumulado, calculados a partir dos itens registrados.
- **RF-005:** registrar pagamentos parciais por Pix, cartão ou dinheiro; calcular saldo e troco somente para dinheiro.
- **RF-006:** impedir encerramento com saldo pendente e liberar a mesa após quitação.

As comandas fechadas permanecem armazenadas no estado demonstrativo, embora ainda não exista uma tela de relatórios ou histórico.

## Como executar

1. Clone ou baixe o repositório.
2. Abra `Frontend/index.html` no navegador (Chrome, Edge ou Firefox atualizado).
3. Clique em **Abrir comanda** em qualquer mesa livre.
4. Na tela de pedidos, selecione produtos, informe quantidades e registre os itens.
5. Vá para **Pagamentos**, efetue pagamentos fictícios até quitar o saldo e encerre a comanda.
6. Volte ao painel e confira que a mesa foi liberada.

Opcionalmente, execute com servidor local para reproduzir uma implantação web estática:

```powershell
cd Frontend
python -m http.server 8000
```

Depois, abra `http://localhost:8000/`.

**Reiniciar demonstração:** botão disponível no menu lateral. Ele apaga os dados fictícios locais após confirmação. O conteúdo pode persistir após fechar o navegador, pois usa `localStorage`.

## Estrutura

```text
Frontend/
├── index.html             # Painel de mesas
├── pedidos.html           # Formulário e consumo da comanda
├── pagamentos.html        # Pagamentos parciais, troco e encerramento
├── css/
│   └── global.css         # Design system e estilos compartilhados
└── js/
    ├── store.js           # Operações de estado e regras demonstrativas
    └── app.js             # Interação e renderização das páginas
```

## Regras de negócio no protótipo

- Uma mesa não pode ter mais de uma comanda aberta.
- Um pedido exige produto cadastrado e quantidade inteira positiva (1 a 999).
- O total da comanda é a soma de preço unitário × quantidade de cada item.
- Pagamento parcial recalcula o saldo; Pix e cartão não podem exceder o saldo.
- Dinheiro pode exceder o valor devido; a diferença é exibida como troco, sem aumentar o valor aplicado à dívida.
- Só é possível encerrar comanda com itens registrados e saldo igual a zero.
- O encerramento libera a mesa; uma nova abertura cria outra comanda.

## Arquitetura prevista (próxima etapa)

O projeto deverá evoluir para **Python 3.12 + FastAPI + SQLAlchemy + SQLite**, em execução local no Windows. Nesse momento, as funções de `Frontend/js/store.js` serão substituídas por chamadas HTTP à API, enquanto `app.js` continuará responsável pela apresentação. Validações e autorização também precisarão ocorrer **no backend**, independentemente das validações do navegador.

## Limitações e segurança

- Não há autenticação, controle de permissões, persistência transacional, testes de backend ou integrações com Pix e cartões.
- Os dados do navegador podem ser alterados ou apagados pelo usuário; `localStorage` não oferece integridade ou segurança adequadas para dados financeiros reais.
- O catálogo de produtos e as dez mesas são dados fictícios codificados para demonstração.
- Não há estoque integrado, operação multiusuário ou relatórios financeiros nesta versão.

## ODS

Alinhamento acadêmico com o **ODS 8 — Trabalho Decente e Crescimento Econômico**, especialmente a meta 8.2, por meio da modernização de operações simples de um pequeno estabelecimento.
