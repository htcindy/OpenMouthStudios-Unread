# Usa uma versão leve do Python
FROM python:3.10-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências primeiro (otimiza o cache)
COPY requirements.txt .

# Instala as bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o seu código para dentro do container
COPY . .

# Expõe a porta que o Flask usa
EXPOSE 5000

# Comando para rodar o app
CMD ["python", "app.py"]