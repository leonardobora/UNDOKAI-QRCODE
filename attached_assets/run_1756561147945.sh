#!/bin/bash
# Lightera BUNDOKAI - Quick Start Script

echo "🚀 Iniciando Lightera BUNDOKAI System..."

# Check Python version
python3 --version || { echo "Python 3 não encontrado!"; exit 1; }

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv --prompt="lightera-bundokai"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📋 Instalando dependências..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Setup environment
if [ ! -f ".env" ]; then
    echo "⚙️ Configurando ambiente..."
    cp .env.example .env
fi

# Create directories
mkdir -p static/qr_codes static/uploads logs reports static/checkin_cache

# Initialize database
echo "🗄️ Inicializando banco de dados..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"

# Start application
echo "🎯 Iniciando aplicação..."
echo "📱 Acesse: http://localhost:5000"
echo "📊 Dashboard: http://localhost:5000/dashboard" 
echo "📷 Scanner: http://localhost:5000/scanner"
python app.py
