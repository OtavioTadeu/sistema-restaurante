# 🍽️ Sistema de Pedidos para Restaurante

Este é um sistema de gestão de pedidos (POS) desenvolvido em Python e Flask, focado em pequenos restaurantes que trabalham com o modelo de "Prato do Dia". O projeto foi criado para automatizar a operação de um restaurante familiar, permitindo o cadastro de um cardápio dinâmico e (futuramente) o envio de pedidos para uma impressora na cozinha.

---

## ✨ Funcionalidades Atuais

O sistema é dividido em duas partes principais: o Painel de Admin e a (futura) Interface do Cliente.

### Painel de Admin (`/admin`)
Uma interface de gerenciamento protegida (atualmente) pela obscuridade, onde o dono do restaurante pode:
* **Gerenciar Tamanhos:** CRUD (Criar, Ler, Editar, Excluir) para os tamanhos dos pratos (ex: Pequeno, Grande) e seus preços fixos.
* **Gerenciar Catálogo de Pratos:** CRUD completo para todos os pratos que o restaurante sabe fazer.
* **Montar o Cardápio do Dia:** A função principal. Permite selecionar pratos do catálogo para compor o cardápio de hoje.
* **Controle de Disponibilidade:** Marcar itens do cardápio do dia como "Disponível" ou "Esgotado" em tempo real.
* **Limpar Cardápio:** Um botão para apagar todos os itens do cardápio do dia, facilitando o início de um novo dia.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python
* **Framework Web:** Flask
* **Banco de Dados:** SQLite
* **ORM:** Flask-SQLAlchemy (para interagir com o banco de dados)
* **Frontend:** HTML5, CSS3 e Templates com Jinja2

---

## 🚀 Próximos Passos (Roadmap)

* [ ] **Interface do Cliente:** Desenvolver a tela principal onde os clientes farão os pedidos.
* [ ] **Impressão de Comandas:** Integrar o backend com uma impressora térmica USB (provavelmente usando `python-escpos`).
* [ ] **Migrações de Banco:** Implementar o `Flask-Migrate` para gerenciar alterações no banco de dados de forma segura.
* [ ] **Autenticação:** Adicionar um sistema de login e senha para o `/admin`.