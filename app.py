from flask import Flask, render_template, jsonify
import sqlite3
import os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    db = get_db()
    stats = {
        "totale_operazioni": db.execute("SELECT COUNT(*) FROM operazione").fetchone()[0],
        "profitto_netto": db.execute("SELECT ROUND(SUM(profitto),2) FROM operazione").fetchone()[0],
        "win_rate": db.execute("SELECT ROUND(100.0*SUM(CASE WHEN esito='win' THEN 1 ELSE 0 END)/COUNT(*),2) FROM operazione").fetchone()[0],
        "sharpe": 7.51,
        "deposito": 1000,
    }
    db.close()
    return render_template("index.html", stats=stats)

@app.route("/come-funziona")
def come_funziona():
    db = get_db()
    patterns = db.execute("""
        SELECT s.pattern, COUNT(*) as totale,
               ROUND(100.0*SUM(CASE WHEN o.esito='win' THEN 1 ELSE 0 END)/COUNT(*),1) as win_rate
        FROM operazione o JOIN segnale s ON o.segnale_id = s.id
        GROUP BY s.pattern ORDER BY totale DESC
    """).fetchall()
    db.close()
    return render_template("come-funziona.html", patterns=patterns)

@app.route("/api")
def api_page():
    return render_template("api.html")

@app.route("/infrastruttura")
def infrastruttura():
    db = get_db()
    configs = db.execute("SELECT * FROM configurazione").fetchall()
    db.close()
    return render_template("infrastruttura.html", configs=configs)

@app.route("/processi")
def processi():
    db = get_db()
    stats_mensili = db.execute("SELECT * FROM statistica WHERE granularita='mese' ORDER BY periodo").fetchall()
    db.close()
    return render_template("processi.html", stats_mensili=stats_mensili)

@app.route("/backtest")
def backtest():
    db = get_db()
    ops = db.execute("SELECT * FROM operazione ORDER BY data_apertura LIMIT 200").fetchall()
    stats_mensili = db.execute("SELECT * FROM statistica WHERE granularita='mese' ORDER BY periodo").fetchall()
    db.close()
    return render_template("backtest.html", operazioni=ops, stats_mensili=stats_mensili)

# API JSON per i grafici
@app.route("/api/profitto-cumulativo")
def profitto_cumulativo():
    db = get_db()
    rows = db.execute("SELECT data_apertura, profitto FROM operazione ORDER BY data_apertura").fetchall()
    db.close()
    cumul = 0
    result = []
    for i, r in enumerate(rows):
        cumul += r["profitto"]
        if i % 5 == 0:  # ogni 5 operazioni per alleggerire il grafico
            result.append({"x": i, "y": round(cumul, 2), "data": r["data_apertura"][:10]})
    return jsonify(result)

@app.route("/api/stats-mensili")
def stats_mensili():
    db = get_db()
    rows = db.execute("SELECT periodo, profitto_totale, win_rate FROM statistica WHERE granularita='mese' ORDER BY periodo").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(debug=True)
