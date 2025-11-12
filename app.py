# ... (import os, from flask import Flask, etc.)
# Adicione estas 3 novas importações:
from flask import render_template, request, redirect, url_for
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- Configuração Inicial ---

# Pega o caminho absoluto (a pasta) onde este arquivo app.py está
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configura o Flask para saber onde está nosso banco de dados
# Ele vai criar um arquivo chamado 'restaurante.db' dentro da pasta do projeto
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'restaurante.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desativa alertas desnecessários

# Inicializa a extensão de banco de dados
db = SQLAlchemy(app)

# --- Definição das Nossas 5 Tabelas (Modelos) ---

class Tamanho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: "Pequeno", "Grande"
    preco = db.Column(db.Float, nullable=False) # Ex: 20.00

    def __repr__(self):
        return f'<Tamanho {self.nome}>'

class Prato(db.Model):
    __tablename__ = 'prato' # Nome da tabela no banco
    id = db.Column(db.Integer, primary_key=True)
    nome_prato = db.Column(db.String(100), nullable=False, unique=True) # Ex: "Frango à Parmegiana"
    descricao_base = db.Column(db.String(200)) # Ex: "Arroz, feijão, fritas"
    
    # Relação: Um prato pode estar em muitos cardápios de dias diferentes
    cardapios = db.relationship('CardapioDoDia', back_populates='prato')

    def __repr__(self):
        return f'<Prato {self.nome_prato}>'

class CardapioDoDia(db.Model):
    __tablename__ = 'cardapio_do_dia'
    id = db.Column(db.Integer, primary_key=True)
    descricao_dia = db.Column(db.String(200)) # Descrição específica do dia (ex: "Hoje com purê")
    disponivel = db.Column(db.Boolean, default=True, nullable=False)
    
    # Chave Estrangeira: Liga este cardápio ao prato base
    prato_id = db.Column(db.Integer, db.ForeignKey('prato.id'), nullable=False)
    
    # Relação: Define o "lado de cá" da ligação com o Prato
    prato = db.relationship('Prato', back_populates='cardapios')

    def __repr__(self):
        return f'<CardapioDoDia {self.prato.nome_prato}>'

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefone_cliente = db.Column(db.String(20), nullable=True) # Nulo se for retirada
    tipo_pedido = db.Column(db.String(20), nullable=False) # "ENTREGA" ou "RETIRADA"
    endereco_cliente = db.Column(db.String(200), nullable=True) # Nulo se for retirada
    status_pedido = db.Column(db.String(20), default='PENDENTE') # PENDENTE, IMPRESSO, CONCLUÍDO

    # Relação: Um pedido pode ter vários itens
    itens = db.relationship('ItemPedido', back_populates='pedido')

    def __repr__(self):
        return f'<Pedido {self.id} - {self.nome_cliente}>'

class ItemPedido(db.Model):
    __tablename__ = 'item_pedido'
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    preco_unitario_pago = db.Column(db.Float, nullable=False) # Salvamos o preço no momento da compra
    
    # Chaves Estrangeiras
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    cardapio_id = db.Column(db.Integer, db.ForeignKey('cardapio_do_dia.id'), nullable=False)
    tamanho_id = db.Column(db.Integer, db.ForeignKey('tamanho.id'), nullable=False)

    # Relações
    pedido = db.relationship('Pedido', back_populates='itens')
    cardapio = db.relationship('CardapioDoDia')
    tamanho = db.relationship('Tamanho')

    def __repr__(self):
        return f'<ItemPedido {self.quantidade}x>'

# ... (todas as 5 classes do banco de dados terminam aqui) ...
# --- ROTAS DA APLICAÇÃO (O CÉREBRO) ---

@app.route('/')
def home():
    # Esta é a página principal do cliente (cardápio)
    try:
        # 1. Busca os pratos disponíveis hoje
        cardapio_hoje = CardapioDoDia.query.filter_by(disponivel=True).all()
        
        # 2. Busca todos os tamanhos e seus preços
        tamanhos = Tamanho.query.order_by(Tamanho.preco).all() # Ordena do mais barato ao mais caro
        
    except Exception as e:
        print(f"Erro ao buscar o cardápio principal: {e}")
        cardapio_hoje = []
        tamanhos = []

    # 3. Envia esses dados para um novo template 'index.html'
    return render_template('index.html', 
                           cardapio_hoje=cardapio_hoje, 
                           tamanhos=tamanhos)

