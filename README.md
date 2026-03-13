# 🎮 Unread - OpenMouth Studio

<p align="center">
  <img src="static/logo.png" alt="Unread Logo" width="200">
</p>

## 📝 Sobre o Projeto
**Unread** é uma Visual Novel imersiva desenvolvida pelo **OpenMouth Studio**. O jogo foca no ensino da língua inglesa através de uma narrativa de mistério ambientada em uma biblioteca. O jogador deve desvendar enigmas enquanto pratica vocabulário, audição e tradução.

Este repositório contém o sistema de gestão do jogador, incluindo:
* Autenticação de usuários.
* Validação de segurança via **OTP (One-Time Password)** por e-mail.
* Dashboard de download do jogo.

---

## 🚀 Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Framework Web:** Flask
* **Banco de Dados:** PostgreeSQL
* **Segurança:** Flask-Mail (Integração com SMTP do Gmail)
* **Containerização:** Docker & Docker Compose
* **Interface:** HTML5, CSS3 (Design Moderno/Dark Mode)

---

## 🛠️ Como Executar o Projeto

### Pré-requisitos
* Docker instalado.
* Um arquivo `.env` configurado na raiz (veja a seção de Variáveis de Ambiente).

### Passo a Passo
1. Clone o repositório:
   ```bash
   git clone https://github.com/htcindy/OpenMouthStudios-Unread.git
2. Crie o arquivo .env e adicione suas credenciais.

3. Suba os containers:
   ```Bash
   docker-compose up --build

4. Em outro terminal inicie
   ```Bash
   docker-compose up
Iniciando assim todo o site

5. Acesse no navegador:
  http://localhost:5001


👤 Desenvolvedor
Estúdio: OpenMouth Studio

Status: Em desenvolvimento 🛠️
