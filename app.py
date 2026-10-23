import os
import json
import secrets
import logging
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

basedir = os.path.abspath(os.path.dirname(__file__))

# Carregar variáveis de ambiente do .env
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

# Configurações de Segurança
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
csrf = CSRFProtect(app)

# Banco de dados (PostgreSQL na nuvem ou SQLite local)
database_url = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'restaurante.db'))
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Diretório para uploads locais (fallback)
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Token do Agente de Impressão na Cozinha
PRINTER_TOKEN = os.getenv('PRINTER_TOKEN', 'dogao_printer_sec_token')

# Configuração do Cloudinary para imagens na Nuvem
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
    CLOUDINARY_ATIVO = True
else:
    CLOUDINARY_ATIVO = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# --- Upload de Fotos Inteligente ---

def upload_foto_prato(foto_arquivo):
    if not foto_arquivo or foto_arquivo.filename == '':
        return ''
    filename = secure_filename(foto_arquivo.filename)
    if not filename:
        return ''

    if CLOUDINARY_ATIVO:
        try:
            logger.info(f"Enviando foto '{filename}' para o Cloudinary...")
            res = cloudinary.uploader.upload(
                foto_arquivo,
                folder="dogao_castelo",
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'auto'}
                ]
            )
            return res.get('secure_url', '')
        except Exception as e:
            logger.error(f"Erro no upload Cloudinary: {e}. Usando armazenamento local.")
            foto_arquivo.seek(0)

    # Fallback local
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    foto_arquivo.save(caminho)
    return url_for('static', filename='uploads/' + filename)

# --- Models ---

