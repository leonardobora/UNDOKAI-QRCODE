from flask import Flask, render_template, jsonify, make_response, send_from_directory
import os

app = Flask(__name__)
app.secret_key = "test-secret-key"

@app.route('/')
def index():
    return render_template('user_index.html')

@app.route('/scanner')
def scanner():
    return render_template('test_scanner.html')

@app.route('/service-worker.js')
def service_worker():
    """Serve the service worker with correct content type"""
    response = make_response(send_from_directory('static/js', 'service-worker.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/api/validate_qr', methods=['POST'])
def validate_qr():
    """Mock API endpoint for testing"""
    return jsonify({
        'success': True,
        'participant': {
            'nome': 'Teste PWA',
            'email': 'teste@example.com',
            'departamento': 'TI'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)