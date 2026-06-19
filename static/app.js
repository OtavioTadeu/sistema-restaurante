document.addEventListener('DOMContentLoaded', () => {

    const addButtons = document.querySelectorAll('.btn-add-item');
    const cartList = document.getElementById('lista-carrinho');
    const cartTotalSpan = document.getElementById('total-carrinho');
    const clearCartBtn = document.getElementById('clear-cart-btn');
    const cartBadge = document.getElementById('cart-badge');
    
    const formPedido = document.getElementById('form-pedido');
    const btnFinalizar = document.getElementById('btn-finalizar');
    const tipoRetirada = document.getElementById('tipo_retirada');
    const tipoEntrega = document.getElementById('tipo_entrega');
    const campoEndereco = document.getElementById('campo_endereco');

    const modalOverlay = document.getElementById('success-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnWhatsapp = document.getElementById('btn-whatsapp');
    const modalPedidoId = document.getElementById('modal-pedido-id');

    // Número do restaurante para WhatsApp (exemplo, deve ser trocado pelo real)
    const RESTAURANTE_WHATSAPP = "5511999999999"; 

    let cart = [];

    addButtons.forEach(button => {
        button.addEventListener('click', () => {
            const item = {
                pratoId: button.dataset.pratoId,
                pratoNome: button.dataset.pratoNome,
                tamanhoId: button.dataset.tamanhoId,
                tamanhoNome: button.dataset.tamanhoNome,
                preco: parseFloat(button.dataset.preco),
                quantidade: 1
            };
            addToCart(item);
            
            // Animação de feedback no botão
            const btnOriginalText = button.innerHTML;
            button.innerHTML = '✓ Adicionado';
            button.style.background = 'var(--success)';
            button.style.color = '#fff';
            button.style.borderColor = 'var(--success)';
            
            setTimeout(() => {
                button.innerHTML = btnOriginalText;
                button.style.background = '';
                button.style.color = '';
                button.style.borderColor = '';
            }, 1000);
            
            // Feedback badge
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
            cartTotalSpan.textContent = 'R$ 0.00';
            cartBadge.innerText = '0';
            return;
        }

        let total = 0;
        let count = 0;
        cart.forEach((item, index) => {
            const itemTotal = item.preco * item.quantidade;
            total += itemTotal;
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
        cartTotalSpan.textContent = `R$ ${total.toFixed(2)}`;
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

    tipoRetirada.addEventListener('change', () => {
        if (tipoRetirada.checked) campoEndereco.style.display = 'none';
    });

    tipoEntrega.addEventListener('change', () => {
        if (tipoEntrega.checked) campoEndereco.style.display = 'block';
    });

    const formaPagamento = document.getElementById('forma_pagamento');
    const campoTroco = document.getElementById('campo_troco');
    
    formaPagamento.addEventListener('change', () => {
        if (formaPagamento.value === 'DINHEIRO') {
            campoTroco.style.display = 'block';
        } else {
            campoTroco.style.display = 'none';
        }
    });

    function gerarTextoWhatsApp(pedidoId, dados, itens, total) {
        let texto = `*NOVO PEDIDO #${pedidoId}*\n`;
        texto += `*Cliente:* ${dados.nome_cliente}\n`;
        texto += `*Tipo:* ${dados.tipo_pedido}\n`;
        if (dados.tipo_pedido === 'ENTREGA') {
            texto += `*Endereço:* ${dados.endereco_cliente}\n`;
        }
        texto += `*Pagamento:* ${dados.forma_pagamento}\n`;
        if (dados.forma_pagamento === 'DINHEIRO' && dados.troco_para) {
            texto += `*Troco para:* ${dados.troco_para}\n`;
        }
        texto += `\n*ITENS:*\n`;
        itens.forEach(item => {
            texto += `${item.quantidade}x ${item.pratoNome} (${item.tamanhoNome}) - R$ ${(item.preco * item.quantidade).toFixed(2)}\n`;
        });
        texto += `\n*TOTAL:* R$ ${total.toFixed(2)}\n`;
        return encodeURIComponent(texto);
    }

    formPedido.addEventListener('submit', (event) => {
        event.preventDefault(); 
        
        if (cart.length === 0) {
            alert('Adicione itens ao carrinho.');
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

        fetch('/api/finalizar_pedido', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let total = cart.reduce((acc, item) => acc + (item.preco * item.quantidade), 0);
                
                modalPedidoId.innerText = data.pedido_id;
                
                const textoWs = gerarTextoWhatsApp(data.pedido_id, dadosPedido, cart, total);
                btnWhatsapp.href = `https://api.whatsapp.com/send?phone=${RESTAURANTE_WHATSAPP}&text=${textoWs}`;
                
                modalOverlay.style.display = 'flex';
                
                cart = [];
                cartBadge.innerText = '0';
                renderCart();
                formPedido.reset();
                campoEndereco.style.display = 'none';
                campoTroco.style.display = 'none';
                document.getElementById('tipo_retirada').checked = true;
            } else {
                alert('Erro ao finalizar pedido: ' + data.message);
            }
            btnFinalizar.disabled = false;
            btnFinalizar.textContent = 'Finalizar Pedido';
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Falha na comunicação.');
            btnFinalizar.disabled = false;
            btnFinalizar.textContent = 'Finalizar Pedido';
        });
    });

    btnCloseModal.addEventListener('click', () => {
        modalOverlay.style.display = 'none';
    });
});