@app.route('/admin')
def admin():
    # Esta será a página de admin
    # Vamos buscar todos os tamanhos cadastrados no banco
    try:
        tamanhos = Tamanho.query.all()
    except Exception as e:
        # Se der erro (ex: banco ainda não foi criado), lista vazia
        print(f"Erro ao buscar tamanhos: {e}")
        tamanhos = []
        
    # 'render_template' vai procurar um arquivo chamado 'admin.html'
    return render_template('admin.html', tamanhos=tamanhos)

@app.route('/admin/pratos')
def admin_pratos():
    # Esta é a página para gerenciar o catálogo de pratos
    try:
        pratos = Prato.query.all()
    except Exception as e:
        print(f"Erro ao buscar pratos: {e}")
        pratos = []
        
    return render_template('admin_pratos.html', pratos=pratos)

@app.route('/admin/cardapio')
def admin_cardapio():
    # Esta é a página principal para montar o cardápio do dia
    
    try:
        # 1. Busca todos os pratos do CATÁLOGO para o formulário
        pratos_catalogo = Prato.query.all()
        
        # 2. Busca todos os itens JÁ ADICIONADOS ao cardápio de hoje
        # O .options(db.joinedload(CardapioDoDia.prato)) é um truque de performance
        # para carregar os nomes dos pratos junto, evitando N+1 queries.
        cardapio_hoje = CardapioDoDia.query.options(db.joinedload(CardapioDoDia.prato)).all()
        
    except Exception as e:
        print(f"Erro ao buscar cardápio: {e}")
        pratos_catalogo = []
        cardapio_hoje = []
        
    return render_template('admin_cardapio.html', 
                           pratos_catalogo=pratos_catalogo, 
                           cardapio_hoje=cardapio_hoje)

@app.route('/admin/add_cardapio', methods=['POST'])
def add_cardapio():
    # Rota que adiciona um prato do catálogo ao cardápio do dia
    if request.method == 'POST':
        prato_id = request.form['prato_id']
        descricao_dia = request.form['descricao_dia']

        # Verifica se já não foi adicionado (evita duplicatas)
        existe = CardapioDoDia.query.filter_by(prato_id=prato_id).first()
        
        if not existe:
            # Pega a descrição base do prato original, caso a de hoje esteja vazia
            if not descricao_dia:
                prato = Prato.query.get(prato_id)
                descricao_dia = prato.descricao_base

            novo_item_cardapio = CardapioDoDia(
                prato_id=prato_id,
                descricao_dia=descricao_dia,
                disponivel=True
            )
            
            try:
                db.session.add(novo_item_cardapio)
                db.session.commit()
            except Exception as e:
                print(f"Erro ao adicionar ao cardápio: {e}")
                db.session.rollback()
        else:
            print("Prato já estava no cardápio do dia.")

        return redirect(url_for('admin_cardapio'))

@app.route('/admin/toggle_disponivel/<int:item_id>')
def toggle_disponivel(item_id):
    # Esta rota vai "virar a chave" (True/False) do item
    try:
        item = CardapioDoDia.query.get(item_id)
        if item:
            # Inverte o valor booleano
            item.disponivel = not item.disponivel
            db.session.commit()
        else:
            print(f"Item com id {item_id} não encontrado.")
            
    except Exception as e:
        print(f"Erro ao mudar status: {e}")
        db.session.rollback()

    # Sempre redireciona de volta para a página do cardápio
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/clear_cardapio', methods=['POST'])
def clear_cardapio():
    # Esta rota apaga TODOS os itens do cardápio do dia
    try:
        # Deleta todas as entradas da tabela CardapioDoDia
        db.session.query(CardapioDoDia).delete()
        db.session.commit()
        print("Cardápio do dia limpo com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar cardápio: {e}")
        db.session.rollback()

    # Redireciona de volta para a página do cardápio
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/delete_prato/<int:prato_id>')
def delete_prato(prato_id):
    # Encontra o prato pelo ID e o deleta
    try:
        prato = Prato.query.get(prato_id)
        if prato:
            db.session.delete(prato)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao deletar prato: {e}")
        db.session.rollback()
    
    # Redireciona de volta para a página de pratos
    return redirect(url_for('admin_pratos'))

