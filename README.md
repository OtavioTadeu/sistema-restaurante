# 🌭 Sistema de Pedidos - Dogão do Castelo

Sistema de gestão de pedidos (POS) e cardápio digital moderno e responsivo desenvolvido sob medida para a lanchonete **Dogão do Castelo**. O projeto permite que clientes façam pedidos online (de casa via celular) e automatiza a impressão de comandas diretamente na cozinha.

---

## ✨ Funcionalidades (Versão 2.0)

O sistema foi atualizado para uma arquitetura moderna, segura e com acesso remoto.

### 1. Área do Cliente e Cardápio 📱
* **Contas de Clientes:** Sistema completo de cadastro e login de clientes usando o número do WhatsApp como identificador.
* **Minha Conta:** Painel exclusivo onde o cliente visualiza seus dados, endereço, preferência de entrega (Retirada/Delivery) e um histórico completo de pedidos passados.
* **Checkout Automático:** Clientes logados têm seus dados de endereço e telefone pré-preenchidos automaticamente, acelerando o fechamento do pedido. Visitantes ainda podem comprar normalmente!
* **Múltiplas Formas de Pagamento:** Suporte para escolher a forma de pagamento (Pix, Crédito, Débito e Dinheiro) com cálculo inteligente de troco embutido.
* **Design "Dark Mode":** Experiência visual Premium e imersiva.

### 2. Painel Administrativo Segurado (`/admin`) 🔒
* **Acesso Protegido:** Painel inteiramente protegido por senha (`admin123`).
* **Gestão Total:** Adicionar/Editar/Remover pratos, tamanhos e fotos (upload de imagens nativo).
* **Painel de Pedidos:** Acompanhamento em tempo real, filtros por data (podendo ver o histórico de vendas de dias anteriores), gerenciamento de status (Pendente, Preparando, etc) e reimpressão de tickets manuais.

### 3. Fila de Impressão (Cozinha) 🖨️
* Os pedidos são salvos de forma resiliente na pasta `fila_impressao/`. Se houver falha na internet ou falta de papel, nenhum pedido é perdido e ele entra na fila do Windows nativamente.

---

## 🚀 Guia de Instalação e Execução

Como o sistema opera no próprio computador do restaurante, mas precisa ser acessado da rua pelos clientes, nós utilizamos o **Cloudflare Tunnels**.

### Passo 1: Configuração Inicial
1. Abra o terminal na pasta do projeto.
2. Crie e ative o ambiente virtual:
    ```bash
    py -m venv venv
    .\venv\Scripts\activate
    ```
3. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

### Passo 2: Rodar o Sistema (Obrigatório para o Expediente)

Para abrir a lanchonete e iniciar tudo com **1 único clique**, basta dar duplo clique no arquivo:
👉 **`iniciar_sistema.bat`**

O inicializador abrirá o menu onde você pode escolher:
- **[1] NGROK (Recomendado):** Inicia o servidor, o impressor de comandas e o túnel com o seu **domínio fixo permanente** (ex: `https://homalographic-unbiliously-randall.ngrok-free.dev`), sem alterar o link para os clientes.
- **[2] CLOUDFLARE:** Inicia o túnel direto do Cloudflare (link temporário).
- **[3] Local:** Inicia apenas no computador da loja (`http://localhost:5000`) sem acesso externo.

As 3 janelas necessárias (Servidor Flask, Impressor de Comandas e Túnel) serão abertas automaticamente e organizadas por cores. Mantenha-as abertas durante o expediente!