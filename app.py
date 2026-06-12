import os
import hmac
import hashlib
import mercadopago
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import pyotp
from functools import wraps
from flask_mail import Mail, Message


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configurações Mailtrap
app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

# Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///usuarios.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Mercado Pago SDK
sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    secret_token = db.Column(db.String(32))
    verificado = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)  # <-- novo campo


with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_email' not in session:
            return redirect(url_for('login'))
        user = Usuario.query.filter_by(email=session['usuario_email']).first()
        if not user or not user.is_admin:
            return redirect(url_for('jogo'))
        return f(*args, **kwargs)
    return decorated_function


# --- ROTAS ---

@app.route('/')
def splash():
    return render_template('splash.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login_verificar', methods=['POST'])
def login_verificar():
    email = request.form.get('email')
    senha_digitada = request.form.get('senha')
    user = Usuario.query.filter_by(email=email).first()

    erro_msg = "Credenciais inválidas. Tente novamente."

    if user and check_password_hash(user.senha, senha_digitada):
        if user.verificado:
            session.clear()
            session['usuario_email'] = user.email
            session['is_admin'] = user.is_admin
            return redirect(url_for('jogo'))
        else:
            session['email_verificacao'] = user.email
            return redirect(url_for('verificar'))

    return render_template('login.html', erro=erro_msg)


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')


@app.route('/processa_cadastro', methods=['POST'])
def processa_cadastro():
    username = request.form.get('usuario')
    email = request.form.get('email')
    senha = request.form.get('senha')
    is_admin = username == os.getenv('ADMIN_USERNAME')

    user_existente = Usuario.query.filter_by(email=email).first()

    if user_existente:
        if not user_existente.verificado:
            session['email_verificacao'] = email
            totp = pyotp.TOTP(user_existente.secret_token)
            codigo = totp.now()

            msg = Message("Seu Código de Acesso", sender="noreply@englishadventure.com", recipients=[email])
            msg.body = f"Seu novo código é: {codigo}"
            mail.send(msg)

            return redirect(url_for('verificar'))
        return render_template('erro_cadastro.html')

    secret = pyotp.random_base32()
    senha_hash = generate_password_hash(senha)
    novo_user = Usuario(
        username=username,
        email=email,
        senha=senha_hash,
        secret_token=secret,
        verificado=False,
        is_admin=is_admin
    )

    try:
        db.session.add(novo_user)
        db.session.commit()

        totp = pyotp.TOTP(secret)
        codigo = totp.now()

        msg = Message("Bem-vindo! Confirme seu e-mail", sender="noreply@englishadventure.com", recipients=[email])
        msg.body = f"Welcome! Seu código de verificação é: {codigo}"
        mail.send(msg)

        session['email_verificacao'] = email
        return redirect(url_for('verificar'))

    except Exception as e:
        db.session.rollback()
        print(f"Erro detectado: {e}")
        return render_template('erro_geral.html')


@app.route('/verificar')
def verificar():
    if 'email_verificacao' not in session:
        return redirect(url_for('cadastro'))
    return render_template('verificar.html')


@app.route('/validar_otp', methods=['POST'])
def validar_otp():
    codigo_digitado = request.form.get('codigo_otp')
    email = session.get('email_verificacao')
    user = Usuario.query.filter_by(email=email).first()

    if user:
        totp = pyotp.TOTP(user.secret_token)
        if totp.verify(codigo_digitado, valid_window=1):
            user.verificado = True
            db.session.commit()

            session.pop('email_verificacao', None)
            session['usuario_email'] = user.email
            session['is_admin'] = user.is_admin

            return redirect(url_for('jogo'))

    return render_template('verificar.html', erro="Código inválido! Tente novamente.")


@app.route('/reenviar_otp')
def reenviar_otp():
    email = session.get('email_verificacao')
    if not email:
        return redirect(url_for('cadastro'))

    user = Usuario.query.filter_by(email=email).first()
    if user:
        totp = pyotp.TOTP(user.secret_token)
        codigo = totp.now()
        msg = Message("Novo Código de Acesso", sender="noreply@englishadventure.com", recipients=[email])
        msg.body = f"Seu novo código é: {codigo}"
        mail.send(msg)

    return redirect(url_for('verificar'))


@app.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')


