#!/bin/bash
# Lightera BUNDOKAI - Quick Start Script

echo "🚀 Iniciando Lightera BUNDOKAI System..."
echo "   Sistema de Check-in e Controle de Entregas"
echo "   Substitui Digitevent - Economia R$ 5.427,00/evento"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Check Python version
print_header "📋 Verificando Requisitos..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não encontrado! Por favor, instale Python 3.8 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python $PYTHON_VERSION encontrado"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_header "📦 Criando ambiente virtual..."
    python3 -m venv venv --prompt="lightera-bundokai"
    if [ $? -eq 0 ]; then
        print_status "Ambiente virtual criado com sucesso"
    else
        print_error "Falha ao criar ambiente virtual"
        exit 1
    fi
else
    print_status "Ambiente virtual já existe"
fi

# Activate virtual environment
print_header "🔧 Ativando ambiente virtual..."
source venv/bin/activate
if [ $? -eq 0 ]; then
    print_status "Ambiente virtual ativado"
else
    print_error "Falha ao ativar ambiente virtual"
    exit 1
fi

# Upgrade pip
print_header "⬆️ Atualizando pip..."
python -m pip install --upgrade pip setuptools wheel --quiet
print_status "Pip atualizado"

# Install dependencies
print_header "📋 Instalando dependências..."
echo "   Flask, SQLAlchemy, QRCode, Pandas, Gunicorn..."

pip install --quiet \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.0.5 \
    qrcode[pil]==7.4.2 \
    pandas==2.1.1 \
    gunicorn==21.2.0 \
    python-dotenv==1.0.0 \
    Pillow==10.0.1 \
    opencv-python-headless==4.8.1.78

if [ $? -eq 0 ]; then
    print_status "Dependências instaladas com sucesso"
else
    print_error "Falha ao instalar dependências"
    exit 1
fi

# Setup environment file
print_header "⚙️ Configurando ambiente..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Arquivo .env criado a partir do template"
    print_warning "Configure suas credenciais de email no arquivo .env"
else
    print_status "Arquivo .env já existe"
fi

# Create directories
print_header "📁 Criando diretórios..."
mkdir -p static/qr_codes static/uploads logs reports static/checkin_cache
print_status "Diretórios criados"

# Initialize database
print_header "🗄️ Inicializando banco de dados..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database tables created')" 2>/dev/null
if [ $? -eq 0 ]; then
    print_status "Banco de dados inicializado"
else
    print_warning "Executando script de setup do banco..."
    python scripts/setup_database.py
    if [ $? -eq 0 ]; then
        print_status "Banco de dados configurado com sucesso"
    else
        print_error "Falha ao configurar banco de dados"
        exit 1
    fi
fi

# Check if we should generate sample data
read -p "$(echo -e ${YELLOW}"🎲 Gerar dados de exemplo para desenvolvimento? (y/N): "${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_header "🎲 Gerando dados de exemplo..."
    python scripts/generate_sample_data.py
    if [ $? -eq 0 ]; then
        print_status "Dados de exemplo gerados"
    else
        print_warning "Falha ao gerar dados de exemplo (não crítico)"
    fi
fi

# Run health check
print_header "🔍 Verificando integridade do sistema..."
python -c "
from app import app, db
from models import Participant, CheckIn, DeliveryItem
try:
    with app.app_context():
        participants = Participant.query.count()
        checkins = CheckIn.query.count()
        items = DeliveryItem.query.count()
        print(f'✅ Sistema operacional:')
        print(f'   📊 {participants} participantes')
        print(f'   ✅ {checkins} check-ins')
        print(f'   📦 {items} itens de entrega')
except Exception as e:
    print(f'❌ Erro na verificação: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Verificação de integridade passou"
else
    print_error "Falha na verificação de integridade"
    exit 1
fi

# Display startup information
echo ""
print_header "🎯 Sistema Lightera BUNDOKAI - Pronto para uso!"
echo ""
print_info "📱 URLs Principais:"
echo "   • Homepage:        http://localhost:5000"
echo "   • Inscrições:      http://localhost:5000/register"
echo "   • Scanner QR:      http://localhost:5000/scanner"
echo "   • Busca Manual:    http://localhost:5000/checkin/search"
echo "   • Dashboard:       http://localhost:5000/dashboard"
echo "   • Entregas:        http://localhost:5000/delivery"
echo "   • Estoque:         http://localhost:5000/inventory"
echo ""
print_info "🔧 Comandos Úteis:"
echo "   • Health Check:    curl http://localhost:5000/health"
echo "   • Parar Servidor:  Ctrl+C"
echo "   • Logs:            tail -f logs/bundokai.log"
echo ""
print_info "📧 Configuração de Email:"
echo "   • Configure SMTP no arquivo .env para envio de QR codes"
echo "   • Use --dry-run para testar: python scripts/send_qr_emails.py --dry-run"
echo ""
print_info "💰 ROI: Economia de R$ 5.427,00 vs Digitevent por evento"
echo ""

# Start the application
print_header "🚀 Iniciando servidor Flask..."
export FLASK_ENV=development
export FLASK_DEBUG=True

echo ""
print_status "Servidor iniciando em http://localhost:5000"
print_info "Pressione Ctrl+C para parar o servidor"
echo ""

# Run the Flask application
python app.py
