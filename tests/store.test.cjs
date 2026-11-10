'use strict';

// Testes do frontend demonstrativo; sem dependencias externas.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'Frontend', 'js', 'store.js'), 'utf8');

function loadStore() {
  const data = new Map();
  const storage = {
    getItem: (key) => data.has(key) ? data.get(key) : null,
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  };
  const context = { window: {}, localStorage: storage, sessionStorage: storage, Date, Math, JSON };
  vm.runInNewContext(source, context, { filename: 'store.js' });
  return context.window.BarFlowStore;
}

test('abre comandas independentes em mesas diferentes sem duplicar a mesma mesa', () => {
  const store = loadStore();
  const first = store.open(3);
  const second = store.open(5);
  assert.notEqual(first.id, second.id);
  assert.equal(store.open(3).id, first.id);
  assert.equal(store.read().accounts.filter(a => a.status === 'OPEN').length, 2);
});

test('recusa quantidade invalida e produto inexistente', () => {
  const store = loadStore();
  store.open(5);
  assert.throws(() => store.addItem(5, 'refri', 0), /quantidade/i);
  assert.throws(() => store.addItem(5, 'refri', 1.5), /quantidade/i);
  assert.throws(() => store.addItem(5, 'inexistente', 1), /produto/i);
});

test('calcula valor de pedido, pagamento parcial e troco em centavos', () => {
  const store = loadStore();
  store.open(5);
  store.addItem(5, 'refri', 2);  // R$ 16,00
  store.addItem(5, 'batata', 1); // R$ 35,00
  assert.equal(store.total(store.account(5)), 5100);
  const pix = store.pay(5, 'pix', 3000);
  assert.equal(pix.appliedCents, 3000);
  assert.equal(store.due(store.account(5)), 2100);
  const cash = store.pay(5, 'dinheiro', 2500);
  assert.equal(cash.appliedCents, 2100);
  assert.equal(cash.changeCents, 400);
  assert.equal(store.due(store.account(5)), 0);
});

test('bloqueia pagamento nao monetario acima do saldo', () => {
  const store = loadStore();
  store.open(1);
  store.addItem(1, 'agua', 1);
  assert.throws(() => store.pay(1, 'pix', 700), /saldo/i);
  assert.throws(() => store.pay(1, 'cartao', 700), /saldo/i);
});

test('impede encerrar comanda vazia ou com saldo pendente', () => {
  const store = loadStore();
  store.open(4);
  assert.throws(() => store.close(4), /vazia/i);
  store.addItem(4, 'agua', 1);
  assert.throws(() => store.close(4), /pendente/i);
});

test('encerrar apos quitacao libera mesa e preserva historico', () => {
  const store = loadStore();
  const account = store.open(4);
  store.addItem(4, 'agua', 1);
  store.pay(4, 'dinheiro', 600);
  assert.equal(store.close(4).status, 'CLOSED');
  assert.equal(store.account(4), null);
  const next = store.open(4);
  assert.notEqual(next.id, account.id);
  assert.equal(store.read().accounts.some(a => a.id === account.id && a.status === 'CLOSED'), true);
});
