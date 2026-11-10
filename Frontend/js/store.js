/* BarFlow: camada de armazenamento DEMONSTRATIVA.
 * Futuramente os métodos desta camada serão substituídos por requisições à API FastAPI.
 * Nenhum dado é enviado a servidores. Não usar para operações reais.
 */
(function () {
  'use strict';
  const KEY = 'barflow-demo-v2';
  const PRODUCTS = Object.freeze([
    { id: 'refri', name: 'Refrigerante lata', priceCents: 800 },
    { id: 'batata', name: 'Porção de batata', priceCents: 3500 },
    { id: 'agua', name: 'Água mineral', priceCents: 600 },
    { id: 'suco', name: 'Suco natural', priceCents: 1200 },
    { id: 'porcao', name: 'Porção de mandioca', priceCents: 3200 },
    { id: 'cerveja', name: 'Cerveja long neck', priceCents: 1100 }
  ]);
  const seed = () => ({ version: 2, nextId: 101, tables: Array.from({length:10}, (_,i)=>i+1), accounts: [] });
  function read() {
    try {
      const data = JSON.parse(localStorage.getItem(KEY));
      if (data && data.version === 2 && Array.isArray(data.accounts) && Array.isArray(data.tables) && Number.isSafeInteger(data.nextId)) return data;
    } catch (_) { /* dados inválidos -> sessão demonstrativa reiniciada */ }
    const value = seed(); localStorage.setItem(KEY, JSON.stringify(value)); return value;
  }
  function write(value) { localStorage.setItem(KEY, JSON.stringify(value)); return value; }
  const active = (state, tableNo) => state.accounts.find(a=>a.tableNo===tableNo && a.status==='OPEN');
  const total = a => a.items.reduce((s,i)=>s+i.qty*i.priceCents,0);
  const paid = a => a.payments.reduce((s,p)=>s+p.appliedCents,0);
  const due = a => Math.max(0,total(a)-paid(a));
  const assertTable = (state,tableNo) => {
    if (!state.tables.includes(tableNo)) throw new Error('Mesa não cadastrada.');
  };
  function open(tableNo) {
    const s=read(); assertTable(s,tableNo);
    let a=active(s,tableNo);
    if (!a) {
      a={id:s.nextId++,tableNo,status:'OPEN',createdAt:new Date().toISOString(),items:[],payments:[]};
      s.accounts.push(a);write(s);
    }
    return a;
  }
  function account(tableNo) {
    const s=read(); assertTable(s,tableNo); return active(s,tableNo)||null;
  }
  function addItem(tableNo,productId,qty) {
    const s=read(),a=active(s,tableNo),p=PRODUCTS.find(x=>x.id===productId);
    if (!a) throw new Error('Abra uma comanda para registrar pedidos.');
    if (!p) throw new Error('Selecione um produto válido.');
    if (!Number.isSafeInteger(qty)||qty<=0||qty>999) throw new Error('A quantidade deve ser um número inteiro entre 1 e 999.');
    const item={id:'I'+Date.now()+Math.random().toString(36).slice(2,7),productId:p.id,name:p.name,priceCents:p.priceCents,qty};
    a.items.push(item); write(s);return item;
  }
  function pay(tableNo,method,receivedCents) {
    const s=read(),a=active(s,tableNo);
    if(!a) throw new Error('Nenhuma comanda aberta para esta mesa.');
    if(!['pix','dinheiro','cartao'].includes(method)) throw new Error('Forma de pagamento inválida.');
    if(!Number.isSafeInteger(receivedCents)||receivedCents<=0) throw new Error('Informe um valor positivo válido.');
    const outstanding=due(a);
    if(outstanding===0) throw new Error('A comanda não possui saldo pendente.');
    if(method!=='dinheiro' && receivedCents>outstanding) throw new Error('Pix e cartão não podem ultrapassar o saldo restante.');
    const appliedCents=Math.min(receivedCents,outstanding);
    const changeCents=method==='dinheiro'?receivedCents-appliedCents:0;
    const payment={id:'P'+Date.now()+Math.random().toString(36).slice(2,7),method,receivedCents,appliedCents,changeCents,createdAt:new Date().toISOString()};
    a.payments.push(payment);write(s);return payment;
  }
  function close(tableNo) {
    const s=read(),a=active(s,tableNo);
    if(!a) throw new Error('Não existe comanda aberta nesta mesa.');
    if(!a.items.length) throw new Error('A comanda está vazia.');
    if(due(a)>0) throw new Error('Não é possível encerrar: existe saldo pendente.');
    a.status='CLOSED';a.closedAt=new Date().toISOString();write(s);return a;
  }
  function reset() {const value=seed();write(value);sessionStorage.removeItem('barflow-current-table');return value;}
  window.BarFlowStore={products:PRODUCTS,read,account,open,addItem,pay,close,reset,total,paid,due};
})();
