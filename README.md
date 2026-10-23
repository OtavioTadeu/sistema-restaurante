# 🌭 Sistema de Gestão e Cardápio Digital - Dogão do Castelo

Sistema completo de delivery, cardápio digital e gestão de pedidos (POS) desenvolvido em **Python (Flask)** sob medida para a lanchonete **Dogão do Castelo**.

O sistema foi preparado para operar em **arquitetura híbrida moderna**:
* **Servidor e Banco de Dados na Nuvem (24/7):** O cliente acessa de casa pelo celular através do domínio próprio sem sobrecarregar a máquina do restaurante.
* **Agente de Impressão no Balcão:** Um script leve roda no Windows da lanchonete, consome os novos pedidos da nuvem e comanda a impressora térmica física automaticamente via USB/Spooler.

---

## ✨ Principais Funcionalidades

### 1. Área do Cliente e Cardápio Digital 📱
* **Cadastro & Login:** Identificação rápida pelo número de WhatsApp.
* **Carrinho Inteligente:** Cálculo instantâneo do subtotal e taxa de entrega dinâmica.
* **Campo de Observações:** Clientes podem especificar detalhes (ex: *"Sem cebola, interfone 302, caprichar na batata"*).
* **Controle de Loja Aberta/Fechada:** Banner automático quando o restaurante estiver fechado, impedindo fechamento de novos pedidos.
* **Finalização com WhatsApp:** Geração de link formatado com 1 clique para envio do resumo do pedido diretamente ao WhatsApp da loja.

### 2. Painel Administrativo em Tempo Real (`/admin`) 🔒
* **Segurança de Acesso:** Proteção CSRF em todos os formulários e **troca obrigatória da senha padrão no primeiro acesso**.
* **Gestão de Pedidos em Tempo Real:** Atualização automática a cada 10 segundos sem necessidade de dar F5.
* **Alerta Sonoro com Botão Mute:** Notificação sonora agradável quando chega novo pedido, podendo ser ativado (🔊) ou mutado (🔇) pelo operador.
* **Controle Operacional:** Alternar status da loja (Aberta / Fechada), definir taxa de entrega padrão e alterar o WhatsApp de atendimento.
* **Gestão de Cardápio e Fotos:** Cadastro de pratos e tamanhos com suporte a upload de fotos com otimização automática via **Cloudinary**.

### 3. Agente de Impressão Local (Nuvem ➔ Balcão) 🖨️
* Script [`agente_impressao.py`](file:///c:/Users/Tadeu/Documents/Projetos/sistema-restaurante/agente_impressao.py) que roda na máquina do caixa/cozinha.
* Autenticado por token seguro (`X-Printer-Token`), garantindo que apenas a sua impressora receba os pedidos.
* Inicialização com **1 clique** pelo arquivo [`iniciar_impressor_balcao.bat`](file:///c:/Users/Tadeu/Documents/Projetos/sistema-restaurante/iniciar_impressor_balcao.bat).

---

## 🛠️ Configuração e Variáveis de Ambiente (`.env`)

Crie o arquivo `.env` a partir do modelo [`.env.example`](file:///c:/Users/Tadeu/Documents/Projetos/sistema-restaurante/.env.example):

```ini
# Chave Secreta da Sessão
SECRET_KEY=sua-chave-secreta-forte

# Banco de Dados
# Desenvolvimento local (SQLite):
DATABASE_URL=sqlite:///restaurante.db
# Produção na Nuvem (PostgreSQL):
# DATABASE_URL=postgresql://usuario:senha@host:5432/nome_banco

# WhatsApp da Lanchonete (apenas dígitos)
RESTAURANTE_WHATSAPP=553194585341

# Token do Agente de Impressão
PRINTER_TOKEN=seu-token-secreto-de-impressao

# Cloudinary (Upload gratuito de fotos dos pratos)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

---

## 🚀 Como Executar Localmente

### 1. Criar o Ambiente Virtual e Instalar Dependências
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Iniciar o Servidor Flask
```bash
python app.py
```
* Cardápio do Cliente: `http://localhost:5000/cardapio`
* Painel Administrativo: `http://localhost:5000/admin` *(Senha padrão inicial: `admin123`)*

### 3. Iniciar o Agente de Impressão na Loja
Basta dar duplo clique em:
👉 **`iniciar_impressor_balcao.bat`**

---

## ☁️ Preparação para Deploy na Nuvem (Render / Railway / VPS)

O projeto já conta com o arquivo [`Procfile`](file:///c:/Users/Tadeu/Documents/Projetos/sistema-restaurante/Procfile) configurado para rodar com o servidor WSGI de produção **Gunicorn**:
```bash
web: gunicorn app:app -w 4 -b 0.0.0.0:$PORT
```
Basta conectar o repositório Git no **Render.com** ou **Railway.app**, adicionar as variáveis de ambiente do `.env` e adicionar um banco **PostgreSQL gerenciado**.