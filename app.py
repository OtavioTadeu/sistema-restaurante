import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- Configuração Inicial ---

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'restaurante.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Definição das Tabelas (Modelos) ---

class Tamanho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    preco = db.Column(db.Float, nullable=False)

class Prato(db.Model):
    __tablename__ = 'prato'
    id = db.Column(db.Integer, primary_key=True)
    nome_prato = db.Column(db.String(100), nullable=False, unique=True)
    descricao_base = db.Column(db.String(200))
    cardapios = db.relationship('CardapioDoDia', back_populates='prato')

class CardapioDoDia(db.Model):
    __tablename__ = 'cardapio_do_dia'
    id = db.Column(db.Integer, primary_key=True)
    descricao_dia = db.Column(db.String(200))
    disponivel = db.Column(db.Boolean, default=True, nullable=False)
    prato_id = db.Column(db.Integer, db.ForeignKey('prato.id'), nullable=False)
    prato = db.relationship('Prato', back_populates='cardapios')

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.now)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefone_cliente = db.Column(db.String(20), nullable=True)
    tipo_pedido = db.Column(db.String(20), nullable=False)
    endereco_cliente = db.Column(db.String(200), nullable=True)
    status_pedido = db.Column(db.String(20), default='PENDENTE')
    itens = db.relationship('ItemPedido', back_populates='pedido')

class ItemPedido(db.Model):
    __tablename__ = 'item_pedido'
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    preco_unitario_pago = db.Column(db.Float, nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    cardapio_id = db.Column(db.Integer, db.ForeignKey('cardapio_do_dia.id'), nullable=False)
    tamanho_id = db.Column(db.Integer, db.ForeignKey('tamanho.id'), nullable=False)
    pedido = db.relationship('Pedido', back_populates='itens')
    cardapio = db.relationship('CardapioDoDia')
    tamanho = db.relationship('Tamanho')

# --- ROTAS DE ADMINISTRAÇÃO ---

@app.route('/admin')
def admin():
    try:
        tamanhos = Tamanho.query.all()
    except:
        tamanhos = []
    return render_template('admin.html', tamanhos=tamanhos)

@app.route('/admin/pratos')
def admin_pratos():
    try:
        pratos = Prato.query.all()
    except:
        pratos = []
    return render_template('admin_pratos.html', pratos=pratos)

@app.route('/admin/cardapio')
def admin_cardapio():
    try:
        pratos_catalogo = Prato.query.all()
        cardapio_hoje = CardapioDoDia.query.options(db.joinedload(CardapioDoDia.prato)).all()
    except:
        pratos_catalogo = []
        cardapio_hoje = []
    return render_template('admin_cardapio.html', pratos_catalogo=pratos_catalogo, cardapio_hoje=cardapio_hoje)

# --- Rotas de Ação do Admin (Adicionar/Remover/Editar) ---

@app.route('/admin/add_tamanho', methods=['POST'])
def add_tamanho():
    if request.method == 'POST':
        try:
            novo_tamanho = Tamanho(nome=request.form['nome'], preco=float(request.form['preco']))
            db.session.add(novo_tamanho)
            db.session.commit()
        except:
            db.session.rollback()
        return redirect(url_for('admin'))

@app.route('/admin/delete_tamanho/<int:tamanho_id>')
def delete_tamanho(tamanho_id):
    try:
        tamanho = Tamanho.query.get(tamanho_id)
        if tamanho:
            db.session.delete(tamanho)
            db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('admin'))

@app.route('/admin/edit_tamanho/<int:tamanho_id>', methods=['GET', 'POST'])
def edit_tamanho(tamanho_id):
    tamanho = Tamanho.query.get_or_404(tamanho_id)
    if request.method == 'POST':
        try:
            tamanho.nome = request.form['nome']
            tamanho.preco = float(request.form['preco'])
            db.session.commit()
            return redirect(url_for('admin'))
        except:
            db.session.rollback()
    return render_template('edit_tamanho.html', tamanho=tamanho)

@app.route('/admin/add_prato', methods=['POST'])
def add_prato():
    if request.method == 'POST':
        try:
            novo_prato = Prato(nome_prato=request.form['nome_prato'], descricao_base=request.form['descricao_base'])
            db.session.add(novo_prato)
            db.session.commit()
        except:
            db.session.rollback()
        return redirect(url_for('admin_pratos'))

@app.route('/admin/delete_prato/<int:prato_id>')
def delete_prato(prato_id):
    try:
        prato = Prato.query.get(prato_id)
        if prato:
            db.session.delete(prato)
            db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('admin_pratos'))

@app.route('/admin/edit_prato/<int:prato_id>', methods=['GET', 'POST'])
def edit_prato(prato_id):
    prato = Prato.query.get_or_404(prato_id)
    if request.method == 'POST':
        try:
            prato.nome_prato = request.form['nome_prato']
            prato.descricao_base = request.form['descricao_base']
            db.session.commit()
            return redirect(url_for('admin_pratos'))
        except:
            db.session.rollback()
    return render_template('edit_prato.html', prato=prato)

@app.route('/admin/add_cardapio', methods=['POST'])
def add_cardapio():
    if request.method == 'POST':
        prato_id = request.form['prato_id']
        descricao_dia = request.form['descricao_dia']
        existe = CardapioDoDia.query.filter_by(prato_id=prato_id).first()
        if not existe:
            if not descricao_dia:
                prato = Prato.query.get(prato_id)
                descricao_dia = prato.descricao_base
            try:
                novo_item = CardapioDoDia(prato_id=prato_id, descricao_dia=descricao_dia)
                db.session.add(novo_item)
                db.session.commit()
            except:
                db.session.rollback()
        return redirect(url_for('admin_cardapio'))

