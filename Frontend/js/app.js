// BarFlow: protótipo demonstrativo, sem backend e sem persistência real.
const $ = id => document.getElementById(id);
const pages = {mesas: 'index.html', pedidos: 'pedidos.html', pagamentos: 'pagamentos.html'};
let occupied;
try { occupied = new Set(JSON.parse(sessionStorage.getItem('barflow-demo-mesas') || '[2,4,7,9]')); }
catch { occupied = new Set([2,4,7,9]); }
const persistTables = () => sessionStorage.setItem('barflow-demo-mesas', JSON.stringify([...occupied]));
const money = n => n.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
function go(page) { if (pages[page]) window.location.href = pages[page]; }
function drawTables() {
  if (!$('tables')) return;
  let html = '';
  for (let i = 1; i <= 10; i++) {
    const busy = occupied.has(i);
    html += '<article class="tablecard ' + (busy ? 'occupied' : '') + ' ' + (i === 3 ? 'selected' : '') +
      '"><div class="tableupper"><b>Mesa ' + String(i).padStart(2, '0') + '</b><span class="status ' +
      (busy ? 'busy' : 'free') + '">' + (busy ? '◷ Ocupada' : '✓ Livre') +
      '</span></div><p>' + (busy ? 'Comanda em andamento' : 'Disponível para atendimento') +
      '</p><button type="button" data-table="' + i + '">' +
      (busy ? 'Visualizar comanda' : '＋ Abrir comanda') + '</button></article>';
  }
  $('tables').innerHTML = html;
  $('freecount').textContent = 10 - occupied.size;
  $('busycount').textContent = occupied.size;
}
function openTable(n) {
  if (n === 3) {
    // O fluxo demonstrativo apresenta a comanda fictícia 101 da Mesa 03.
    occupied.add(3); persistTables(); go('pedidos');
  } else {
    alert('O fluxo completo desta demonstração utiliza a Mesa 03. As demais mesas ainda não possuem formulário próprio.');
  }
}
function addItem() {
  const q = Number($('quantity').value);
  if (!Number.isInteger(q) || q <= 0) {
    $('order-feedback').className = 'notice warn';
    $('order-feedback').textContent = '⚠ Quantidade inválida. Informe um número inteiro maior que zero.';
    return;
  }
  $('order-feedback').className = 'notice info';
  $('order-feedback').textContent = 'ⓘ Item conferido. Use “Confirmar pedido” para concluir o registro.';
}
function confirmOrder() {
  const q = Number($('quantity').value);
  if (!Number.isInteger(q) || q <= 0) { addItem(); return; }
  $('order-feedback').className = 'notice good';
  $('order-feedback').textContent = '✓ Pedido registrado na demonstração. O total da comanda permanece ilustrativo.';
}
function closeAccount() {
  occupied.delete(3); persistTables();
  $('closebutton').disabled = true;
  $('closebutton').textContent = '✓ Comanda encerrada';
  $('success-title').textContent = 'Comanda #101 encerrada com sucesso';
  $('success-desc').textContent = 'Mesa 03 liberada para um novo atendimento.';
  $('closing-info').textContent = '✓ Histórico preservado na demonstração.';
}
document.addEventListener('DOMContentLoaded', () => {
  drawTables();
  $('tables')?.addEventListener('click', event => {
    const button = event.target.closest('button[data-table]');
    if (button) openTable(Number(button.dataset.table));
  });
  $('product')?.addEventListener('change', event => {
    $('unit-price').value = money(Number(event.target.value));
  });
});