@app.route('/enviar_reset', methods=['POST'])
def enviar_reset():
    email = request.form.get('email')
    user = Usuario.query.filter_by(email=email).first()

    if user:
        totp = pyotp.TOTP(user.secret_token)
        codigo = totp.now()

        msg = Message("Recuperação de Senha",
                      sender="noreply@englishadventure.com",
                      recipients=[email])
        msg.body = f"Use o código {codigo} para redefinir sua senha. Caso não tenha sido você quem solicitou a redefinição, altere sua senha para manter sua conta segura."
        mail.send(msg)

        session['reset_email'] = email
        return redirect(url_for('verificar_reset'))

    return render_template('esqueci_senha.html', erro="Email não encontrado")


@app.route('/verificar_reset')
def verificar_reset():
    if 'reset_email' not in session:
        return redirect(url_for('login'))
    return render_template('verificar_reset.html')


@app.route('/validar_reset', methods=['POST'])
def validar_reset():
    codigo = request.form.get('codigo')
    email = session.get('reset_email')

    user = Usuario.query.filter_by(email=email).first()

    if user:
        totp = pyotp.TOTP(user.secret_token)
        if totp.verify(codigo, valid_window=1):
            return redirect(url_for('nova_senha'))

    return render_template('verificar_reset.html', erro="Código inválido")


@app.route('/nova_senha')
def nova_senha():
    if 'reset_email' not in session:
        return redirect(url_for('login'))
    return render_template('nova_senha.html')


@app.route('/salvar_nova_senha', methods=['POST'])
def salvar_nova_senha():
    senha = request.form.get('senha')
    email = session.get('reset_email')

    user = Usuario.query.filter_by(email=email).first()

    if user:
        user.senha = generate_password_hash(senha)
        db.session.commit()

        session.pop('reset_email', None)
        return redirect(url_for('login'))

    return redirect(url_for('esqueci_senha'))


@app.route('/jogo')
@login_required
def jogo():
    user = Usuario.query.filter_by(email=session['usuario_email']).first()
    return render_template('jogo.html', is_admin=user.is_admin, is_premium=user.is_premium)

# --- MERCADO PAGO ---

@app.route('/comprar_premium')
@login_required
def comprar_premium():
    user = Usuario.query.filter_by(email=session['usuario_email']).first()

    if user.is_premium:
        return redirect(url_for('download_premium'))

    preference_data = {
    "items": [
        {
            "id": "unread-premium",
            "title": "Unread — Versão Completa",
            "description": "Acesso completo ao jogo com todos os capítulos e conteúdos.",
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": 29.90
        }
    ],
    "payer": {
        "email": user.email
    },
    "external_reference": str(user.id)
}

    try:
        result = sdk.preference().create(preference_data)
        preference = result.get("response", {})
        checkout_url = preference.get("sandbox_init_point") or preference.get("init_point")
        if not checkout_url:
            return f"Erro: checkout_url é None. Resposta MP: {result}", 500
        return redirect(checkout_url)
    except Exception as e:  
        print(f"Erro MP: {e}")
    return render_template('erro_geral.html')


@app.route('/pagamento/sucesso')
@login_required
def pagamento_sucesso():
    status = request.args.get('status')
    user_id = request.args.get('external_reference')

    if status == 'approved' and user_id:
        user = Usuario.query.get(int(user_id))
        if user and not user.is_premium:
            user.is_premium = True
            db.session.commit()

    user = Usuario.query.filter_by(email=session['usuario_email']).first()
    return render_template('pagamento_sucesso.html', is_premium=user.is_premium)


@app.route('/pagamento/falha')
@login_required
def pagamento_falha():
    return render_template('pagamento_falha.html')


@app.route('/pagamento/pendente')
@login_required
def pagamento_pendente():
    return render_template('pagamento_pendente.html')


@app.route('/download/premium')
@login_required
def download_premium():
    """Rota protegida — só usuários premium conseguem baixar o jogo completo."""
    user = Usuario.query.filter_by(email=session['usuario_email']).first()
    if not user.is_premium:
        return redirect(url_for('jogo'))
    # Aqui você pode redirecionar para o arquivo direto ou gerar um link temporário
    return redirect('/static/meu_jogo_completo.zip')


# --- PAINEL ADMIN ---

@app.route('/admin')
@admin_required
def admin():
    usuarios = Usuario.query.order_by(Usuario.id).all()
    return render_template('admin.html', usuarios=usuarios)


@app.route('/admin/deletar/<int:user_id>', methods=['POST'])
@admin_required
def admin_deletar(user_id):
    user = Usuario.query.get_or_404(user_id)
    if user.email == session['usuario_email']:
        return redirect(url_for('admin'))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/promover/<int:user_id>', methods=['POST'])
@admin_required
def admin_promover(user_id):
    user = Usuario.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('splash'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)