@app.route('/admin/toggle_disponivel/<int:item_id>')
def toggle_disponivel(item_id):
    try:
        item = CardapioDoDia.query.get(item_id)
        if item:
            item.disponivel = not item.disponivel
            db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/remove_cardapio/<int:item_id>')
def remove_cardapio(item_id):
    try:
        item = CardapioDoDia.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/clear_cardapio', methods=['POST'])
def clear_cardapio():
    try:
        db.session.query(CardapioDoDia).delete()
        db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('admin_cardapio'))

# --- ROTA DA LOJA (CLIENTE) ---

@app.route('/')
def home():
    try:
        cardapio_hoje = CardapioDoDia.query.filter_by(disponivel=True).all()
        tamanhos = Tamanho.query.order_by(Tamanho.preco).all()
    except:
        cardapio_hoje = []
        tamanhos = []
    return render_template('index.html', cardapio_hoje=cardapio_hoje, tamanhos=tamanhos)

# --- FUNÇÃO HELPER: SALVAR ARQUIVO (FILA DE IMPRESSÃO) ---

def salvar_arquivo_cupom(pedido, itens):
    """
    Gera o texto do cupom e salva num arquivo .txt na pasta 'fila_impressao'.
    """
    try:
        # Cria a pasta se não existir
        pasta_fila = os.path.join(basedir, 'fila_impressao')
        if not os.path.exists(pasta_fila):
            os.makedirs(pasta_fila)

        nome_arquivo = f"pedido_{pedido.id}.txt"
        caminho_completo = os.path.join(pasta_fila, nome_arquivo)

        with open(caminho_completo, 'w', encoding='utf-8') as f:
            # --- Cabeçalho ---
            f.write("DOGAO DO CASTELO\n")
            f.write("-" * 32 + "\n")
            f.write(f"PEDIDO #{pedido.id}\n")
            f.write(f"Cliente: {pedido.nome_cliente}\n")
            f.write(f"Telefone: {pedido.telefone_cliente}\n")
            f.write("\n")

            if pedido.tipo_pedido == 'ENTREGA':
                f.write(">>> PARA ENTREGA <<<\n")
                f.write(f"{pedido.endereco_cliente}\n")
            else:
                f.write(">>> PARA RETIRADA <<<\n")

            f.write("-" * 32 + "\n")
            f.write("QTD  ITEM (TAM)               VALOR\n")

            # --- Itens ---
            total_pedido = 0
            for item in itens:
                nome_prato = item['pratoNome']
                nome_tamanho = item['tamanhoNome']
                qtd = int(item['quantidade'])
                preco_unit = float(item['preco'])
                preco_total_item = qtd * preco_unit
                total_pedido += preco_total_item

                # Formata a linha
                linha_item = f"{qtd}x {nome_prato} ({nome_tamanho})"
                linha_preco = f"R$ {preco_total_item:.2f}"

                # Trunca se for muito longo
                if len(linha_item) > 24:
                    linha_item = linha_item[:24]

                # Calcula espaços para alinhar à direita
                espacos = 32 - len(linha_item) - len(linha_preco)
                if espacos < 0: espacos = 0

                f.write(linha_item + (" " * espacos) + linha_preco + "\n")

            f.write("-" * 32 + "\n")
            
            # --- Total e Rodapé ---
            texto_total = f"TOTAL: R$ {total_pedido:.2f}"
            espacos_total = 32 - len(texto_total)
            f.write((" " * espacos_total) + texto_total + "\n")
            
            f.write("\n")
            f.write(f"{pedido.data_hora.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("\n\n\n") # Espaço extra para o corte

        print(f"--- SUCESSO: Arquivo {nome_arquivo} salvo na fila de impressão.")

    except Exception as e:
        print(f"!!! ERRO AO SALVAR ARQUIVO DE IMPRESSÃO: {e}")

# --- ROTA DA API (RECEBE O PEDIDO) ---

@app.route('/api/finalizar_pedido', methods=['POST'])
def api_finalizar_pedido():
    if not request.is_json:
        return jsonify({"success": False, "message": "Erro: Formato inválido."}), 400

    data = request.get_json()
    dados_pedido = data.get('pedido')
    itens_carrinho = data.get('carrinho')

    if not dados_pedido or not itens_carrinho:
        return jsonify({"success": False, "message": "Dados incompletos."}), 400

    try:
        # 1. Salva o Pedido
        novo_pedido = Pedido(
            nome_cliente=dados_pedido['nome_cliente'],
            telefone_cliente=dados_pedido['telefone_cliente'],
            tipo_pedido=dados_pedido['tipo_pedido'],
            endereco_cliente=dados_pedido.get('endereco_cliente'),
            status_pedido='PENDENTE'
        )
        db.session.add(novo_pedido)
        db.session.flush() # Garante o ID

        # 2. Salva os Itens
        for item in itens_carrinho:
            novo_item = ItemPedido(
                pedido_id=novo_pedido.id,
                cardapio_id=int(item['pratoId']),
                tamanho_id=int(item['tamanhoId']),
                quantidade=int(item['quantidade']),
                preco_unitario_pago=float(item['preco'])
            )
            db.session.add(novo_item)
        
        db.session.commit()
        
        # 3. GERA O ARQUIVO PARA A FILA DE IMPRESSÃO
        salvar_arquivo_cupom(novo_pedido, itens_carrinho)

        return jsonify({
            "success": True, 
            "message": f"Pedido #{novo_pedido.id} recebido!",
            "pedido_id": novo_pedido.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro interno: {e}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)