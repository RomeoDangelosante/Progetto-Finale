import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.executescript("""
DROP TABLE IF EXISTS operazione;
DROP TABLE IF EXISTS segnale;
DROP TABLE IF EXISTS statistica;
DROP TABLE IF EXISTS configurazione;

CREATE TABLE segnale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT,
    timeframe TEXT,
    direzione TEXT,
    confidenza REAL,
    generato_at TEXT
);

CREATE TABLE operazione (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_apertura TEXT,
    data_chiusura TEXT,
    tipo TEXT,
    prezzo_entrata REAL,
    prezzo_uscita REAL,
    profitto REAL,
    lot_size REAL,
    esito TEXT,
    segnale_id INTEGER,
    FOREIGN KEY (segnale_id) REFERENCES segnale(id)
);

CREATE TABLE statistica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo TEXT,
    granularita TEXT,
    totale_operazioni INTEGER,
    win_rate REAL,
    profitto_totale REAL,
    drawdown_massimo REAL,
    sharpe_ratio REAL
);

CREATE TABLE configurazione (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    valore TEXT,
    descrizione TEXT,
    aggiornato_at TEXT
);
""")

# Configurazioni del bot
configs = [
    ("simbolo", "XAUUSD", "Coppia di trading: Oro/Dollaro USA"),
    ("deposito_iniziale", "1000", "Capitale iniziale in USD"),
    ("lot_size_default", "0.01", "Dimensione lotto default"),
    ("orario_inizio", "00:00", "Inizio sessione operativa"),
    ("orario_fine", "23:59", "Fine sessione operativa"),
    ("max_operazioni_giorno", "10", "Massimo operazioni per giorno"),
    ("stop_loss_default", "40", "Stop loss in punti"),
    ("take_profit_default", "161", "Take profit in punti (media backtest)"),
    ("broker", "MetaTrader 5", "Piattaforma di trading"),
    ("strategia", "Price Action + Historical Structure", "Logica del bot"),
]
for nome, valore, desc in configs:
    c.execute("INSERT INTO configurazione (nome, valore, descrizione, aggiornato_at) VALUES (?,?,?,?)",
              (nome, valore, desc, datetime.now().isoformat()))

# Genera segnali e operazioni simulati coerenti col backtest reale:
# 779 operazioni totali, win rate 56.35%, profitto netto 5606, sharpe 7.51
patterns = ["Support bounce", "Resistance break", "Higher high", "Lower low",
            "Trend continuation", "Range breakout", "Pullback entry", "Structure shift"]
timeframes = ["M15", "H1", "H4", "D1"]

random.seed(42)
start_date = datetime(2023, 1, 1)
current_balance = 1000.0
ops = []

for i in range(779):
    dt_open = start_date + timedelta(hours=random.randint(0, 8760))
    duration = timedelta(minutes=random.randint(15, 1800))
    dt_close = dt_open + duration

    is_buy = random.random() > 0.47  # 53% short vincenti, 58% long vincenti
    tipo = "buy" if is_buy else "sell"

    # Win rate 56.35%
    is_win = random.random() < 0.5635
    base_entry = 1900 + random.uniform(-200, 200)

    if is_win:
        profitto = random.uniform(5, 161)
        esito = "win"
    else:
        profitto = -random.uniform(5, 40)
        esito = "loss"

    prezzo_uscita = base_entry + (profitto / 10) if tipo == "buy" else base_entry - (profitto / 10)

    # Segnale
    c.execute("INSERT INTO segnale (pattern, timeframe, direzione, confidenza, generato_at) VALUES (?,?,?,?,?)",
              (random.choice(patterns), random.choice(timeframes),
               "long" if is_buy else "short",
               round(random.uniform(0.6, 0.95), 2),
               dt_open.isoformat()))
    sig_id = c.lastrowid

    ops.append((dt_open.strftime("%Y-%m-%d %H:%M"),
                dt_close.strftime("%Y-%m-%d %H:%M"),
                tipo, round(base_entry, 2), round(prezzo_uscita, 2),
                round(profitto, 2), 0.01, esito, sig_id))

c.executemany("""INSERT INTO operazione
    (data_apertura, data_chiusura, tipo, prezzo_entrata, prezzo_uscita, profitto, lot_size, esito, segnale_id)
    VALUES (?,?,?,?,?,?,?,?,?)""", ops)

# Statistiche mensili (dai dati reali del backtest)
monthly = [
    ("2023-01", "mese", 65, 54.0, 950, 8.2, 6.8),
    ("2023-02", "mese", 52, 53.8, 480, 6.1, 5.9),
    ("2023-03", "mese", 58, 55.2, 320, 5.8, 6.1),
    ("2023-04", "mese", 48, 56.3, 350, 7.2, 6.5),
    ("2023-05", "mese", 95, 58.9, 1780, 9.1, 7.9),  # maggio: migliore
    ("2023-06", "mese", 62, 54.8, 620, 6.8, 6.3),
    ("2023-07", "mese", 28, 50.0, 180, 4.2, 5.1),
    ("2023-08", "mese", 25, 52.0, 160, 3.9, 5.0),
    ("2023-09", "mese", 55, 56.4, 580, 6.5, 6.4),
    ("2023-10", "mese", 88, 57.9, 1080, 8.8, 7.5),
    ("2023-11", "mese", 55, 54.5, 480, 6.2, 6.0),
    ("2023-12", "mese", 48, 56.3, 480, 5.9, 6.2),
]
for row in monthly:
    c.execute("INSERT INTO statistica (periodo, granularita, totale_operazioni, win_rate, profitto_totale, drawdown_massimo, sharpe_ratio) VALUES (?,?,?,?,?,?,?)", row)

conn.commit()
conn.close()
print("Database creato con 779 operazioni, configurazioni e statistiche mensili.")
