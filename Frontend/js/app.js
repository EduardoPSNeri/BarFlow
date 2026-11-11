'use strict';
const $=id=>document.getElementById(id);
const money=n=>(n/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const tableNo=Number(new URLSearchParams(location.search).get('mesa')||sessionStorage.getItem('barflow-current-table'));
const qs=(page,n)=>page+'.html'+(n?'?mesa='+n:'');
let me=null;
async function api(path,method='GET',data){
  const headers={};if(data!==undefined)headers['Content-Type']='application/json';
  if(method!=='GET')headers['X-CSRF-Token']=sessionStorage.getItem('barflow-csrf')||'';
  let response;
  try{response=await fetch('/api'+path,{method,headers,body:data===undefined?undefined:JSON.stringify(data),credentials:'same-origin'});}catch{throw Error('Não foi possível conectar ao servidor local.');}
  const json=await response.json().catch(()=>({}));
  if(response.status===401){sessionStorage.removeItem('barflow-csrf');if(!['login','alterar-senha'].includes(document.body.dataset.page))location.replace('login.html');throw Error('Sessão expirada. Entre novamente.');}
  if(!response.ok)throw Error(typeof json.detail==='string'?json.detail:'Erro na operação.');
  return json;
}
function notify(message,type='info'){
  let f=$('feedback');if(!f){alert(message);return;}f.className='notice '+type;f.textContent=message;f.hidden=false;f.setAttribute('role','status');
}
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function labelContext(account){
  for(const e of document.querySelectorAll('[data-mesa]'))e.textContent=String(account.table_number).padStart(2,'0');
  for(const e of document.querySelectorAll('[data-comanda]'))e.textContent='#'+account.id;
}
async function context(){
  if(!Number.isInteger(tableNo)||tableNo<1){$('flow-panel').hidden=true;$('empty-state').hidden=false;$('empty-state').textContent='Selecione uma mesa no Painel de mesas.';return null;}
  try{let account=await api('/tables/'+tableNo+'/account');$('flow-panel').hidden=false;$('empty-state').hidden=true;labelContext(account);return account;}
  catch(e){$('flow-panel').hidden=true;$('empty-state').hidden=false;$('empty-state').textContent=e.message;return null;}
}
function cart(account){let list=$('order-items');list.replaceChildren();if(!account.items.length)list.textContent='Nenhum item registrado.';
  for(const item of account.items){let row=element('div',undefined,'cartline'),a=element('div'),b=element('strong',item.name),sm=element('small',item.qty+' × '+money(item.price_cents)),p=element('span',money(item.qty*item.price_cents),'price');a.append(b,sm);row.append(a,p);list.append(row);}
  $('order-total').textContent=money(account.total_cents);
}
async function tables(){const state=await api('/tables');let occupied=state.filter(t=>t.account).length;
  $('all-count').textContent=state.length;$('busy-count').textContent=occupied;$('free-count').textContent=state.length-occupied;
  $('tables').replaceChildren();for(const item of state){
    let card=element('article',undefined,'tablecard'+(item.account?' occupied':''));
    let upper=element('div',undefined,'tableupper');upper.append(element('b','Mesa '+String(item.number).padStart(2,'0')),element('span',item.account?'◷ Ocupada':'✓ Livre','status '+(item.account?'busy':'free')));
    let p=element('p',item.account?'Comanda #'+item.account.id+' · '+money(item.account.due_cents)+' pendente':'Disponível para atendimento');
    let btn=element('button',item.account?'Visualizar comanda':'＋ Abrir comanda');btn.type='button';btn.disabled=!item.active;
    btn.onclick=async()=>{try{await api('/tables/'+item.number+'/open','POST');sessionStorage.setItem('barflow-current-table',item.number);location.href=qs('pedidos',item.number);}catch(e){notify('⚠ '+e.message,'warn');}};
    card.append(upper,p,btn);
    if(item.account&&!item.account.items.length&&!item.account.payments.length&&me.role==='ADMINISTRADOR'){
      const cancel=element('button','Cancelar comanda vazia');cancel.type='button';cancel.className='cancel-action';
      cancel.onclick=async()=>{const reason=prompt('Justificativa para cancelar a comanda (mínimo 5 caracteres):');if(reason===null)return;try{await api('/tables/'+item.number+'/cancel','POST',{reason});await tables();notify('✓ Comanda vazia cancelada.','good');}catch(e){notify('⚠ '+e.message,'warn');}};
      card.append(cancel);
    }
    $('tables').append(card);
  }
}
async function orders(){let account=await context();if(!account)return;
  const products=(await api('/products')).filter(p=>p.active);let select=$('product');select.replaceChildren();
  for(const p of products){let option=element('option',p.name+' — '+money(p.price_cents));option.value=p.id;select.append(option);}
  const price=()=>{$('unit-price').value=money(products.find(p=>String(p.id)===select.value)?.price_cents||0);};select.onchange=price;price();cart(account);
  $('order-form').onsubmit=async(e)=>{e.preventDefault();try{
    const qty=Number($('quantity').value);if(!Number.isInteger(qty)||qty<=0||qty>999)throw Error('Informe quantidade inteira de 1 a 999.');
    await api('/tables/'+tableNo+'/items','POST',{product_id:Number(select.value),qty,request_id:crypto.randomUUID()});account=await api('/tables/'+tableNo+'/account');cart(account);notify('✓ Item registrado na comanda.','good');
  }catch(error){notify('⚠ '+error.message,'warn');}};
  $('to-payments').href=qs('pagamentos',tableNo);
}
function payRender(account){
  const items=$('pay-items');items.replaceChildren();for(const item of account.items){let r=element('div',undefined,'summaryrow');r.append(element('span',item.qty+' × '+item.name),element('b',money(item.qty*item.price_cents)));items.append(r);}
  $('pay-total').textContent=money(account.total_cents);$('pay-paid').textContent=money(account.paid_cents);$('pay-due').textContent=money(account.due_cents);
  const list=$('payment-list');list.replaceChildren();for(const p of account.payments){let tr=element('tr');for(const value of [p.method,money(p.received_cents),money(p.applied_cents),money(p.change_cents)])tr.append(element('td',value));list.append(tr);}
  $('pay-form').hidden=account.due_cents===0;$('closebutton').disabled=account.due_cents>0||account.items.length===0;
  $('payment-status').textContent=!account.items.length?'ⓘ Registre produtos antes de pagar.':account.due_cents===0?'✓ Conta quitada. Pode encerrar.':'ⓘ Saldo pendente: '+money(account.due_cents);
}
function cents(value){let v=String(value).trim().replace(',','.');if(!/^\d+(\.\d{1,2})?$/.test(v))throw Error('Use um valor positivo com até duas casas decimais.');let n=Math.round(Number(v)*100);if(!Number.isSafeInteger(n)||n<=0)throw Error('Valor inválido.');return n;}
async function payments(){let account=await context();if(!account)return;payRender(account);$('back-to-orders').href=qs('pedidos',tableNo);
  $('pay-form').onsubmit=async(e)=>{e.preventDefault();try{
    const r=await api('/tables/'+tableNo+'/payments','POST',{method:$('pay-method').value,received_cents:cents($('pay-value').value),request_id:crypto.randomUUID()});
    account=await api('/tables/'+tableNo+'/account');payRender(account);$('pay-value').value='';notify('✓ Pagamento aplicado: '+money(r.applied_cents)+(r.change_cents?' · Troco: '+money(r.change_cents):''),'good');
  }catch(err){notify('⚠ '+err.message,'warn');}};
  $('closebutton').onclick=async()=>{try{await api('/tables/'+tableNo+'/close','POST');sessionStorage.removeItem('barflow-current-table');$('flow-panel').hidden=true;$('empty-state').hidden=false;$('empty-state').textContent='✓ Comanda encerrada, mesa liberada. Volte ao painel.';notify('✓ Comanda encerrada com sucesso.','good');}catch(err){notify('⚠ '+err.message,'warn');}};
}
function tableRow(table,cells){let tr=element('tr');for(const c of cells)tr.append(element('td',String(c)));table.append(tr);}
async function stock(){const products=await api('/products');let list=$('product-list');list.replaceChildren();for(const p of products){let tr=element('tr');for(const txt of [p.name,money(p.price_cents),p.stock_qty,p.track_stock?'Sim':'Não',p.active?'Ativo':'Inativo'])tr.append(element('td',String(txt)));list.append(tr);}
  $('stock-product').replaceChildren();for(const p of products){let o=element('option',p.name);o.value=p.id;$('stock-product').append(o);}
  const settings=await api('/settings');$('allow-negative').checked=settings.allow_negative_stock;
  if(me.role!=='ADMINISTRADOR')for(const id of ['create-product-form','stock-form','stock-setting-form'])$(id).hidden=true;
  else{
    $('create-product-form').onsubmit=async e=>{e.preventDefault();try{await api('/products','POST',{name:$('prod-name').value.trim(),price_cents:cents($('prod-price').value),stock_qty:Number($('prod-stock').value),track_stock:$('prod-track').checked,active:true});location.reload();}catch(err){notify(err.message,'warn');}};
    $('stock-form').onsubmit=async e=>{e.preventDefault();try{await api('/products/'+$('stock-product').value+'/stock','POST',{delta:Number($('stock-delta').value),reason:$('stock-reason').value});location.reload();}catch(err){notify(err.message,'warn');}};
    $('stock-setting-form').onsubmit=async e=>{e.preventDefault();try{await api('/settings','PUT',{allow_negative_stock:$('allow-negative').checked});notify('✓ Configuração atualizada.','good');}catch(err){notify(err.message,'warn');}};
  }
  const movements=await api('/stock/movements');for(const m of movements)tableRow($('movement-list'),[m.product,m.delta,m.reason,new Date(m.created_at).toLocaleString('pt-BR')]);
}
async function cash(){let current=await api('/cash/current');let status=$('cash-status');status.textContent=current.open?'✓ Caixa aberto · início: '+money(current.starting_cash_cents)+' · dinheiro previsto: '+money(current.expected_cash_cents):'ⓘ Nenhum caixa aberto.';
  $('cash-open-form').hidden=current.open;$('cash-close-form').hidden=!current.open||me.role!=='ADMINISTRADOR';
  if(current.open){for(const m of ['pix','cartao','dinheiro'])$(m+'-total').textContent=money(current.totals[m]);}
  $('cash-open-form').onsubmit=async e=>{e.preventDefault();try{await api('/cash/open','POST',{starting_cash_cents:Math.max(0,centsOrZero($('cash-start').value))});location.reload();}catch(err){notify(err.message,'warn');}};
  $('cash-close-form').onsubmit=async e=>{e.preventDefault();try{let r=await api('/cash/close','POST',{counted_cash_cents:centsOrZero($('cash-end').value)});notify('✓ Caixa encerrado. Diferença: '+money(r.difference_cents),'good');$('cash-close-form').hidden=true;setTimeout(()=>location.reload(),800);}catch(err){notify(err.message,'warn');}};
}
function centsOrZero(s){return String(s).trim()==='0'?0:cents(s);}
async function reports(){let data=await api('/reports/summary');$('closed-count').textContent=data.closed_accounts;$('report-sales').textContent=money(data.gross_sales_cents);$('open-count').textContent=data.open_accounts;$('today-sales').textContent=money(data.today_sales_cents);
  for(const [method,n] of Object.entries(data.payments_cents))$(method+'-report').textContent=money(n);
  for(const row of data.history)tableRow($('report-list'),['#'+row.id,'Mesa '+row.table_number,money(row.total_cents),new Date(row.closed_at).toLocaleString('pt-BR')]);
}
async function users(){let users=await api('/users');for(const u of users)tableRow($('user-list'),[u.username,u.role,u.active?'Ativo':'Inativo']);
  $('user-form').onsubmit=async e=>{e.preventDefault();try{await api('/users','POST',{username:$('new-username').value,password:$('new-password').value,role:$('new-role').value});location.reload();}catch(err){notify(err.message,'warn');}};
}
async function login(){const form=$('login-form');form.onsubmit=async e=>{e.preventDefault();try{let data=await api('/auth/login','POST',{username:$('username').value,password:$('password').value});sessionStorage.setItem('barflow-csrf',data.csrf_token);location.replace(data.user.must_change_password?'alterar-senha.html':'index.html');}catch(err){notify(err.message,'warn');}};}
async function passwordChange(){
  const form=$('password-change-form');
  const profile=await api('/auth/me');
  $('password-change-hint').textContent=profile.must_change_password?'Troca obrigatória: defina uma senha de entre 4 e 20 caracteres.':'Para atualizar sua senha, informe a atual e escolha uma nova senha de entre 4 e 20 caracteres.';
  form.onsubmit=async e=>{e.preventDefault();try{
    const next=$('new-password').value;
    if(next!==$('confirm-password').value)throw Error('As senhas novas não coincidem.');
    await api('/auth/change-password','POST',{current_password:$('current-password').value,new_password:next});
    sessionStorage.removeItem('barflow-csrf');
    alert('Senha alterada com sucesso. Faça login com sua nova senha.');
    location.replace('login.html');
  }catch(error){notify('⚠ '+error.message,'warn');}};
}
async function init(){try{
  const page=document.body.dataset.page;
  if(page==='login'){await login();return;}
  if(page==='alterar-senha'){await passwordChange();return;}
  me=await api('/auth/me');
  if(me.must_change_password){location.replace('alterar-senha.html');return;}document.querySelectorAll('.user-identity strong').forEach(e=>e.textContent=me.username);document.querySelectorAll('.user-identity small').forEach(e=>e.textContent='Perfil: '+me.role);
  const nav=document.querySelector('.nav');if(nav){for(const [name,file] of [['Estoque','estoque'],['Caixa','caixa'],['Relatórios','relatorios'],['Usuários','usuarios'],['Minha senha','alterar-senha']]){if(['Relatórios','Usuários'].includes(name)&&me.role!=='ADMINISTRADOR')continue;const a=element('a',name);a.href=file+'.html';a.className=document.body.dataset.page===file?'active':'';nav.append(a);}}
  for(const id of ['reset-demo'])$(id)?.remove();const logout=$('logout-demo');if(logout){logout.onclick=async()=>{try{await api('/auth/logout','POST');}finally{sessionStorage.removeItem('barflow-csrf');location.assign('login.html');}};}
  for(const id of ['nav-pedidos','nav-pagamentos'])if($(id)&&tableNo)$(id).href=qs(id==='nav-pedidos'?'pedidos':'pagamentos',tableNo);
  if(page==='mesas')await tables();if(page==='pedidos')await orders();if(page==='pagamentos')await payments();if(page==='estoque')await stock();if(page==='caixa')await cash();if(page==='relatorios')await reports();if(page==='usuarios')await users();
}catch(e){notify('⚠ '+e.message,'warn');}}
document.addEventListener('DOMContentLoaded',init);
