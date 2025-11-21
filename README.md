# 🌭 Sistema de Pedidos - Dogão do Castelo

Sistema de gestão de pedidos (POS) e cardápio digital desenvolvido sob medida para a lanchonete **Dogão do Castelo**. O projeto moderniza o atendimento, permitindo pedidos via interface web e automação da impressão de comandas na cozinha.

---

## ✨ Funcionalidades (Versão 1.0)

O sistema opera com uma arquitetura de **Fila de Impressão**, garantindo robustez mesmo se a impressora falhar ou estiver sem papel.

### 1. Interface do Cliente (Cardápio Digital)
* **Design Personalizado:** Tema "Dark Mode" com as cores da marca (Preto e Dourado).
* **Cardápio Dinâmico:** Exibe apenas os itens disponíveis no dia.
* **Carrinho Interativo:** Adicionar, remover e ajustar quantidades com atualização de preço em tempo real.
* **Checkout Inteligente:** Formulário que se adapta para "Retirada" ou "Entrega".

### 2. Painel Administrativo (`/admin`)
* **Gestão Total:** Adicionar/Editar/Remover pratos e tamanhos de preços.
* **Controle Diário:** Montar o "Cardápio do Dia" e marcar itens como esgotados em tempo real.
* **Painel de Pedidos:** Visualização dos pedidos recebidos.

### 3. Sistema de Impressão (Backend)
* **Fila de Arquivos:** O sistema salva os pedidos como arquivos `.txt` numa pasta segura.
* **Script Vigia (`impressor.py`):** Um robô que monitora a pasta e envia automaticamente novos pedidos para a impressora padrão do Windows, movendo-os para "Concluídos" após o sucesso.

---

## 🛠️ Tecnologias