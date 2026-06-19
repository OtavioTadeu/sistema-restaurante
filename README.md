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
Sempre que for abrir a lanchonete, você precisará abrir **dois terminais** na pasta do projeto:

**Terminal 1 (O Servidor do Site):**
Mantenha o sistema rodando.
```bash
.\venv\Scripts\activate
py app.py
```

**Terminal 2 (O Túnel Cloudflare para os Clientes):**
Mantenha este rodando para que os clientes acessem o site pelo celular usando a internet 4G/Wifi da casa deles. Ele vai gerar um link (ex: `https://palavra-aleatoria.trycloudflare.com`)
```bash
.\cloudflared.exe tunnel --url http://localhost:5000
```

*(Opcional) Terminal 3: Se tiver script vigia de impressão automática ativado:*
```bash
py impressor.py
```