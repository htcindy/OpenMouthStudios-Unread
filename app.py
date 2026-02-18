from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pyotp

app = Flask(__name__)
app.secret_key = 'chave_secreta_do_seu_jogo'

# Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False) # Aumentei o tamanho para o hash
    secret_token = db.Column(db.String(32))
    verificado = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

# --- ROTAS ---

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/login')
def login():
    return render_template('login.html')

# --- NOVA ROTA DE LOGIN ADICIONADA AQUI ---
@app.route('/login_verificar', methods=['POST'])
def login_verificar():
    email = request.form.get('email')
    senha_digitada = request.form.get('senha')
    
    user = Usuario.query.filter_by(email=email).first()
    
    # Verifica se o usuário existe e se o hash da senha bate
    if user and check_password_hash(user.senha, senha_digitada):
        if user.verificado:
            session['email_verificacao'] = user.email
            return redirect(url_for('jogo'))
        else:
            session['email_verificacao'] = user.email
            return "Verifique seu e-mail primeiro! <a href='/verificar'>Ir para verificação</a>"
    
    return "E-mail ou senha incorretos! <a href='/login'>Tentar novamente</a>"

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/processa_cadastro', methods=['POST'])
def processa_cadastro():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    user_existente = Usuario.query.filter_by(email=email).first()
    
    if user_existente:
        if not user_existente.verificado:
            session['email_verificacao'] = email
            totp = pyotp.TOTP(user_existente.secret_token)
            print(f"--- [RE-ENVIANDO] Código para {email}: {totp.now()} ---")
            return redirect(url_for('verificar'))
        return "E-mail já cadastrado! <a href='/login'>Faça Login</a>"

    # CORREÇÃO AQUI: Primeiro geramos o segredo e o hash, depois criamos o objeto
    secret = pyotp.random_base32()
    senha_hash = generate_password_hash(senha)
    
    novo_user = Usuario(email=email, senha=senha_hash, secret_token=secret, verificado=False)
    
    try:
        db.session.add(novo_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Erro ao salvar no banco: {e}"
    
    totp = pyotp.TOTP(secret)
    print(f"--- [CÓDIGO GERADO] Para {email}: {totp.now()} ---")
    
    session['email_verificacao'] = email
    return redirect(url_for('verificar'))

@app.route('/verificar')
def verificar():
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
            return redirect(url_for('jogo'))
    
    return f"Código inválido para o email {email}! Tente novamente."

@app.route('/jogo')
def jogo():
    return render_template('jogo.html')

if __name__ == '__main__':
    app.run(debug=True)