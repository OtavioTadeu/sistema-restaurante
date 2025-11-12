// Espera o HTML inteiro ser carregado antes de rodar o script
document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Selecionando os Elementos ---
    // Pega todos os botões de "Adicionar"
    const addButtons = document.querySelectorAll('.add-btn');

    // Pega a div onde os itens do carrinho vão aparecer
    const cartList = document.getElementById('lista-carrinho');

    // Pega o span onde o total será exibido
    const cartTotalSpan = document.getElementById('total-carrinho');

    const clearCartBtn = document.getElementById('clear-cart-btn');

    // --- 2. O Carrinho (Onde guardamos os dados) ---
    // Vamos usar um array para guardar os itens do pedido
    let cart = [];

    // --- 3. A Lógica Principal ---

    // Para cada botão de "Adicionar", vamos "ouvir" um clique
    addButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Quando o botão é clicado, pegamos os dados dele
            // (que colocamos nos atributos 'data-...')
            const item = {
                pratoId: button.dataset.pratoId,
                pratoNome: button.dataset.pratoNome,
                tamanhoId: button.dataset.tamanhoId,
                tamanhoNome: button.dataset.tamanhoNome,
                preco: parseFloat(button.dataset.preco),
                quantidade: 1 // Começa com quantidade 1
            };

            // Adiciona o item ao nosso array 'cart'
            addToCart(item);
        });
    });

    /**
     * Adiciona um item ao carrinho ou incrementa a quantidade
     */
    function addToCart(newItem) {
        // Verifica se o item (mesmo prato, mesmo tamanho) JÁ ESTÁ no carrinho
        let itemExists = false;
        for (let item of cart) {
            if (item.pratoId === newItem.pratoId && item.tamanhoId === newItem.tamanhoId) {
                // Se sim, apenas aumenta a quantidade
                item.quantidade++;
                itemExists = true;
                break;
            }
        }

        // Se não existe, adiciona o novo item ao array
        if (!itemExists) {
            cart.push(newItem);
        }

        // Atualiza a tela do carrinho
        renderCart();
    }

    /**
     * "Desenha" o carrinho na tela e calcula o total
     */
    function renderCart() {
        // ... (o início é o mesmo) ...
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
            
            // ATUALIZADO: Agora com o botão [-]
            itemElement.innerHTML = `
                <strong>${item.pratoNome}</strong> (${item.tamanhoNome})
                
                <a href="#" class="remove-btn" data-index="${index}" 
                   style="color: red; float: right; text-decoration: none;">
                   [X]
                </a>
                
                <br>
                
                <span>Qtd: 
                    <a href="#" class="decrement-btn" data-index="${index}" style="color: #007bff; text-decoration: none; font-weight: bold;">
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

    // --- 4. Lógica do Formulário de Checkout ---

    // Seleciona os elementos do formulário
    const tipoRetirada = document.getElementById('tipo_retirada');
    const tipoEntrega = document.getElementById('tipo_entrega');
    const campoEndereco = document.getElementById('campo_endereco');

    // "Ouve" por cliques nos botões de rádio
    tipoRetirada.addEventListener('click', () => {
        campoEndereco.style.display = 'none'; // Esconde o endereço
    });

    tipoEntrega.addEventListener('click', () => {
        campoEndereco.style.display = 'block'; // Mostra o endereço
    });

    // (O código para ENVIAR o formulário virá no próximo passo)

    // --- 5. Lógica de Modificação do Carrinho ---

    // "Ouvinte" principal para os botões [X] e [-]
    cartList.addEventListener('click', (event) => {
        event.preventDefault(); // Impede o link <a> de pular a página
        
        // Se clicou no [X]
        if (event.target.classList.contains('remove-btn')) {
            const indexToRemove = parseInt(event.target.dataset.index, 10);
            removeFromCart(indexToRemove);
        }
        
        // NOVO: Se clicou no [-]
        if (event.target.classList.contains('decrement-btn')) {
            const indexToDecrement = parseInt(event.target.dataset.index, 10);
            decrementItem(indexToDecrement);
        }
    });

    /**
     * Remove um item do array 'cart' usando seu índice
     */
    function removeFromCart(index) {
        cart.splice(index, 1);
        renderCart();
    }

    /**
     * NOVO: Diminui a quantidade de um item
     */
    function decrementItem(index) {
        let item = cart[index];
        
        if (item.quantidade > 1) {
            // Se a quantidade é > 1, apenas diminui
            item.quantidade--;
            renderCart();
        } else {
            // Se a quantidade é 1, remover o item é a mesma coisa
            removeFromCart(index);
        }
    }

    // --- 6. Lógica Limpar Carrinho ---
    
    // NOVO: Ouvinte para o botão "Limpar Carrinho"
    clearCartBtn.addEventListener('click', () => {
        // Pede confirmação, pois é uma ação destrutiva
        if (confirm('Tem certeza que quer esvaziar o carrinho?')) {
            cart = []; // Esvazia o array
            renderCart(); // "Redesenha" o carrinho (que mostrará "vazio")
        }
    });

    // --- 7. Lógica do Formulário de Checkout ---
    // (O código dos botões de rádio "Entrega" e "Retirada" continua aqui)

    /**
     * Remove um item do array 'cart' usando seu índice
     */
    function removeFromCart(index) {
        // 'splice' remove 1 item na posição 'index'
        cart.splice(index, 1);

        // "Redesenha" o carrinho com o item a menos
        renderCart();
    }
});