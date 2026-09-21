import os
import json
import secrets
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(basedir, 'config.json')

# --- Configuração ---

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

app = Flask(__name__)

# Carregar ou inicializar config
config_data = load_config()

# Gerar SECRET_KEY segura se não existir
if 'secret_key' not in config_data:
    config_data['secret_key'] = secrets.token_hex(32)
    save_config(config_data)

# Migrar senha em texto puro para hash (retrocompatibilidade)
if 'admin_password' in config_data:
    plain_pw = config_data.pop('admin_password')
    config_data['admin_password_hash'] = generate_password_hash(plain_pw)
    save_config(config_data)

# Garantir que existe uma senha de admin hasheada
if 'admin_password_hash' not in config_data:
    config_data['admin_password_hash'] = generate_password_hash('admin123')
    save_config(config_data)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'restaurante.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = config_data['secret_key']
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_admin_password_hash():
    cfg = load_config()
    return cfg.get('admin_password_hash', '')

def set_admin_password(new_password):
    cfg = load_config()
    cfg['admin_password_hash'] = generate_password_hash(new_password)
    save_config(cfg)

def check_admin_password(password):
    return check_password_hash(get_admin_password_hash(), password)

db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            return redirect(url_for('cliente_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Models ---

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    telefone = db.Column(db.String(20), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    endereco_padrao = db.Column(db.String(200), nullable=True)
    preferencia_entrega = db.Column(db.String(20), default='RETIRADA')
    pedidos = db.relationship('Pedido', back_populates='cliente')

class Tamanho(db.Model):
    __tablename__ = 'tamanho'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    preco = db.Column(db.Float, nullable=False)

class Prato(db.Model):
    __tablename__ = 'prato'
    id = db.Column(db.Integer, primary_key=True)
    nome_prato = db.Column(db.String(100), nullable=False, unique=True)
    descricao_base = db.Column(db.String(200))
    foto_url = db.Column(db.String(500))
    cardapios = db.relationship('CardapioDoDia', back_populates='prato')

class CardapioDoDia(db.Model):
    __tablename__ = 'cardapio_do_dia'
    id = db.Column(db.Integer, primary_key=True)
    descricao_dia = db.Column(db.String(200))
    disponivel = db.Column(db.Boolean, default=True, nullable=False)
    prato_id = db.Column(db.Integer, db.ForeignKey('prato.id'), nullable=False)
    prato = db.relationship('Prato', back_populates='cardapios')

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.now)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefone_cliente = db.Column(db.String(20), nullable=True)
    tipo_pedido = db.Column(db.String(20), nullable=False)
    endereco_cliente = db.Column(db.String(200), nullable=True)
    status_pedido = db.Column(db.String(20), default='PENDENTE')
    forma_pagamento = db.Column(db.String(50), nullable=True)
    troco_para = db.Column(db.String(50), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente = db.relationship('Cliente', back_populates='pedidos')
    itens = db.relationship('ItemPedido', back_populates='pedido')

class ItemPedido(db.Model):
    __tablename__ = 'item_pedido'
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    preco_unitario_pago = db.Column(db.Float, nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    prato_id = db.Column(db.Integer, db.ForeignKey('prato.id'), nullable=False)
    tamanho_id = db.Column(db.Integer, db.ForeignKey('tamanho.id'), nullable=False)
    pedido = db.relationship('Pedido', back_populates='itens')
    prato = db.relationship('Prato')
    tamanho = db.relationship('Tamanho')

# --- Rotas de Autenticação Admin ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if check_admin_password(senha):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Senha incorreta', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/configuracoes', methods=['GET', 'POST'])
@login_required
def admin_configuracoes():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        
        if not check_admin_password(senha_atual):
            flash('A senha atual está incorreta.', 'error')
        elif not nova_senha or len(nova_senha) < 4:
            flash('A nova senha deve ter no mínimo 4 caracteres.', 'error')
        else:
            set_admin_password(nova_senha)
            flash('Senha de administrador alterada com sucesso!', 'success')
            
    return render_template('admin_configuracoes.html')

# --- Rotas de Autenticação Cliente ---

@app.route('/cliente/cadastro', methods=['GET', 'POST'])
def cliente_cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')
        
        # Validações
        if not nome or len(nome) < 2:
            flash('O nome deve ter no mínimo 2 caracteres.', 'error')
            return redirect(url_for('cliente_cadastro'))
        
        telefone_limpo = ''.join(c for c in telefone if c.isdigit())
        if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
            flash('Informe um telefone válido com DDD (10 ou 11 dígitos).', 'error')
            return redirect(url_for('cliente_cadastro'))
        
        if len(senha) < 4:
            flash('A senha deve ter no mínimo 4 caracteres.', 'error')
            return redirect(url_for('cliente_cadastro'))
        
        if Cliente.query.filter_by(telefone=telefone_limpo).first():
            flash('Este telefone já está cadastrado.', 'error')
            return redirect(url_for('cliente_cadastro'))
            
        senha_hash = generate_password_hash(senha)
        novo_cliente = Cliente(nome=nome, telefone=telefone_limpo, senha_hash=senha_hash)
        db.session.add(novo_cliente)
        db.session.commit()
        
        session['cliente_id'] = novo_cliente.id
        session['cliente_nome'] = novo_cliente.nome
        return redirect(url_for('cardapio'))
    return render_template('cliente_cadastro.html')

@app.route('/cliente/login', methods=['GET', 'POST'])
def cliente_login():
    if request.method == 'POST':
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')
        
        telefone_limpo = ''.join(c for c in telefone if c.isdigit())
        cliente = Cliente.query.filter_by(telefone=telefone_limpo).first()
        if cliente and check_password_hash(cliente.senha_hash, senha):
            session['cliente_id'] = cliente.id
            session['cliente_nome'] = cliente.nome
            return redirect(url_for('cardapio'))
        else:
            flash('Telefone ou senha incorretos.', 'error')
    return render_template('cliente_login.html')

@app.route('/cliente/logout')
def cliente_logout():
    session.pop('cliente_id', None)
    session.pop('cliente_nome', None)
    return redirect(url_for('index'))

@app.route('/minha_conta', methods=['GET', 'POST'])
@cliente_required
def minha_conta():
    cliente = Cliente.query.get(session['cliente_id'])
    if request.method == 'POST':
        novo_nome = request.form.get('nome', '').strip()
        novo_telefone = request.form.get('telefone', '').strip()
        novo_telefone_limpo = ''.join(c for c in novo_telefone if c.isdigit())
        
        # Validações
        if not novo_nome or len(novo_nome) < 2:
            flash('O nome deve ter no mínimo 2 caracteres.', 'error')
            return redirect(url_for('minha_conta'))
        
        if len(novo_telefone_limpo) < 10 or len(novo_telefone_limpo) > 11:
            flash('Informe um telefone válido com DDD.', 'error')
            return redirect(url_for('minha_conta'))
        
        # Verificar telefone duplicado
        existente = Cliente.query.filter_by(telefone=novo_telefone_limpo).first()
        if existente and existente.id != cliente.id:
            flash('Este telefone já está cadastrado por outro cliente.', 'error')
            return redirect(url_for('minha_conta'))
        
        cliente.nome = novo_nome
        cliente.telefone = novo_telefone_limpo
        cliente.endereco_padrao = request.form.get('endereco_padrao', '').strip()
        cliente.preferencia_entrega = request.form.get('preferencia_entrega', 'RETIRADA')
        db.session.commit()
        flash('Dados atualizados com sucesso.', 'success')
        session['cliente_nome'] = cliente.nome
        return redirect(url_for('minha_conta'))
        
    pedidos = Pedido.query.filter_by(cliente_id=cliente.id).order_by(Pedido.data_hora.desc()).all()
    return render_template('minha_conta.html', cliente=cliente, pedidos=pedidos)

# --- Rotas Admin ---

@app.route('/admin')
@login_required
def admin():
    try:
        tamanhos = Tamanho.query.all()
    except Exception as e:
        logger.error(f"Erro ao carregar tamanhos: {e}")
        tamanhos = []
    return render_template('admin.html', tamanhos=tamanhos)

@app.route('/admin/pratos')
@login_required
def admin_pratos():
    try:
        pratos = Prato.query.all()
    except Exception as e:
        logger.error(f"Erro ao carregar pratos: {e}")
        pratos = []
    return render_template('admin_pratos.html', pratos=pratos)

@app.route('/admin/cardapio')
@login_required
def admin_cardapio():
    try:
        pratos_catalogo = Prato.query.all()
        cardapio_hoje = CardapioDoDia.query.options(db.joinedload(CardapioDoDia.prato)).all()
    except Exception as e:
        logger.error(f"Erro ao carregar cardápio: {e}")
        pratos_catalogo = []
        cardapio_hoje = []
    return render_template('admin_cardapio.html', pratos_catalogo=pratos_catalogo, cardapio_hoje=cardapio_hoje)

@app.route('/admin/add_tamanho', methods=['POST'])
@login_required
def add_tamanho():
    try:
        novo_tamanho = Tamanho(nome=request.form['nome'], preco=float(request.form['preco']))
        db.session.add(novo_tamanho)
        db.session.commit()
        flash('Tamanho adicionado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar tamanho: {e}")
        flash('Erro ao adicionar tamanho.', 'error')
    return redirect(url_for('admin'))

@app.route('/admin/delete_tamanho/<int:tamanho_id>', methods=['POST'])
@login_required
def delete_tamanho(tamanho_id):
    try:
        tamanho = Tamanho.query.get(tamanho_id)
        if tamanho:
            db.session.delete(tamanho)
            db.session.commit()
            flash('Tamanho excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir tamanho {tamanho_id}: {e}")
        flash('Não é possível excluir este tamanho pois ele já está vinculado a um pedido histórico.', 'error')
    return redirect(url_for('admin'))

@app.route('/admin/edit_tamanho/<int:tamanho_id>', methods=['GET', 'POST'])
@login_required
def edit_tamanho(tamanho_id):
    tamanho = Tamanho.query.get_or_404(tamanho_id)
    if request.method == 'POST':
        try:
            tamanho.nome = request.form['nome']
            tamanho.preco = float(request.form['preco'])
            db.session.commit()
            flash('Tamanho atualizado com sucesso.', 'success')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar tamanho {tamanho_id}: {e}")
            flash('Erro ao atualizar tamanho.', 'error')
    return render_template('edit_tamanho.html', tamanho=tamanho)

@app.route('/admin/add_prato', methods=['POST'])
@login_required
def add_prato():
    try:
        foto_url = request.form.get('foto_url', '')
        foto_arquivo = request.files.get('foto_arquivo')
        if foto_arquivo and foto_arquivo.filename != '':
            filename = secure_filename(foto_arquivo.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            foto_arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto_url = url_for('static', filename='uploads/' + filename)

        novo_prato = Prato(nome_prato=request.form['nome_prato'], descricao_base=request.form['descricao_base'], foto_url=foto_url)
        db.session.add(novo_prato)
        db.session.commit()
        flash('Prato adicionado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar prato: {e}")
        flash('Erro ao adicionar prato.', 'error')
    return redirect(url_for('admin_pratos'))

@app.route('/admin/delete_prato/<int:prato_id>', methods=['POST'])
@login_required
def delete_prato(prato_id):
    try:
        prato = Prato.query.get(prato_id)
        if prato:
            db.session.delete(prato)
            db.session.commit()
            flash('Prato excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir prato {prato_id}: {e}")
        flash('Não é possível excluir este prato pois ele já está no cardápio de hoje ou possui pedidos vinculados.', 'error')
    return redirect(url_for('admin_pratos'))

@app.route('/admin/edit_prato/<int:prato_id>', methods=['GET', 'POST'])
@login_required
def edit_prato(prato_id):
    prato = Prato.query.get_or_404(prato_id)
    if request.method == 'POST':
        try:
            prato.nome_prato = request.form['nome_prato']
            prato.descricao_base = request.form['descricao_base']
            
            nova_foto_url = request.form.get('foto_url', '')
            foto_arquivo = request.files.get('foto_arquivo')
            if foto_arquivo and foto_arquivo.filename != '':
                filename = secure_filename(foto_arquivo.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                foto_arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                nova_foto_url = url_for('static', filename='uploads/' + filename)
            
            if nova_foto_url:
                prato.foto_url = nova_foto_url
                
            db.session.commit()
            flash('Prato atualizado com sucesso.', 'success')
            return redirect(url_for('admin_pratos'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar prato {prato_id}: {e}")
            flash('Erro ao atualizar prato.', 'error')
    return render_template('edit_prato.html', prato=prato)

@app.route('/admin/add_cardapio', methods=['POST'])
@login_required
def add_cardapio():
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
            flash('Prato adicionado ao cardápio.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao adicionar ao cardápio: {e}")
            flash('Erro ao adicionar ao cardápio.', 'error')
    else:
        flash('Este prato já está no cardápio de hoje.', 'error')
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/toggle_disponivel/<int:item_id>', methods=['POST'])
@login_required
def toggle_disponivel(item_id):
    try:
        item = CardapioDoDia.query.get(item_id)
        if item:
            item.disponivel = not item.disponivel
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao alternar disponibilidade {item_id}: {e}")
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/remove_cardapio/<int:item_id>', methods=['POST'])
@login_required
def remove_cardapio(item_id):
    try:
        item = CardapioDoDia.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash('Item removido do cardápio.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover do cardápio {item_id}: {e}")
        flash('Erro ao remover item.', 'error')
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/clear_cardapio', methods=['POST'])
@login_required
def clear_cardapio():
    try:
        db.session.query(CardapioDoDia).delete()
        db.session.commit()
        flash('Cardápio limpo com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao limpar cardápio: {e}")
        flash('Erro ao limpar cardápio.', 'error')
    return redirect(url_for('admin_cardapio'))

@app.route('/admin/pedidos')
@login_required
def admin_pedidos():
    try:
        data_filtro_str = request.args.get('data')
        if data_filtro_str:
            data_filtro = datetime.strptime(data_filtro_str, '%Y-%m-%d').date()
        else:
            data_filtro = datetime.today().date()
            
        start_of_day = datetime.combine(data_filtro, datetime.min.time())
        end_of_day = datetime.combine(data_filtro, datetime.max.time())
        
        pedidos = Pedido.query.filter(
            Pedido.data_hora >= start_of_day,
            Pedido.data_hora <= end_of_day
        ).order_by(Pedido.data_hora.desc()).all()
        
        data_filtro_str_formatada = data_filtro.strftime('%Y-%m-%d')
    except Exception as e:
        logger.error(f"Erro ao carregar pedidos: {e}")
        pedidos = []
        data_filtro_str_formatada = ""
    return render_template('admin_pedidos.html', pedidos=pedidos, data_filtro=data_filtro_str_formatada)

@app.route('/admin/atualizar_pedido/<int:pedido_id>', methods=['POST'])
@login_required
def atualizar_pedido(pedido_id):
    try:
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            novo_status = request.form.get('status')
            if novo_status:
                pedido.status_pedido = novo_status
                db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar pedido {pedido_id}: {e}")
    return redirect(url_for('admin_pedidos'))

@app.route('/admin/imprimir_pedido/<int:pedido_id>', methods=['POST'])
@login_required
def imprimir_pedido_admin(pedido_id):
    try:
        pedido = Pedido.query.get(pedido_id)
        if pedido:
            itens_formatados = []
            for item in pedido.itens:
                itens_formatados.append({
                    'pratoNome': item.prato.nome_prato,
                    'tamanhoNome': item.tamanho.nome,
                    'quantidade': item.quantidade,
                    'preco': item.preco_unitario_pago
                })
            salvar_arquivo_cupom(pedido, itens_formatados)
    except Exception as e:
        logger.error(f"Erro ao imprimir pedido {pedido_id}: {e}")
    return redirect(url_for('admin_pedidos'))

# --- Rotas Públicas ---

@app.route('/')
def index():
    if 'cliente_id' in session:
        return redirect(url_for('cardapio'))
    return redirect(url_for('cliente_login'))

@app.route('/cardapio')
def cardapio():
    try:
        cardapio_hoje = CardapioDoDia.query.filter_by(disponivel=True).all()
        tamanhos = Tamanho.query.order_by(Tamanho.preco).all()
        cliente = None
        if 'cliente_id' in session:
            cliente = Cliente.query.get(session['cliente_id'])
    except Exception as e:
        logger.error(f"Erro ao carregar cardápio público: {e}")
        cardapio_hoje = []
        tamanhos = []
        cliente = None
    return render_template('index.html', cardapio_hoje=cardapio_hoje, tamanhos=tamanhos, cliente=cliente)

# --- Impressão ---

def salvar_arquivo_cupom(pedido, itens):
    try:
        pasta_fila = os.path.join(basedir, 'fila_impressao')
        if not os.path.exists(pasta_fila):
            os.makedirs(pasta_fila)

        nome_arquivo = f"pedido_{pedido.id}.txt"
        caminho_completo = os.path.join(pasta_fila, nome_arquivo)

        with open(caminho_completo, 'w', encoding='utf-8') as f:
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
            if pedido.forma_pagamento:
                f.write(f"PAGAMENTO: {pedido.forma_pagamento}\n")
                if pedido.forma_pagamento == 'DINHEIRO' and pedido.troco_para:
                    f.write(f"TROCO PARA: {pedido.troco_para}\n")
            f.write("-" * 32 + "\n")
            f.write("QTD  ITEM (TAM)               VALOR\n")

            total_pedido = 0
            for item in itens:
                nome_prato = item['pratoNome']
                nome_tamanho = item['tamanhoNome']
                qtd = int(item['quantidade'])
                preco_unit = float(item['preco'])
                preco_total_item = qtd * preco_unit
                total_pedido += preco_total_item

                linha_item = f"{qtd}x {nome_prato} ({nome_tamanho})"
                linha_preco = f"R$ {preco_total_item:.2f}"

                if len(linha_item) > 24:
                    linha_item = linha_item[:24]

                espacos = 32 - len(linha_item) - len(linha_preco)
                if espacos < 0: espacos = 0

                f.write(linha_item + (" " * espacos) + linha_preco + "\n")

            f.write("-" * 32 + "\n")
            
            texto_total = f"TOTAL: R$ {total_pedido:.2f}"
            espacos_total = 32 - len(texto_total)
            f.write((" " * espacos_total) + texto_total + "\n")
            
            f.write("\n")
            f.write(f"{pedido.data_hora.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("\n\n\n")

        logger.info(f"Arquivo {nome_arquivo} salvo na fila de impressão.")

    except Exception as e:
        logger.error(f"Erro ao salvar arquivo de impressão: {e}")

# --- API ---

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
        cliente_id = session.get('cliente_id')
        
        novo_pedido = Pedido(
            nome_cliente=dados_pedido['nome_cliente'],
            telefone_cliente=dados_pedido['telefone_cliente'],
            tipo_pedido=dados_pedido['tipo_pedido'],
            endereco_cliente=dados_pedido.get('endereco_cliente'),
            status_pedido='PENDENTE',
            forma_pagamento=dados_pedido.get('forma_pagamento'),
            troco_para=dados_pedido.get('troco_para'),
            cliente_id=cliente_id
        )
        db.session.add(novo_pedido)
        db.session.flush()

        itens_para_cupom = []
        for item in itens_carrinho:
            # Validar e buscar preço real do banco de dados
            tamanho = Tamanho.query.get(int(item['tamanhoId']))
            prato = Prato.query.get(int(item['pratoId']))
            
            if not tamanho or not prato:
                db.session.rollback()
                return jsonify({"success": False, "message": "Item inválido no carrinho."}), 400
            
            quantidade = max(1, int(item['quantidade']))
            
            novo_item = ItemPedido(
                pedido_id=novo_pedido.id,
                prato_id=prato.id,
                tamanho_id=tamanho.id,
                quantidade=quantidade,
                preco_unitario_pago=tamanho.preco  # Preço real do banco, não do frontend
            )
            db.session.add(novo_item)
            
            itens_para_cupom.append({
                'pratoNome': prato.nome_prato,
                'tamanhoNome': tamanho.nome,
                'quantidade': quantidade,
                'preco': tamanho.preco
            })
        
        db.session.commit()
        
        salvar_arquivo_cupom(novo_pedido, itens_para_cupom)

        return jsonify({
            "success": True, 
            "message": "Pedido recebido com sucesso!",
            "pedido_id": novo_pedido.id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao finalizar pedido: {e}")
        return jsonify({"success": False, "message": "Erro ao processar pedido. Tente novamente."}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)