# 🍽️ Sistema de Pedidos para Restaurante

Este é um sistema de gestão de pedidos (POS) desenvolvido em Python e Flask, focado em pequenos restaurantes que trabalham com o modelo de "Prato do Dia". O projeto foi criado para automatizar a operação de um restaurante familiar, permitindo o cadastro de um cardápio dinâmico e o envio de pedidos para a cozinha.

---

## ✨ Funcionalidades Atuais

O sistema é dividido em duas partes principais:

### 1. Painel de Admin (`/admin`)
Uma interface de gerenciamento onde o dono do restaurante pode:
* **Gerenciar Tamanhos:** CRUD (Criar, Ler, Editar, Excluir) para os tamanhos dos pratos (ex: Pequeno, Grande) e seus preços fixos.
* **Gerenciar Catálogo de Pratos:** CRUD completo para todos os pratos que o restaurante sabe fazer.
* **Montar o Cardápio do Dia:** A função principal. Permite selecionar pratos do catálogo para compor o cardápio de hoje.
* **Controle de Disponibilidade:** Marcar itens do cardápio do dia como "Disponível" ou "Esgotado" em tempo real.
* **Limpar Cardápio:** Um botão para apagar todos os itens do cardápio do dia, facilitando o início de um novo dia.

### 2. Interface do Cliente (`/`)
A tela principal de pedidos com design responsivo (dark mode) para o cliente:
* **Cardápio Dinâmico:** Exibe apenas os itens marcados como "Disponíveis" pelo admin.
* **Carrinho de Compras:** Um carrinho 100% em JavaScript que permite adicionar, remover (unitário ou completo) e limpar itens.
* **Formulário de Checkout:** Coleta os dados do cliente (Nome, Telefone) e se adapta para pedidos de "Entrega" (mostrando o campo de endereço) ou "Retirada".
* **API de Pedidos:** Envia o pedido completo (carrinho + dados do cliente) para o backend Flask, que salva tudo no banco de dados.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python
* **Framework Web:** Flask
* **Banco de Dados:** SQLite
* **ORM:** Flask-SQLAlchemy (para interagir com o banco de dados)
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla) e Templates com Jinja2

---

## 🚀 Próximos Passos (Roadmap)

* [ ] **Impressão de Comandas:** Integrar o backend com uma impressora térmica USB (usando `python-escpos`) para imprimir o pedido automaticamente.
* [ ] **Migrações de Banco:** Implementar o `Flask-Migrate` para gerenciar alterações no banco de dados de forma segura.
* [ ] **Autenticação:** Adicionar um sistema de login e senha para o `/admin`.
* [ ] **Refinamento de Design:** Melhorar o CSS do painel de admin.