class Configuracao(db.Model):
    __tablename__ = 'configuracao'
    chave = db.Column(db.String(50), primary_key=True)
    valor = db.Column(db.Text, nullable=True)

    @classmethod
    def get(cls, chave, default=''):
        try:
            item = cls.query.filter_by(chave=chave).first()
            return item.valor if item and item.valor is not None else default
        except Exception:
            return default

    @classmethod
    def set(cls, chave, valor):
        try:
            item = cls.query.filter_by(chave=chave).first()
            if not item:
                item = cls(chave=chave, valor=str(valor))
                db.session.add(item)
            else:
                item.valor = str(valor)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar configuração {chave}: {e}")

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
    status_pedido = db.Column(db.String(30), default='PENDENTE')
    forma_pagamento = db.Column(db.String(50), nullable=True)
    troco_para = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    taxa_entrega = db.Column(db.Float, default=0.0, nullable=False)
    impresso = db.Column(db.Boolean, default=False, nullable=False)
    impresso_em = db.Column(db.DateTime, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente = db.relationship('Cliente', back_populates='pedidos')
    itens = db.relationship('ItemPedido', back_populates='pedido', cascade='all, delete-orphan')

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

# --- Funções de Autenticação e Permissão ---

def get_admin_password_hash():
    return Configuracao.get('admin_password_hash', '')

def set_admin_password(new_password):
    Configuracao.set('admin_password_hash', generate_password_hash(new_password))
    Configuracao.set('deve_trocar_senha', '0')

def check_admin_password(password):
    hash_gravado = get_admin_password_hash()
    if not hash_gravado:
        return False
    return check_password_hash(hash_gravado, password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        
        # Obrigatoriedade de troca de senha no primeiro acesso
        deve_trocar = Configuracao.get('deve_trocar_senha', '0') == '1'
        if deve_trocar and request.endpoint not in ['admin_configuracoes', 'admin_logout', 'static']:
            flash('⚠️ Por segurança, altere a senha padrão de administrador antes de acessar as demais telas.', 'error')
            return redirect(url_for('admin_configuracoes'))
            
        return f(*args, **kwargs)
    return decorated_function

def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            return redirect(url_for('cliente_login'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor para disponibilizar CSRF e configurações nos templates
@app.context_processor
def inject_global_vars():
    hoje = datetime.now()
    dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    data_formatada = f"{dias_semana[hoje.weekday()]}, {hoje.day} de {meses[hoje.month - 1]}"

    return {
        'data_hoje': data_formatada,
        'loja_aberta': Configuracao.get('loja_aberta', '1') == '1',
        'mensagem_loja_fechada': Configuracao.get('mensagem_loja_fechada', 'Estamos fechados no momento.'),
        'taxa_entrega_padrao': float(Configuracao.get('taxa_entrega', '0.00') or 0.0),
        'restaurante_whatsapp': Configuracao.get('restaurante_whatsapp', os.getenv('RESTAURANTE_WHATSAPP', '553194585341')),
        'deve_trocar_senha': Configuracao.get('deve_trocar_senha', '0') == '1'
    }

# --- Rotas de Autenticação Admin ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if check_admin_password(senha):
            session['logged_in'] = True
            if Configuracao.get('deve_trocar_senha', '0') == '1':
                flash('⚠️ Atenção: Por segurança, altere a senha padrão de administrador agora.', 'error')
                return redirect(url_for('admin_configuracoes'))
            return redirect(url_for('admin_pedidos'))
        else:
            flash('Senha incorreta.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/configuracoes', methods=['GET', 'POST'])
@login_required
def admin_configuracoes():
    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'alterar_senha':
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            
            if not check_admin_password(senha_atual):
                flash('A senha atual informada está incorreta.', 'error')
            elif not nova_senha or len(nova_senha) < 4:
                flash('A nova senha deve ter no mínimo 4 caracteres.', 'error')
            else:
                set_admin_password(nova_senha)
                flash('Senha de administrador alterada com sucesso!', 'success')

        elif acao == 'atualizar_loja':
            loja_aberta = '1' if request.form.get('loja_aberta') == 'on' else '0'
            msg = request.form.get('mensagem_loja_fechada', '').strip()
            taxa = request.form.get('taxa_entrega', '0.00').replace(',', '.').strip()
            whatsapp = request.form.get('restaurante_whatsapp', '').strip()
            whatsapp_limpo = ''.join(c for c in whatsapp if c.isdigit())

            try:
                float(taxa)
            except ValueError:
                taxa = '0.00'

            Configuracao.set('loja_aberta', loja_aberta)
            if msg:
                Configuracao.set('mensagem_loja_fechada', msg)
            Configuracao.set('taxa_entrega', taxa)
            if whatsapp_limpo:
                Configuracao.set('restaurante_whatsapp', whatsapp_limpo)

            flash('Configurações da loja atualizadas com sucesso!', 'success')

    return render_template('admin_configuracoes.html')

# --- Rotas de Autenticação Cliente ---

@app.route('/cliente/cadastro', methods=['GET', 'POST'])
def cliente_cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')
        
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
    cliente = db.session.get(Cliente, session['cliente_id'])
    if request.method == 'POST':
        novo_nome = request.form.get('nome', '').strip()
        novo_telefone = request.form.get('telefone', '').strip()
        novo_telefone_limpo = ''.join(c for c in novo_telefone if c.isdigit())
        
        if not novo_nome or len(novo_nome) < 2:
            flash('O nome deve ter no mínimo 2 caracteres.', 'error')
            return redirect(url_for('minha_conta'))
        
        if len(novo_telefone_limpo) < 10 or len(novo_telefone_limpo) > 11:
            flash('Informe um telefone válido com DDD.', 'error')
            return redirect(url_for('minha_conta'))
        
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

# --- Rotas Admin (Gestão de Pratos, Tamanhos e Cardápio) ---

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
        tamanho = db.session.get(Tamanho, tamanho_id)
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
            foto_url = upload_foto_prato(foto_arquivo)

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
        prato = db.session.get(Prato, prato_id)
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
            
            foto_arquivo = request.files.get('foto_arquivo')
            if foto_arquivo and foto_arquivo.filename != '':
                prato.foto_url = upload_foto_prato(foto_arquivo)
            elif request.form.get('foto_url'):
                prato.foto_url = request.form.get('foto_url')
                
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
            prato = db.session.get(Prato, prato_id)
            descricao_dia = prato.descricao_base if prato else ''
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
        item = db.session.get(CardapioDoDia, item_id)
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
        item = db.session.get(CardapioDoDia, item_id)
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

# --- Rotas Admin (Gestão de Pedidos em Tempo Real) ---

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
        pedido = db.session.get(Pedido, pedido_id)
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
        pedido = db.session.get(Pedido, pedido_id)
        if pedido:
            texto_cupom = formatar_texto_cupom(pedido)
            salvar_arquivo_cupom_local(pedido.id, texto_cupom)
            pedido.impresso = False
            db.session.commit()
            flash(f'Comanda do Pedido #{pedido.id} enviada para a fila de impressão.', 'success')
    except Exception as e:
        logger.error(f"Erro ao imprimir pedido {pedido_id}: {e}")
        flash('Erro ao solicitar impressão.', 'error')
    return redirect(url_for('admin_pedidos'))

# API para atualização automática sem F5 no Painel Admin
@app.route('/api/admin/pedidos/novos')
@login_required
def api_pedidos_novos():
    ultimo_id = request.args.get('ultimo_id', type=int, default=0)
    data_filtro_str = request.args.get('data')
    
    if data_filtro_str:
        try:
            data_filtro = datetime.strptime(data_filtro_str, '%Y-%m-%d').date()
        except ValueError:
            data_filtro = datetime.today().date()
    else:
        data_filtro = datetime.today().date()

    start_of_day = datetime.combine(data_filtro, datetime.min.time())
    end_of_day = datetime.combine(data_filtro, datetime.max.time())

    pedidos = Pedido.query.filter(
        Pedido.data_hora >= start_of_day,
        Pedido.data_hora <= end_of_day
    ).order_by(Pedido.data_hora.desc()).all()

    maior_id_atual = max([p.id for p in pedidos], default=0)
    novos_detectados = any(p.id > ultimo_id for p in pedidos) if ultimo_id > 0 else False

    total_pendentes = sum(1 for p in pedidos if p.status_pedido == 'PENDENTE')

    return jsonify({
        "success": True,
        "novos_detectados": novos_detectados,
        "maior_id": maior_id_atual,
        "total_pendentes": total_pendentes,
        "total_pedidos": len(pedidos)
    })

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
            cliente = db.session.get(Cliente, session['cliente_id'])
    except Exception as e:
        logger.error(f"Erro ao carregar cardápio público: {e}")
        cardapio_hoje = []
        tamanhos = []
        cliente = None
    return render_template('index.html', cardapio_hoje=cardapio_hoje, tamanhos=tamanhos, cliente=cliente)

# --- Formatação e Fila de Impressão ---

def formatar_texto_cupom(pedido):
    linhas = []
    linhas.append("DOGAO DO CASTELO\n")
    linhas.append("-" * 32 + "\n")
    linhas.append(f"PEDIDO #{pedido.id}\n")
    linhas.append(f"Cliente: {pedido.nome_cliente}\n")
    linhas.append(f"Telefone: {pedido.telefone_cliente or 'Nao informado'}\n")
    linhas.append("\n")

    if pedido.tipo_pedido == 'ENTREGA':
        linhas.append(">>> PARA ENTREGA <<<\n")
        linhas.append(f"Endereco: {pedido.endereco_cliente or 'Retirada na loja'}\n")
    else:
        linhas.append(">>> PARA RETIRADA <<<\n")

    linhas.append("-" * 32 + "\n")
    if pedido.forma_pagamento:
        linhas.append(f"PAGAMENTO: {pedido.forma_pagamento}\n")
        if pedido.forma_pagamento == 'DINHEIRO' and pedido.troco_para:
            linhas.append(f"TROCO PARA: {pedido.troco_para}\n")

    if pedido.observacoes:
        linhas.append("-" * 32 + "\n")
        linhas.append("OBSERVACOES:\n")
        linhas.append(f"{pedido.observacoes}\n")

    linhas.append("-" * 32 + "\n")
    linhas.append("QTD  ITEM (TAM)               VALOR\n")

    subtotal = 0.0
    for item in pedido.itens:
        nome_prato = item.prato.nome_prato if item.prato else "Item"
        nome_tamanho = item.tamanho.nome if item.tamanho else ""
        qtd = item.quantidade
        preco_unit = item.preco_unitario_pago
        preco_total_item = qtd * preco_unit
        subtotal += preco_total_item

        linha_item = f"{qtd}x {nome_prato} ({nome_tamanho})"
        linha_preco = f"R$ {preco_total_item:.2f}"

        if len(linha_item) > 24:
            linha_item = linha_item[:24]

        espacos = 32 - len(linha_item) - len(linha_preco)
        if espacos < 0:
            espacos = 0

        linhas.append(linha_item + (" " * espacos) + linha_preco + "\n")

    linhas.append("-" * 32 + "\n")

    if pedido.tipo_pedido == 'ENTREGA' and pedido.taxa_entrega > 0:
        texto_taxa = f"TAXA ENTREGA: R$ {pedido.taxa_entrega:.2f}"
        espacos_taxa = 32 - len(texto_taxa)
        if espacos_taxa < 0: espacos_taxa = 0
        linhas.append((" " * espacos_taxa) + texto_taxa + "\n")

    total_final = subtotal + (pedido.taxa_entrega if pedido.tipo_pedido == 'ENTREGA' else 0.0)
    texto_total = f"TOTAL: R$ {total_final:.2f}"
    espacos_total = 32 - len(texto_total)
    if espacos_total < 0: espacos_total = 0
    linhas.append((" " * espacos_total) + texto_total + "\n")
    
    linhas.append("\n")
    linhas.append(f"{pedido.data_hora.strftime('%d/%m/%Y %H:%M:%S')}\n")
    linhas.append("\n\n\n")

    return "".join(linhas)

def salvar_arquivo_cupom_local(pedido_id, texto_cupom):
    try:
        pasta_fila = os.path.join(basedir, 'fila_impressao')
        os.makedirs(pasta_fila, exist_ok=True)
        nome_arquivo = f"pedido_{pedido_id}.txt"
        caminho_completo = os.path.join(pasta_fila, nome_arquivo)
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(texto_cupom)
        logger.info(f"Arquivo {nome_arquivo} salvo na fila local.")
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo local de impressão: {e}")

# --- API do Agente de Impressão na Nuvem (Autenticado por Token) ---

@app.route('/api/agente/pedidos/pendentes', methods=['GET'])
@csrf.exempt
def agente_pedidos_pendentes():
    token = request.headers.get('X-Printer-Token')
    if not token or token != PRINTER_TOKEN:
        return jsonify({"success": False, "message": "Token não autorizado."}), 401

    pedidos = Pedido.query.filter_by(impresso=False).order_by(Pedido.data_hora.asc()).all()
    lista_pedidos = []
    for p in pedidos:
        lista_pedidos.append({
            "id": p.id,
            "data_hora": p.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
            "cliente": p.nome_cliente,
            "tipo": p.tipo_pedido,
            "cupom_texto": formatar_texto_cupom(p)
        })

    return jsonify({"success": True, "pedidos": lista_pedidos})

@app.route('/api/agente/pedidos/<int:pedido_id>/confirmar-impressao', methods=['POST'])
@csrf.exempt
def agente_confirmar_impressao(pedido_id):
    token = request.headers.get('X-Printer-Token')
    if not token or token != PRINTER_TOKEN:
        return jsonify({"success": False, "message": "Token não autorizado."}), 401

    pedido = db.session.get(Pedido, pedido_id)
    if not pedido:
        return jsonify({"success": False, "message": "Pedido não encontrado."}), 404

    pedido.impresso = True
    pedido.impresso_em = datetime.now()
    db.session.commit()
    return jsonify({"success": True, "message": f"Pedido #{pedido_id} marcado como impresso."})

# --- API de Finalização de Pedido do Cliente ---

@app.route('/api/finalizar_pedido', methods=['POST'])
def api_finalizar_pedido():
    # Validar se a loja está aberta
    loja_aberta = Configuracao.get('loja_aberta', '1') == '1'
    if not loja_aberta:
        msg = Configuracao.get('mensagem_loja_fechada', 'Estamos fechados no momento.')
        return jsonify({"success": False, "message": f"A lanchonete está fechada agora: {msg}"}), 400

    if not request.is_json:
        return jsonify({"success": False, "message": "Erro: Formato inválido."}), 400

    data = request.get_json()
    dados_pedido = data.get('pedido')
    itens_carrinho = data.get('carrinho')

    if not dados_pedido or not itens_carrinho:
        return jsonify({"success": False, "message": "Dados incompletos."}), 400

    try:
        cliente_id = session.get('cliente_id')
        tipo_pedido = dados_pedido.get('tipo_pedido', 'RETIRADA')
        
        taxa_entrega = 0.0
        if tipo_pedido == 'ENTREGA':
            taxa_entrega = float(Configuracao.get('taxa_entrega', '0.00') or 0.0)

        novo_pedido = Pedido(
            nome_cliente=dados_pedido['nome_cliente'],
            telefone_cliente=dados_pedido.get('telefone_cliente'),
            tipo_pedido=tipo_pedido,
            endereco_cliente=dados_pedido.get('endereco_cliente'),
            status_pedido='PENDENTE',
            forma_pagamento=dados_pedido.get('forma_pagamento'),
            troco_para=dados_pedido.get('troco_para'),
            observacoes=dados_pedido.get('observacoes', '').strip(),
            taxa_entrega=taxa_entrega,
            impresso=False,
            cliente_id=cliente_id
        )
        db.session.add(novo_pedido)
        db.session.flush()

        for item in itens_carrinho:
            tamanho = db.session.get(Tamanho, int(item['tamanhoId']))
            prato = db.session.get(Prato, int(item['pratoId']))
            
            if not tamanho or not prato:
                db.session.rollback()
                return jsonify({"success": False, "message": "Item inválido no carrinho."}), 400
            
            quantidade = max(1, int(item['quantidade']))
            
            novo_item = ItemPedido(
                pedido_id=novo_pedido.id,
                prato_id=prato.id,
                tamanho_id=tamanho.id,
                quantidade=quantidade,
                preco_unitario_pago=tamanho.preco
            )
            db.session.add(novo_item)
        
        db.session.commit()
        
        # Gerar o cupom formatado e salvar na fila local para contingência
        texto_cupom = formatar_texto_cupom(novo_pedido)
        salvar_arquivo_cupom_local(novo_pedido.id, texto_cupom)

        return jsonify({
            "success": True, 
            "message": "Pedido recebido com sucesso!",
            "pedido_id": novo_pedido.id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao finalizar pedido: {e}")
        return jsonify({"success": False, "message": "Erro ao processar pedido. Tente novamente."}), 500

# --- Inicialização ---

with app.app_context():
    db.create_all()
    # Migrar ou inicializar configurações essenciais
    if not Configuracao.get('admin_password_hash'):
        Configuracao.set('admin_password_hash', generate_password_hash('admin123'))
        Configuracao.set('deve_trocar_senha', '1')

    if Configuracao.get('loja_aberta') == '':
        Configuracao.set('loja_aberta', '1')

    if Configuracao.get('mensagem_loja_fechada') == '':
        Configuracao.set('mensagem_loja_fechada', 'Estamos fechados no momento. Nosso expediente começará em breve!')

    if Configuracao.get('taxa_entrega') == '':
        Configuracao.set('taxa_entrega', '0.00')

    if Configuracao.get('restaurante_whatsapp') == '':
        Configuracao.set('restaurante_whatsapp', os.getenv('RESTAURANTE_WHATSAPP', '553194585341'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)