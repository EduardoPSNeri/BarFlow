/* Camada de interface BarFlow: os cálculos e regras ficam em store.js. */
(function () {
  'use strict';
  const S=window.BarFlowStore;
  const $=id=>document.getElementById(id);
  const money=cents=>(cents/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const tableParam=new URLSearchParams(location.search).get('mesa');
  const chosenTable=Number(tableParam||sessionStorage.getItem('barflow-current-table'));
  const validTable=()=>S.read().tables.includes(chosenTable);
  const selectTable=n=>sessionStorage.setItem('barflow-current-table',String(n));
  const url=(page,tableNo)=>page+'.html'+(Number.isInteger(tableNo)?'?mesa='+tableNo:'');
  const nav=(page,tableNo)=>location.assign(url(page,tableNo));
  const tableNo=()=>validTable()?chosenTable:null;
  function notify(text,type='info') {
    const el=$('feedback');if(!el)return;
    el.className='notice '+type;el.textContent=text;el.hidden=false;
  }
  function setupNavigation() {
    for (const [id,page] of [['nav-mesas','index'],['nav-pedidos','pedidos'],['nav-pagamentos','pagamentos']]) {
      const el=$(id);if(el)el.href=url(page,page==='index'?null:tableNo());
    }
    const reset=$('reset-demo');
    reset?.addEventListener('click',()=>{
      if(!confirm('Reiniciar dados fictícios? Todas as comandas demonstrativas serão apagadas deste navegador.'))return;
      S.reset();location.assign('index.html');
    });
    $('logout-demo')?.addEventListener('click',()=>notify('ⓘ Esta versão é demonstrativa e ainda não possui autenticação.'));
  }
  function renderTables() {
    if(!$('tables'))return;
    const state=S.read(),openAccounts=state.accounts.filter(x=>x.status==='OPEN');
    $('all-count').textContent=state.tables.length;
    $('busy-count').textContent=openAccounts.length;
    $('free-count').textContent=state.tables.length-openAccounts.length;
    $('tables').replaceChildren();
    for(const no of state.tables){
      const a=openAccounts.find(x=>x.tableNo===no),card=document.createElement('article');
      card.className='tablecard'+(a?' occupied':'');
      card.innerHTML='<div class="tableupper"><b>Mesa '+String(no).padStart(2,'0')+'</b><span class="status '+(a?'busy':'free')+'">'+(a?'◷ Ocupada':'✓ Livre')+'</span></div>';
      const p=document.createElement('p');p.textContent=a?'Comanda #'+a.id+' · '+money(S.due(a))+' pendente':'Disponível para atendimento';card.append(p);
      const btn=document.createElement('button');btn.type='button';btn.textContent=a?'Visualizar comanda':'＋ Abrir comanda';
      btn.addEventListener('click',()=>{
        try{S.open(no);selectTable(no);nav('pedidos',no);}catch(e){notify('⚠ '+e.message,'warn');}
      });
      card.append(btn);$('tables').append(card);
    }
  }
  function renderContext() {
    const no=tableNo();
    if(no===null){
      $('flow-panel').hidden=true;$('empty-state').hidden=false;
      $('empty-state').textContent='ⓘ Selecione uma mesa no Painel de mesas antes de continuar.';
      return null;
    }
    const a=S.account(no);
    if(!a){$('flow-panel').hidden=true;$('empty-state').hidden=false;$('empty-state').textContent='ⓘ A Mesa '+String(no).padStart(2,'0')+' não possui comanda aberta. Abra a comanda no painel.';return null;}
    $('flow-panel').hidden=false;$('empty-state').hidden=true;
    for(const el of document.querySelectorAll('[data-mesa]'))el.textContent=String(no).padStart(2,'0');
    for(const el of document.querySelectorAll('[data-comanda]'))el.textContent='#'+a.id;
    $('back-to-orders')?.setAttribute('href',url('pedidos',no));
    $('to-payments')?.setAttribute('href',url('pagamentos',no));
    return a;
  }
  function renderCart(account) {
    const list=$('order-items');list.replaceChildren();
    if(account.items.length===0){list.textContent='Nenhum item registrado. Adicione o primeiro produto.';}
    for(const item of account.items){
      const row=document.createElement('div');row.className='cartline';
      const info=document.createElement('div'),name=document.createElement('strong'),qty=document.createElement('small'),price=document.createElement('span');
      name.textContent=item.name;qty.textContent=item.qty+' × '+money(item.priceCents);price.className='price';price.textContent=money(item.qty*item.priceCents);
      info.append(name,qty);row.append(info,price);list.append(row);
    }
    $('order-total').textContent=money(S.total(account));
  }
  function renderOrders() {
    const a=renderContext();if(!a)return;
    const product=$('product');
    for(const p of S.products){const opt=document.createElement('option');opt.value=p.id;opt.textContent=p.name+' — '+money(p.priceCents);product.append(opt);}
    const renderPrice=()=>{$('unit-price').value=money(S.products.find(p=>p.id===product.value)?.priceCents||0);};
    product.addEventListener('change',renderPrice);renderPrice();renderCart(a);
    $('order-form').addEventListener('submit',event=>{
      event.preventDefault();
      const qty=Number($('quantity').value);
      try{
        const item=S.addItem(tableNo(),product.value,qty);
        renderCart(S.account(tableNo()));notify('✓ '+item.qty+' × '+item.name+' registrado(s) na comanda.','good');
      }catch(e){notify('⚠ '+e.message,'warn');}
    });
  }
  function renderPayments() {
    const a=renderContext();if(!a)return;
    const items=$('pay-items');items.replaceChildren();
    for(const item of a.items){const row=document.createElement('div');row.className='summaryrow';
      const s=document.createElement('span'),b=document.createElement('b');s.textContent=item.qty+' × '+item.name;b.textContent=money(item.priceCents*item.qty);row.append(s,b);items.append(row);}
    $('pay-total').textContent=money(S.total(a));$('pay-paid').textContent=money(S.paid(a));$('pay-due').textContent=money(S.due(a));
    const list=$('payment-list');list.replaceChildren();
    if(!a.payments.length){list.textContent='Nenhum pagamento registrado.';}
    for(const p of a.payments){const tr=document.createElement('tr');
      for(const val of [p.method==='dinheiro'?'Dinheiro':p.method==='pix'?'Pix':'Cartão',money(p.receivedCents),money(p.appliedCents),money(p.changeCents)]){
        const td=document.createElement('td');td.textContent=val;tr.append(td);}
      list.append(tr);
    }
    $('pay-form').hidden=S.due(a)===0;
    $('closebutton').disabled=S.due(a)>0||a.items.length===0;
    $('payment-status').textContent=a.items.length===0?'ⓘ Registre itens antes de pagar.':S.due(a)===0?'✓ Conta quitada. Você já pode encerrar a comanda.':'ⓘ Saldo pendente: '+money(S.due(a))+'. Você pode pagar parcialmente.';
  }
  function centsFromInput(value) {
    const v=String(value).trim().replace(',','.');
    if(!/^\d+(?:\.\d{1,2})?$/.test(v))throw new Error('Informe um valor válido, com no máximo duas casas decimais.');
    const [integer,decimal='']=v.split('.');
    const cents=Number(integer)*100+Number(decimal.padEnd(2,'0'));
    if(!Number.isSafeInteger(cents)||cents<=0)throw new Error('Informe um valor maior que zero.');
    return cents;
  }
  function initPayments() {
    if(!renderContext())return;
    renderPayments();
    $('pay-form').addEventListener('submit',event=>{
      event.preventDefault();
      try{
        const p=S.pay(tableNo(),$('pay-method').value,centsFromInput($('pay-value').value));
        $('pay-value').value='';renderPayments();
        notify('✓ Pagamento registrado: '+money(p.appliedCents)+' aplicado(s)'+(p.changeCents?' · Troco: '+money(p.changeCents):'')+'.','good');
      }catch(e){notify('⚠ '+e.message,'warn');}
    });
    $('closebutton').addEventListener('click',()=>{
      try{const closed=S.close(tableNo());
        sessionStorage.removeItem('barflow-current-table');
        $('flow-panel').hidden=true;$('empty-state').hidden=false;
        $('empty-state').textContent='✓ Comanda #'+closed.id+' encerrada. Mesa '+String(closed.tableNo).padStart(2,'0')+' liberada. Volte ao painel de mesas.';
        notify('✓ Comanda encerrada com sucesso.','good');
      }catch(e){notify('⚠ '+e.message,'warn');}
    });
  }
  document.addEventListener('DOMContentLoaded',()=>{
    setupNavigation();
    const page=document.body.dataset.page;
    if(page==='mesas')renderTables();
    if(page==='pedidos')renderOrders();
    if(page==='pagamentos')initPayments();
  });
})();
