🚀 Como Rodar o Projeto
Pré-requisitos
Docker Desktop instalado e rodando.

VS Code (ou seu editor de preferência).

Passo a Passo
Clone o repositório ou entre na pasta do projeto:

Bash

cd Unread-OpenMouthStudios
Suba o ambiente com o Docker:
No terminal, execute o comando abaixo. Ele vai baixar a imagem do Python, instalar as bibliotecas do requirements.txt e ligar o servidor:

Bash

docker-compose up --build
Acesse no Navegador:
O projeto foi configurado para evitar conflitos de portas. Acesse através do endereço:

http://localhost:5001