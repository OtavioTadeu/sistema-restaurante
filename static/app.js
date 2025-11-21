document.addEventListener('DOMContentLoaded', () => {

    const addButtons = document.querySelectorAll('.btn-add-item');
    const cartList = document.getElementById('lista-carrinho');
    const cartTotalSpan = document.getElementById('total-carrinho');
    const clearCartBtn = document.getElementById('clear-cart-btn');
    
    const formPedido = document.getElementById('form-pedido');
    const btnFinalizar = document.getElementById('btn-finalizar');
    const tipoRetirada = document.getElementById('tipo_retirada');
    const tipoEntrega = document.getElementById('tipo_entrega');
    const campoEndereco = document.getElementById('campo_endereco');

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
        });
    });

    function addToCart(newItem) {
        let itemExists = false;
        for (let item of cart) {
            if (item.pratoId === newItem.pratoId && item.tamanhoId === newItem.tamanhoId) {
                item.quantidade++;
                itemExists = true;
                break;
            }
        }
        if (!itemExists) {
            cart.push(newItem);
        }
        renderCart();
    }

    function renderCart() {
        cartList.innerHTML = '';
        if (cart.length === 0) {
            cartList.innerHTML = '<p style="color: #777;">Seu carrinho está vazio.</p>';
            cartTotalSpan.textContent = 'R$ 0.00';
            return;
        }

        let total = 0;
        cart.forEach((item, index) => {
            const itemTotal = item.preco * item.quantidade;
            total += itemTotal;

            const itemElement = document.createElement('div');
            itemElement.classList.add('carrinho-item');

            itemElement.innerHTML = `
                <strong>${item.pratoNome}</strong> (${item.tamanhoNome})
                <a href="#" class="remove-btn" data-index="${index}" 
                   style="color: var(--cor-perigo); float: right; text-decoration: none;">
                   [X]
                </a>
                <br>
                <span>Qtd: 
                    <a href="#" class="decrement-btn" data-index="${index}" style="color: var(--cor-dourado); text-decoration: none; font-weight: bold;">
                        [-]
                    </a>
                    ${item.quantidade}
                </span>
                <span style="float: right; font-weight: bold; margin-right: 10px;">R$ ${itemTotal.toFixed(2)}</span>
            `;
            cartList.appendChild(itemElement);
        });

        cartTotalSpan.textContent = `R$ ${total.toFixed(2)}`;
    }

    cartList.addEventListener('click', (event) => {
        event.preventDefault(); 

        if (event.target.classList.contains('remove-btn')) {
            const indexToRemove = parseInt(event.target.dataset.index, 10);
            removeFromCart(indexToRemove);
        }
        
        if (event.target.classList.contains('decrement-btn')) {
            const indexToDecrement = parseInt(event.target.dataset.index, 10);
            decrementItem(indexToDecrement);
        }
    });

    function removeFromCart(index) {
        cart.splice(index, 1);
        renderCart();
    }

    function decrementItem(index) {
        let item = cart[index];
        if (item.quantidade > 1) {
            item.quantidade--;
            renderCart();
        } else {
            removeFromCart(index);
        }
    }

    clearCartBtn.addEventListener('click', () => {
        if (cart.length > 0 && confirm('Tem certeza que quer esvaziar o carrinho?')) {
            cart = [];
            renderCart();
        }
    });

    tipoRetirada.addEventListener('click', () => {
        campoEndereco.style.display = 'none';
    });

    tipoEntrega.addEventListener('click', () => {
        campoEndereco.style.display = 'block';
    });

    formPedido.addEventListener('submit', (event) => {
        event.preventDefault(); 
        
        if (cart.length === 0) {
            alert('Seu carrinho está vazio. Adicione pelo menos um item.');
            return;
        }

        btnFinalizar.disabled = true;
        btnFinalizar.textContent = 'Enviando...';

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
                alert(data.message);
                cart = [];
                renderCart();
                formPedido.reset();
                campoEndereco.style.display = 'none';
                document.getElementById('tipo_retirada').checked = true;
            } else {
                alert('Erro ao finalizar pedido: ' + data.message);
            }
            btnFinalizar.disabled = false;
            btnFinalizar.textContent = 'Finalizar Pedido';
        })
        .catch(error => {
            console.error('Erro de rede:', error);
            alert('Não foi possível conectar ao servidor. Tente novamente.');
            btnFinalizar.disabled = false;
            btnFinalizar.textContent = 'Finalizar Pedido';
        });
    });
});