document.addEventListener('DOMContentLoaded', () => {

    const addButtons = document.querySelectorAll('.btn-add-item');
    const cartList = document.getElementById('lista-carrinho');
    const subtotalSpan = document.getElementById('subtotal-carrinho');
    const cartTotalSpan = document.getElementById('total-carrinho');
    const clearCartBtn = document.getElementById('clear-cart-btn');
    const cartBadge = document.getElementById('cart-badge');
    const linhaTaxaEntrega = document.getElementById('linha-taxa-entrega');
    const valorTaxaSpan = document.getElementById('valor-taxa-entrega');
    
    const formPedido = document.getElementById('form-pedido');
    const btnFinalizar = document.getElementById('btn-finalizar');
    const tipoRetirada = document.getElementById('tipo_retirada');
    const tipoEntrega = document.getElementById('tipo_entrega');
    const campoEndereco = document.getElementById('campo_endereco');

    const modalOverlay = document.getElementById('success-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnWhatsapp = document.getElementById('btn-whatsapp');
    const modalPedidoId = document.getElementById('modal-pedido-id');

    // Metadados dinâmicos injetados com segurança pelo backend
    const metaWhatsapp = document.querySelector('meta[name="restaurante-whatsapp"]');
    const RESTAURANTE_WHATSAPP = metaWhatsapp ? metaWhatsapp.getAttribute('content') : "553194585341";

    const metaTaxa = document.querySelector('meta[name="taxa-entrega"]');
    const TAXA_ENTREGA = metaTaxa ? (parseFloat(metaTaxa.getAttribute('content')) || 0) : 0;

    const metaCsrf = document.querySelector('meta[name="csrf-token"]');
    const CSRF_TOKEN = metaCsrf ? metaCsrf.getAttribute('content') : "";

    const metaLoja = document.querySelector('meta[name="loja-aberta"]');
    const LOJA_ABERTA = metaLoja ? metaLoja.getAttribute('content') === '1' : true;

    let cart = [];

    // Adicionar item ao carrinho
    addButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (!LOJA_ABERTA) {
                alert('A lanchonete está fechada no momento.');
                return;
            }

            const item = {
                pratoId: button.dataset.pratoId,
                pratoNome: button.dataset.pratoNome,
                tamanhoId: button.dataset.tamanhoId,
                tamanhoNome: button.dataset.tamanhoNome,
                preco: parseFloat(button.dataset.preco),
                quantidade: 1
            };
            addToCart(item);
            
            // Feedback visual no botão
            if (!button.dataset.originalHtml) {
                button.dataset.originalHtml = button.innerHTML;
            }
            
            if (button._resetTimer) {
                clearTimeout(button._resetTimer);
            }
            
            button.innerHTML = '✓ Adicionado';
            button.style.background = 'var(--success)';
            button.style.color = '#fff';
            button.style.borderColor = 'var(--success)';
            
            button._resetTimer = setTimeout(() => {
                button.innerHTML = button.dataset.originalHtml;
                button.style.background = '';
                button.style.color = '';
                button.style.borderColor = '';
                button._resetTimer = null;
            }, 800);
            
            // Animação no badge
            cartBadge.classList.remove('bump');
            void cartBadge.offsetWidth;
            cartBadge.classList.add('bump');
            setTimeout(() => cartBadge.classList.remove('bump'), 200);
        });
    });

    function addToCart(newItem) {
        let itemExists = false;
        let totalItems = 0;
        for (let item of cart) {
            if (item.pratoId === newItem.pratoId && item.tamanhoId === newItem.tamanhoId) {
                item.quantidade++;
                itemExists = true;
            }
            totalItems += item.quantidade;
        }
        if (!itemExists) {
            cart.push(newItem);
            totalItems++;
        }
        cartBadge.innerText = totalItems;
        renderCart();
    }

    function renderCart() {
        cartList.innerHTML = '';
        if (cart.length === 0) {
            cartList.innerHTML = '<div class="empty-cart-msg">Seu carrinho está vazio.</div>';
            if (subtotalSpan) subtotalSpan.textContent = 'R$ 0.00';
            cartTotalSpan.textContent = 'R$ 0.00';
            cartBadge.innerText = '0';
            if (linhaTaxaEntrega) linhaTaxaEntrega.style.display = 'none';
            return;
        }

        let subtotal = 0;
        let count = 0;
        cart.forEach((item, index) => {
            const itemTotal = item.preco * item.quantidade;
            subtotal += itemTotal;
            count += item.quantidade;

            const itemElement = document.createElement('div');
            itemElement.classList.add('carrinho-item');

            itemElement.innerHTML = `
                <div class="carrinho-item-header">
                    <strong>${item.quantidade}x ${item.pratoNome}</strong>
                    <a href="#" class="btn-remove" data-index="${index}">X</a>
                </div>
                <div class="carrinho-item-actions">
                    <span style="color: var(--text-muted); font-size: 0.9em;">Tam: ${item.tamanhoNome}</span>
                    <strong style="color: var(--primary);">R$ ${itemTotal.toFixed(2)}</strong>
                </div>
            `;
            cartList.appendChild(itemElement);
        });

        cartBadge.innerText = count;
        if (subtotalSpan) subtotalSpan.textContent = `R$ ${subtotal.toFixed(2)}`;

        // Calcular frete se for Entrega
        const isEntrega = tipoEntrega && tipoEntrega.checked;
        let valorFrete = (isEntrega && TAXA_ENTREGA > 0) ? TAXA_ENTREGA : 0;

        if (linhaTaxaEntrega) {
            if (isEntrega && TAXA_ENTREGA > 0) {
                linhaTaxaEntrega.style.display = 'flex';
                if (valorTaxaSpan) valorTaxaSpan.textContent = `R$ ${TAXA_ENTREGA.toFixed(2)}`;
            } else {
                linhaTaxaEntrega.style.display = 'none';
            }
        }

        const totalGeral = subtotal + valorFrete;
        cartTotalSpan.textContent = `R$ ${totalGeral.toFixed(2)}`;
    }

    cartList.addEventListener('click', (event) => {
        event.preventDefault(); 
        if (event.target.classList.contains('btn-remove')) {
            const indexToRemove = parseInt(event.target.dataset.index, 10);
            removeFromCart(indexToRemove);
        }
    });

    function removeFromCart(index) {
        cart.splice(index, 1);
        let count = cart.reduce((acc, item) => acc + item.quantidade, 0);
        cartBadge.innerText = count;
        renderCart();
    }

    clearCartBtn.addEventListener('click', () => {
        if (cart.length > 0 && confirm('Esvaziar o carrinho?')) {
            cart = [];
            cartBadge.innerText = '0';
            renderCart();
        }
    });

    if (tipoRetirada) {
        tipoRetirada.addEventListener('change', () => {
            if (tipoRetirada.checked) {
                campoEndereco.style.display = 'none';
                renderCart();
            }
        });
    }

    if (tipoEntrega) {
        tipoEntrega.addEventListener('change', () => {
            if (tipoEntrega.checked) {
                campoEndereco.style.display = 'block';
                renderCart();
            }
        });
    }

    const formaPagamento = document.getElementById('forma_pagamento');
    const campoTroco = document.getElementById('campo_troco');
    
    if (formaPagamento) {
        formaPagamento.addEventListener('change', () => {
            if (formaPagamento.value === 'DINHEIRO') {
                campoTroco.style.display = 'block';
            } else {
                campoTroco.style.display = 'none';
            }
        });
    }

    function gerarTextoWhatsApp(pedidoId, dados, itens, subtotal, taxaEntrega) {
        let texto = `*NOVO PEDIDO #${pedidoId}*\n`;
        texto += `*Cliente:* ${dados.nome_cliente}\n`;
        texto += `*Telefone:* ${dados.telefone_cliente}\n`;
        texto += `*Tipo:* ${dados.tipo_pedido}\n`;
        
        if (dados.tipo_pedido === 'ENTREGA') {
            texto += `*Endereço:* ${dados.endereco_cliente}\n`;
        }
        
        texto += `*Pagamento:* ${dados.forma_pagamento}\n`;
        if (dados.forma_pagamento === 'DINHEIRO' && dados.troco_para) {
            texto += `*Troco para:* ${dados.troco_para}\n`;
        }

        if (dados.observacoes && dados.observacoes.trim() !== '') {
            texto += `\n*OBSERVAÇÕES:* ${dados.observacoes.trim()}\n`;
        }

        texto += `\n*ITENS DO PEDIDO:*\n`;
        itens.forEach(item => {
            texto += `• ${item.quantidade}x ${item.pratoNome} (${item.tamanhoNome}) - R$ ${(item.preco * item.quantidade).toFixed(2)}\n`;
        });

        if (dados.tipo_pedido === 'ENTREGA' && taxaEntrega > 0) {
            texto += `\n*Taxa de Entrega:* R$ ${taxaEntrega.toFixed(2)}\n`;
        }

        const totalFinal = subtotal + (dados.tipo_pedido === 'ENTREGA' ? taxaEntrega : 0);
        texto += `\n*TOTAL A PAGAR: R$ ${totalFinal.toFixed(2)}*\n`;
        
        return encodeURIComponent(texto);
    }

    if (formPedido) {
        formPedido.addEventListener('submit', (event) => {
            event.preventDefault(); 

            if (!LOJA_ABERTA) {
                alert('A lanchonete está fechada para novos pedidos no momento.');
                return;
            }
            
            if (cart.length === 0) {
                alert('Adicione itens ao carrinho antes de finalizar.');
                return;
            }

            btnFinalizar.disabled = true;
            btnFinalizar.textContent = 'Processando...';

            const formData = new FormData(formPedido);
            const dadosPedido = Object.fromEntries(formData.entries());
            
            const payload = {
                pedido: dadosPedido,
                carrinho: cart
            };

            const headers = {
                'Content-Type': 'application/json'
            };
            if (CSRF_TOKEN) {
                headers['X-CSRFToken'] = CSRF_TOKEN;
            }

            fetch('/api/finalizar_pedido', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let subtotal = cart.reduce((acc, item) => acc + (item.preco * item.quantidade), 0);
                    let taxaAplicada = dadosPedido.tipo_pedido === 'ENTREGA' ? TAXA_ENTREGA : 0;
                    
                    modalPedidoId.innerText = data.pedido_id;
                    
                    const textoWs = gerarTextoWhatsApp(data.pedido_id, dadosPedido, cart, subtotal, taxaAplicada);
                    btnWhatsapp.href = `https://api.whatsapp.com/send?phone=${RESTAURANTE_WHATSAPP}&text=${textoWs}`;
                    
                    modalOverlay.style.display = 'flex';
                    
                    cart = [];
                    cartBadge.innerText = '0';
                    renderCart();
                    formPedido.reset();
                    campoEndereco.style.display = 'none';
                    campoTroco.style.display = 'none';
                    if (tipoRetirada) tipoRetirada.checked = true;
                } else {
                    alert('Erro ao finalizar pedido: ' + data.message);
                }
                btnFinalizar.disabled = false;
                btnFinalizar.textContent = 'Finalizar Pedido';
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                alert('Falha na comunicação com o servidor. Verifique sua conexão e tente novamente.');
                btnFinalizar.disabled = false;
                btnFinalizar.textContent = 'Finalizar Pedido';
            });
        });
    }

    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', () => {
            modalOverlay.style.display = 'none';
        });
    }
});