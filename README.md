# Lightera BUNDOKAI - Sistema de Check-in e Entregas

![CI/CD Status](https://github.com/leonardobora/UNDOKAI-QRCODE/workflows/Lightera%20BUNDOKAI%20CI%2FCD/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema desenvolvido com funcionalidades essenciais para eventos corporativos da Furukawa Electric/Lightera, otimizado para até 2.500 participantes.

## 🎯 Funcionalidades

### ✅ Check-in de Evento (BUNDOKAI)
- Inscrição online com nome + dependentes (até 5 por família)
- Geração automática de QR Codes únicos
- Scanner web para check-in via câmera do dispositivo
- Busca por nome (modo offline para contingências)
- Dashboard em tempo real com estatísticas
- Suporte a múltiplos pontos de check-in simultâneos

### 📦 Controle de Entregas de Final de Ano  
- Gestão de estoque por categoria (festas, cestas, brinquedos, material escolar)
- Check-in de entregas com QR Code
- Controle de horários e responsáveis
- Relatórios de controle e reconciliação automáticos
- Tracking de quem pegou vs quem não pegou

### 📧 Sistema de Comunicação
- Envio automático de QR Codes (1 semana antes do evento)
- Lembretes por email configuráveis
- Templates personalizáveis com branding Lightera
- Tracking de entrega e abertura de emails
- Logs de auditoria completos

## 🚀 Desenvolvimento Local - Guia Completo

### Pré-requisitos
- Python 3.11 ou superior
- Git
- pip (gerenciador de pacotes Python)

### 1. Clone e Configuração Inicial

```bash
# Clone o repositório
git clone https://github.com/leonardobora/UNDOKAI-QRCODE.git
cd UNDOKAI-QRCODE

# Crie um ambiente virtual
python -m venv venv --prompt="lightera-bundokai"

# Ative o ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Atualize pip e instale dependências
python -m pip install --upgrade pip
pip install -e .[test,dev]
```

### 2. Configuração do Ambiente

```bash
# Copie o arquivo de configuração
cp .env.example .env

# Edite o arquivo .env com suas configurações
# Variáveis importantes:
# - SMTP_* para configuração de email
# - DATABASE_URL para banco de dados personalizado
# - SESSION_SECRET para segurança das sessões
```

### 3. Inicialização do Banco de Dados

```bash
# Crie as tabelas do banco
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized')"

# Crie diretórios necessários
mkdir -p static/qr_codes static/uploads logs reports static/checkin_cache

# (Opcional) Carregue dados de exemplo
python -c "from utils import create_sample_delivery_items; create_sample_delivery_items(); print('✅ Sample data loaded')"
```

### 4. Executar a Aplicação

#### Desenvolvimento
```bash
# Modo desenvolvimento com recarga automática
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py

# A aplicação estará disponível em: http://localhost:5000
```

#### Método Alternativo: Script Automático
```bash
chmod +x run.sh
./run.sh
```

## 🧪 Execução de Testes

### Testes Unitários Completos
```bash
# Execute todos os testes
pytest tests/ -v

# Execute testes específicos
pytest tests/test_models.py -v          # Testes dos modelos de dados
pytest tests/test_utils.py -v           # Testes das funções utilitárias
pytest tests/test_routes.py -v          # Testes das rotas da aplicação

# Execute testes com cobertura
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
# Relatório HTML gerado em: htmlcov/index.html
```

### Verificação de Código
```bash
# Verificação de estilo e qualidade
flake8 . --max-line-length=88 --statistics
black --check .
isort --check-only .

# Correção automática de formatação
black .
isort .
```

### Testes de Integração
```bash
# Teste de importação de módulos
python -c "from app import app, db; from models import *; from utils import *; print('✅ All imports successful')"

# Teste de geração de QR Code
python -c "from utils import generate_qr_code; qr = generate_qr_code('TEST123'); print('✅ QR generation working')"

# Teste de conectividade do banco
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database connection OK')"
```

## 🔧 Comandos de Desenvolvimento

### Usando AGENTS.md (Automação com IA)
Este projeto utiliza o sistema AGENTS.md para automação:

```bash
# Setup completo do ambiente
python agents_executor.py --section setup

# Executar testes automatizados
python agents_executor.py --section test

# Build e validação
python agents_executor.py --section build

# Limpeza do ambiente
python agents_executor.py --section cleanup
```

### Comandos Manuais Principais
```bash
# Desenvolvimento
export FLASK_ENV=development && python app.py

# Produção
export FLASK_ENV=production && gunicorn --workers=4 --bind=0.0.0.0:5000 app:app

# Backup do banco
cp bundokai.db backups/bundokai_$(date +%Y%m%d_%H%M%S).db

# Estatísticas do sistema
python -c "from utils import get_checkin_statistics; print(get_checkin_statistics())"
```

## 📊 Monitoramento e Saúde do Sistema

### Health Check
```bash
# Verificação local
curl http://localhost:5000/health

# Verificação com timeout
timeout 10 curl -f http://localhost:5000/health || echo "Health check failed"
```

### Logs e Monitoramento
```bash
# Visualizar logs em tempo real
tail -f logs/app.log

# Estatísticas de uso de memória
python -c "import psutil; print(f'Memory usage: {psutil.virtual_memory().percent}%')"

# Tamanho do banco de dados
python -c "import os; print(f'Database size: {os.path.getsize(\"bundokai.db\") / 1024 / 1024:.2f} MB')"
```

## 🐳 Deploy com Docker

### Build da Imagem
```bash
# Construir imagem Docker
docker build -t lightera-bundokai .

# Executar container
docker run -p 5000:5000 -v $(pwd)/bundokai.db:/app/bundokai.db lightera-bundokai
```

### Docker Compose (Recomendado)
```bash
# Executar stack completa
docker-compose up -d

# Visualizar logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

## 🚀 Deploy em Produção

### Preparação
```bash
# Configurar variáveis de ambiente de produção
export FLASK_ENV=production
export DATABASE_URL=sqlite:///bundokai_prod.db
export SESSION_SECRET=your-secret-key-here

# Criar diretórios de produção
mkdir -p logs reports backups static/qr_codes static/uploads
```

### Gunicorn (Recomendado)
```bash
# Instalar Gunicorn (se não instalado)
pip install gunicorn

# Executar com múltiplos workers
gunicorn --workers=4 --bind=0.0.0.0:5000 --timeout=120 --keep-alive=2 app:app

# Com arquivo de configuração
gunicorn --config gunicorn.conf.py app:app
```

### Nginx (Proxy Reverso)
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔐 Configuração de Segurança

### Variáveis de Ambiente Essenciais
```bash
# .env para produção
SESSION_SECRET=your-super-secret-key-minimum-32-chars
DATABASE_URL=postgresql://user:pass@localhost/bundokai  # Para PostgreSQL
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### HTTPS e SSL
```bash
# Com certificado SSL
gunicorn --certfile=cert.pem --keyfile=key.pem --bind=0.0.0.0:443 app:app
```

## 📈 Capacidade e Performance

- **Participantes**: Até 2.500 simultâneos
- **Check-ins concorrentes**: Até 50 por minuto
- **Armazenamento**: ~100MB para 2.500 participantes completos
- **Memória RAM**: Mínimo 512MB, recomendado 1GB
- **CPU**: Funciona adequadamente com 1 vCPU

## 🆘 Solução de Problemas

### Problemas Comuns

#### 1. Erro de Importação de Módulos
```bash
# Verificar instalação
pip list | grep -E "(flask|sqlalchemy|qrcode)"

# Reinstalar dependências
pip install --force-reinstall -e .
```

#### 2. Erro de Banco de Dados
```bash
# Recriar banco
rm bundokai.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### 3. Problemas de QR Code
```bash
# Testar geração
python -c "from utils import generate_qr_code; print(len(generate_qr_code('TEST')))"
```

#### 4. Erros de Permissão
```bash
# Corrigir permissões
chmod -R 755 static/
mkdir -p logs && chmod 755 logs/
```

### Logs de Debug
```bash
# Ativar modo debug
export FLASK_DEBUG=True
export PYTHONPATH=.
python app.py

# Verificar logs detalhados
tail -f logs/app.log | grep ERROR
```

## 🤝 Contribuição

### Setup para Desenvolvimento
```bash
# Instalar dependências de desenvolvimento
pip install -e .[dev]

# Configurar pre-commit hooks
pre-commit install

# Executar testes antes do commit
pytest tests/ --cov=. --cov-fail-under=80
```

### Estrutura de Commits
```
feat: nova funcionalidade
fix: correção de bug  
docs: documentação
style: formatação
refactor: refatoração
test: testes
chore: tarefas de manutenção
```

## 📞 Suporte e Contato

**Desenvolvido por**: Leonardo Bora  
**Objetivo**: Substituir soluções comerciais caras mantendo funcionalidades essenciais  

### Recursos Adicionais
- [Documentação da API](docs/api.md)
- [Guia de Deploy](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Agents.md Reference](docs/agents.md)