@app.route('/admin/edit_prato/<int:prato_id>', methods=['GET', 'POST'])
def edit_prato(prato_id):
    # 1. Busca o prato que queremos editar
    prato = Prato.query.get_or_404(prato_id)

    # 2. Se o formulário foi ENVIADO (POST)
    if request.method == 'POST':
        try:
            # Pega os novos dados do formulário
            prato.nome_prato = request.form['nome_prato']
            prato.descricao_base = request.form['descricao_base']
            
            # Salva a alteração
            db.session.commit()
            print(f"Prato {prato.id} atualizado com sucesso.")
            
            # Redireciona de volta para a lista de pratos
            return redirect(url_for('admin_pratos'))
            
        except Exception as e:
            print(f"Erro ao atualizar prato: {e}")
            db.session.rollback()

    # 3. Se foi um clique para CARREGAR a página (GET)
    # Mostra o formulário de edição pré-preenchido
    return render_template('edit_prato.html', prato=prato)

@app.route('/admin/delete_tamanho/<int:tamanho_id>')
def delete_tamanho(tamanho_id):
    # Encontra o tamanho pelo ID e o deleta
    try:
        tamanho = Tamanho.query.get(tamanho_id)
        if tamanho:
            db.session.delete(tamanho)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao deletar tamanho: {e}")
        db.session.rollback()

    # Redireciona de volta para a página principal de admin
    return redirect(url_for('admin'))

@app.route('/admin/edit_tamanho/<int:tamanho_id>', methods=['GET', 'POST'])
def edit_tamanho(tamanho_id):
    # 1. Busca o item que queremos editar no banco de dados
    tamanho = Tamanho.query.get_or_404(tamanho_id)

    # 2. Se o formulário foi ENVIADO (POST)
    if request.method == 'POST':
        try:
            # Pega os novos dados do formulário
            tamanho.nome = request.form['nome']
            tamanho.preco = float(request.form['preco'])
            
            # Salva a alteração no banco
            db.session.commit()
            print(f"Tamanho {tamanho.id} atualizado com sucesso.")
            
            # Redireciona de volta para a página principal
            return redirect(url_for('admin'))
            
        except Exception as e:
            print(f"Erro ao atualizar tamanho: {e}")
            db.session.rollback()

    # 3. Se foi apenas um clique para CARREGAR a página (GET)
    # Mostra o formulário de edição pré-preenchido
    return render_template('edit_tamanho.html', tamanho=tamanho)

@app.route('/admin/remove_cardapio/<int:item_id>')
def remove_cardapio(item_id):
    # Encontra o item do cardápio do dia pelo ID e o deleta
    try:
        item = CardapioDoDia.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao remover item do cardápio: {e}")
        db.session.rollback()

    # Redireciona de volta para a página do cardápio
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/add_prato', methods=['POST'])
def add_prato():
    # Esta rota recebe os dados do formulário de 'admin_pratos.html'
    if request.method == 'POST':
        nome = request.form['nome_prato']
        descricao = request.form['descricao_base']

        novo_prato = Prato(nome_prato=nome, descricao_base=descricao)
        
        try:
            db.session.add(novo_prato)
            db.session.commit()
        except Exception as e:
            # Lida com erros, ex: nome do prato já existe (unique=True)
            print(f"Erro ao salvar prato: {e}")
            db.session.rollback()

        # Redireciona o usuário de volta para a página de pratos
        return redirect(url_for('admin_pratos'))

@app.route('/admin/add_tamanho', methods=['POST'])
def add_tamanho():
    # Esta rota só aceita dados via 'POST' (enviados pelo formulário)
    if request.method == 'POST':
        # Pega os dados do formulário
        nome_tamanho = request.form['nome']
        preco_tamanho = request.form['preco']

        # Cria um novo objeto 'Tamanho'
        novo_tamanho = Tamanho(nome=nome_tamanho, preco=float(preco_tamanho))
        
        # Salva no banco de dados
        try:
            db.session.add(novo_tamanho)
            db.session.commit()
        except Exception as e:
            print(f"Erro ao salvar tamanho: {e}")
            db.session.rollback() # Desfaz a tentativa

        # Redireciona o usuário de volta para a página /admin
        return redirect(url_for('admin'))

# --- Comando para RODAR o servidor ---

if __name__ == '__main__':
    # Este 'with' é importante para garantir que o SQLAlchemy
    # funcione corretamente com o Flask
    with app.app_context():
        # Vamos garantir que as tabelas existam (não apaga dados existentes)
        db.create_all() 
        
    # Roda o servidor web do Flask
    # debug=True faz o servidor reiniciar sozinho quando você salvar o arquivo
    app.run(debug=True, port=5000)