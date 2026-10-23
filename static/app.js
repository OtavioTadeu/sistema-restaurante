document.addEventListener('DOMContentLoaded', () => {

    const $ = (sel) => document.querySelector(sel);
    const meta = (name) => {
        const el = document.querySelector(`meta[name="${name}"]`);
        return el ? el.getAttribute('content') : '';
    };

    // Dados injetados pelo backend
    const RESTAURANTE_WHATSAPP = meta('restaurante-whatsapp');
    const TAXA_ENTREGA = parseFloat(meta('taxa-entrega')) || 0;
    const CSRF_TOKEN = meta('csrf-token');
    const LOJA_ABERTA = meta('loja-aberta') !== '0';

    const brl = (v) => 'R$ ' + v.toFixed(2).replace('.', ',');
    const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const cartList = $('#lista-carrinho');
    if (!cartList) return;

    const subtotalEl = $('#subtotal-carrinho');
    const totalEl = $('#total-carrinho');
    const badge = $('#cart-badge');
    const linhaTaxa = $('#linha-taxa-entrega');
    const valorTaxa = $('#valor-taxa-entrega');
    const clearBtn = $('#clear-cart-btn');
    const cartBar = $('#cart-bar');
    const cartBarCount = $('#cart-bar-count');
    const cartBarTotal = $('#cart-bar-total');

    const form = $('#form-pedido');
    const btnFinalizar = $('#btn-finalizar');
    const tipoRetirada = $('#tipo_retirada');
    const tipoEntrega = $('#tipo_entrega');
    const campoEndereco = $('#campo_endereco');
    const formaPagamento = $('#forma_pagamento');
    const campoTroco = $('#campo_troco');

    const modal = $('#success-modal');
    const btnCloseModal = $('#btn-close-modal');
    const btnWhatsapp = $('#btn-whatsapp');
    const modalPedidoId = $('#modal-pedido-id');

    const EMPTY_HTML = cartList.innerHTML;
    let cart = [];

    const isEntrega = () => tipoEntrega && tipoEntrega.checked;
    const subtotal = () => cart.reduce((acc, i) => acc + i.preco * i.quantidade, 0);
    const count = () => cart.reduce((acc, i) => acc + i.quantidade, 0);
    const taxaAtual = () => (isEntrega() ? TAXA_ENTREGA : 0);

    function bumpBadge() {
        badge.classList.remove('bump');
        void badge.offsetWidth;
        badge.classList.add('bump');
        setTimeout(() => badge.classList.remove('bump'), 180);
    }

    // ---- Adicionar ao pedido ----
    document.querySelectorAll('.btn-add-item').forEach((button) => {
        button.addEventListener('click', () => {
            if (!LOJA_ABERTA) return;

            const novo = {
                pratoId: button.dataset.pratoId,
                pratoNome: button.dataset.pratoNome,
                tamanhoId: button.dataset.tamanhoId,
                tamanhoNome: button.dataset.tamanhoNome,
                preco: parseFloat(button.dataset.preco),
                quantidade: 1
            };

            const existente = cart.find((i) => i.pratoId === novo.pratoId && i.tamanhoId === novo.tamanhoId);
            if (existente) existente.quantidade++;
            else cart.push(novo);

            render();
            bumpBadge();

            // feedback no botão
            const original = button.innerHTML;
            button.classList.add('is-added');
            button.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-check"></use></svg>';
            clearTimeout(button._t);
            button._t = setTimeout(() => {
                button.classList.remove('is-added');
                button.innerHTML = original;
            }, 700);
        });
    });

    // ---- Render do carrinho ----
    function render() {
        const sub = subtotal();
        const qtd = count();
        const taxa = cart.length ? taxaAtual() : 0;
        const total = sub + taxa;

        badge.textContent = qtd;

        if (!cart.length) {
            cartList.innerHTML = EMPTY_HTML;
        } else {
            cartList.innerHTML = cart.map((item, idx) => `
                <li class="line">
                    <div>
                        <div class="line-name">${esc(item.pratoNome)}</div>
                        <div class="line-size">${esc(item.tamanhoNome)} · ${brl(item.preco)}</div>
                    </div>
                    <div class="line-total">${brl(item.preco * item.quantidade)}</div>
                    <div></div>
                    <div class="stepper" role="group" aria-label="Quantidade de ${esc(item.pratoNome)}">
                        <button type="button" data-action="dec" data-index="${idx}" aria-label="Diminuir">
                            <svg class="icon" aria-hidden="true"><use href="#i-${item.quantidade === 1 ? 'trash' : 'minus'}"></use></svg>
                        </button>
                        <output>${item.quantidade}</output>
                        <button type="button" data-action="inc" data-index="${idx}" aria-label="Aumentar">
                            <svg class="icon" aria-hidden="true"><use href="#i-plus"></use></svg>
                        </button>
                    </div>
                </li>
            `).join('');
        }

        if (subtotalEl) subtotalEl.textContent = brl(sub);
        totalEl.textContent = brl(total);

        if (linhaTaxa) {
            const mostrar = isEntrega() && TAXA_ENTREGA > 0;
            linhaTaxa.hidden = !mostrar;
            if (valorTaxa) valorTaxa.textContent = brl(TAXA_ENTREGA);
        }

        if (cartBar) {
            cartBar.classList.toggle('is-visible', qtd > 0);
            document.body.classList.toggle('has-cart-bar', qtd > 0);
            cartBarCount.textContent = qtd;
            cartBarTotal.textContent = brl(total);
        }
    }

    cartList.addEventListener('click', (e) => {
        const btn = e.target.closest('button[data-action]');
        if (!btn) return;
        const idx = parseInt(btn.dataset.index, 10);
        const item = cart[idx];
        if (!item) return;
        if (btn.dataset.action === 'inc') item.quantidade++;
        else {
            item.quantidade--;
            if (item.quantidade <= 0) cart.splice(idx, 1);
        }
        render();
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (cart.length && confirm('Remover todos os itens do pedido?')) {
                cart = [];
                render();
            }
        });
    }

    if (cartBar) {
        cartBar.addEventListener('click', () => {
            $('#carrinho-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    // ---- Tipo de pedido / pagamento ----
    const syncTipo = () => {
        if (campoEndereco) campoEndereco.hidden = !isEntrega();
        render();
    };
    if (tipoRetirada) tipoRetirada.addEventListener('change', syncTipo);
    if (tipoEntrega) tipoEntrega.addEventListener('change', syncTipo);

    if (formaPagamento && campoTroco) {
        formaPagamento.addEventListener('change', () => {
            campoTroco.hidden = formaPagamento.value !== 'DINHEIRO';
        });
    }

    // ---- Mensagem do WhatsApp ----
    function textoWhatsApp(pedidoId, dados, itens, sub, taxa) {
        let t = `*PEDIDO Nº ${pedidoId} — Dogão do Castelo*\n\n`;
        t += `*Cliente:* ${dados.nome_cliente}\n`;
        t += `*WhatsApp:* ${dados.telefone_cliente}\n`;
        t += `*Tipo:* ${dados.tipo_pedido === 'ENTREGA' ? 'Entrega' : 'Retirada'}\n`;
        if (dados.tipo_pedido === 'ENTREGA') t += `*Endereço:* ${dados.endereco_cliente}\n`;
        t += `*Pagamento:* ${dados.forma_pagamento}\n`;
        if (dados.forma_pagamento === 'DINHEIRO' && dados.troco_para) t += `*Troco para:* ${dados.troco_para}\n`;
        if (dados.observacoes && dados.observacoes.trim()) t += `\n*Observações:* ${dados.observacoes.trim()}\n`;

        t += `\n*Itens*\n`;
        itens.forEach((i) => {
            t += `${i.quantidade}x ${i.pratoNome} (${i.tamanhoNome}) — ${brl(i.preco * i.quantidade)}\n`;
        });
        if (taxa > 0) t += `Taxa de entrega — ${brl(taxa)}\n`;
        t += `\n*TOTAL: ${brl(sub + taxa)}*`;
        return encodeURIComponent(t);
    }

    // ---- Envio ----
    function validar() {
        const nome = $('#nome_cliente');
        const tel = $('#telefone_cliente');
        const end = $('#endereco_cliente');
        if (!cart.length) return 'Adicione pelo menos um item ao pedido.';
        if (!nome.value.trim()) { nome.focus(); return 'Informe seu nome.'; }
        if (tel.value.replace(/\D/g, '').length < 10) { tel.focus(); return 'Informe um WhatsApp válido com DDD.'; }
        if (isEntrega() && !end.value.trim()) { end.focus(); return 'Informe o endereço de entrega.'; }
        if (!formaPagamento.value) { formaPagamento.focus(); return 'Escolha a forma de pagamento.'; }
        return null;
    }

    if (form && btnFinalizar) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            if (!LOJA_ABERTA) return;

            const erro = validar();
            if (erro) { alert(erro); return; }

            btnFinalizar.disabled = true;
            btnFinalizar.textContent = 'Enviando…';

            const dados = Object.fromEntries(new FormData(form).entries());
            const headers = { 'Content-Type': 'application/json' };
            if (CSRF_TOKEN) headers['X-CSRFToken'] = CSRF_TOKEN;

            fetch('/api/finalizar_pedido', {
                method: 'POST',
                headers,
                body: JSON.stringify({ pedido: dados, carrinho: cart })
            })
                .then((r) => r.json())
                .then((data) => {
                    if (!data.success) {
                        alert(data.message || 'Não foi possível finalizar o pedido.');
                        return;
                    }
                    const sub = subtotal();
                    const taxa = dados.tipo_pedido === 'ENTREGA' ? TAXA_ENTREGA : 0;

                    modalPedidoId.textContent = data.pedido_id;
                    btnWhatsapp.href = `https://api.whatsapp.com/send?phone=${RESTAURANTE_WHATSAPP}&text=${textoWhatsApp(data.pedido_id, dados, cart, sub, taxa)}`;
                    modal.classList.add('is-open');

                    cart = [];
                    $('#observacoes').value = '';
                    $('#troco_para').value = '';
                    render();
                })
                .catch(() => alert('Falha de conexão. Verifique sua internet e tente novamente.'))
                .finally(() => {
                    btnFinalizar.disabled = false;
                    btnFinalizar.textContent = 'Finalizar pedido';
                });
        });
    }

    const fecharModal = () => modal.classList.remove('is-open');
    if (btnCloseModal) btnCloseModal.addEventListener('click', fecharModal);
    if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) fecharModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharModal(); });

    render();
});