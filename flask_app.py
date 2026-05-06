from flask import Flask
from flask_cors import CORS

from routes.signal_routes import signal_bp
from routes.reliability_routes import reliability_bp
from routes.file_routes import file_bp
from routes.crypto_routes import crypto_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(signal_bp)
app.register_blueprint(reliability_bp)
app.register_blueprint(file_bp)
app.register_blueprint(crypto_bp)

if __name__ == '__main__':
    print("🚀 Server berjalan di http://0.0.0.0:5632")
    app.run(host='0.0.0.0', port=5632, debug=True)
