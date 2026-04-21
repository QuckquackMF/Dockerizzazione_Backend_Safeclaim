from flask import Flask, request, jsonify
from datetime import datetime, UTC
import mysql.connector
import pymongo
from bson.objectid import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURAZIONE DATABASE ---

# MySQL (MariaDB)
MYSQL_CONFIG = {
    "host": "mysql",
    "user": "pythonuser",
    "password": "password123",
    "database": "gestione_assicurazioni"
}

def get_db_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

# MongoDB Atlas
MONGO_URI = "mongodb+srv://dbFakeClaim:xxx123%23%23@cluster0.zgw1jft.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_db = mongo_client["FakeClaim"]
    sinistri_col = mongo_db["Sinistri"]
    soccorso_col = mongo_db["Soccorso"]
    
    mongo_client.admin.command('ping')
    print("✅ Connessione a MongoDB Atlas riuscita!")
except Exception as e:
    print(f"❌ Errore connessione MongoDB: {e}")

# VEIOCLI 
@app.route('/veicoli', methods=['GET'])
@app.route('/veicoli/<int:id>', methods=['GET'])
def get_veicoli(id=None):
    """GET Unificata: recupera tutti i veicoli o uno specifico per ID"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if id:
            cursor.execute("SELECT * FROM Veicolo WHERE id = %s", (id,))
            veicolo = cursor.fetchone()
            if not veicolo: return jsonify({"error": "Veicolo non trovato"}), 404
            return jsonify(veicolo), 200
        else:
            cursor.execute("SELECT * FROM Veicolo")
            return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/veicoli-utente/<int:automobilista_id>', methods=['GET'])
def get_veicoli_utente(automobilista_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Veicolo WHERE automobilista_id = %s", (automobilista_id,))
        veicoli = cursor.fetchall()
        return jsonify(veicoli), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    # Mantenuta porta 6000 come da tua ultima riga
    app.run(host='0.0.0.0', port=7000, debug=True)