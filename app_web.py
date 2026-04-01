import streamlit as st

USER = "marco"
PASS = "er@-1y6tio8934"

def login():
    st.title("Login")

    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Accedi"):
        if user == USER and password == PASS:
            st.session_state["logged"] = True
        else:
            st.error("Credenziali errate")

if "logged" not in st.session_state:
    st.session_state["logged"] = False

if not st.session_state["logged"]:
    login()
    st.stop()
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import tempfile
import os
import json
import pandas as pd

st.set_page_config(page_title="OFFICINA3D", layout="wide")

FILE_PREVENTIVI = "preventivi.json"
FILE_CLIENTI = "clienti.json"
COUNTER_FILE = "counter.txt"

def carica_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def salva_json(file, dati):
    with open(file, "w") as f:
        json.dump(dati, f, indent=4)

preventivi_db = carica_json(FILE_PREVENTIVI)
clienti_db = carica_json(FILE_CLIENTI)

# --- COUNTER ---
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        f.write("1")

with open(COUNTER_FILE, "r") as f:
    numero_preventivo = int(f.read())

# --- RESET ---
if st.button("🔄 Reset numerazione"):
    with open(COUNTER_FILE, "w") as f:
        f.write("1")
    st.success("Contatore resettato")

# --- HEADER ---
st.title("⚙ OFFICINA3D")

# --- INTESTAZIONE ---
col1, col2, col3 = st.columns(3)

with col1:
    logo_file = st.file_uploader("Logo", type=["png", "jpg"])

with col2:
    nome_azienda_pdf = st.text_input("Nome azienda", "OFFICINA3D")

with col3:
    autore = st.text_input("Creato da", "Marco")

# --- CLIENTI ---
st.sidebar.header("Cliente")

nomi_clienti = [c["nome"] for c in clienti_db]

cliente = st.sidebar.selectbox("Cliente esistente", [""] + nomi_clienti)
nuovo_cliente = st.sidebar.text_input("➕ Nuovo cliente")

if nuovo_cliente:
    cliente = nuovo_cliente

# --- COSTI ---
st.sidebar.header("Costi")

peso = st.sidebar.number_input("Peso (g)", 0.0)
filamento = st.sidebar.number_input("€/kg", 22.0)
ore = st.sidebar.number_input("Ore", 0.0)
macchina = st.sidebar.number_input("€/h", 1.2)

materiale = (peso / 1000) * filamento
costo_macchina = ore * macchina

# --- STATO MODIFICA ---
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# --- VOCI ---
if "voci" not in st.session_state:
    st.session_state.voci = []

st.sidebar.header("Voci lavorazione")

if st.sidebar.button("➕ Aggiungi voce"):
    st.session_state.voci.append({"desc": "", "qta": 1, "prezzo": 0.0})
    st.rerun()

totale_voci = 0

for i, v in enumerate(st.session_state.voci):
    v["desc"] = st.sidebar.text_input(f"Desc {i}", v["desc"], key=f"d{i}")
    v["qta"] = st.sidebar.number_input(f"Qta {i}", v["qta"], key=f"q{i}")
    v["prezzo"] = st.sidebar.number_input(f"Prezzo {i}", v["prezzo"], key=f"p{i}")

    tot = v["qta"] * v["prezzo"]
    totale_voci += tot

    if st.sidebar.button(f"❌ Rimuovi {i}", key=f"rem{i}"):
        st.session_state.voci.pop(i)
        st.rerun()

# --- CALCOLO ---
totale = materiale + costo_macchina + totale_voci

st.success(f"Totale: € {totale:.2f}")

# --- PREVIEW ---
st.subheader("Dettaglio preventivo")

st.write(f"Cliente: {cliente}")
st.write(f"Creato da: {autore}")
st.write(f"Materiale: € {materiale:.2f}")
st.write(f"Macchina: € {costo_macchina:.2f}")

if st.session_state.voci:
    df_preview = pd.DataFrame(st.session_state.voci)
    df_preview["totale"] = df_preview["qta"] * df_preview["prezzo"]
    st.table(df_preview)

# --- SALVA / MODIFICA ---
def salva_preventivo():
    global preventivi_db

    dati = {
        "numero": numero_preventivo if st.session_state.edit_index is None else preventivi_db[st.session_state.edit_index]["numero"],
        "data": datetime.now().strftime("%d/%m/%Y"),
        "cliente": cliente,
        "autore": autore,
        "totale": totale,
        "voci": st.session_state.voci,
        "peso": peso,
        "ore": ore
    }

    if st.session_state.edit_index is None:
        preventivi_db.append(dati)
    else:
        preventivi_db[st.session_state.edit_index] = dati

    salva_json(FILE_PREVENTIVI, preventivi_db)

    if cliente and cliente not in nomi_clienti:
        clienti_db.append({"nome": cliente})
        salva_json(FILE_CLIENTI, clienti_db)

    if st.session_state.edit_index is None:
        with open(COUNTER_FILE, "w") as f:
            f.write(str(numero_preventivo + 1))

    st.session_state.edit_index = None

# --- CARICA ---
def carica_preventivo(i):
    p = preventivi_db[i]
    st.session_state.voci = p["voci"]
    st.session_state.edit_index = i

# --- ELIMINA ---
def elimina_preventivo(i):
    preventivi_db.pop(i)
    salva_json(FILE_PREVENTIVI, preventivi_db)

# --- PDF ---
def genera_pdf():
    salva_preventivo()

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp.name, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h - 50, nome_azienda_pdf)

    c.setFont("Helvetica", 10)
    c.drawString(40, h - 80, f"Cliente: {cliente}")
    c.drawString(40, h - 95, f"Creato da: {autore}")

    y = h - 140

    for v in st.session_state.voci:
        tot = v["qta"] * v["prezzo"]
        c.drawString(40, y, f"{v['desc']} - € {tot:.2f}")
        y -= 15

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y - 20, f"TOTALE: € {totale:.2f}")

    c.save()
    return temp.name

# --- BOTTONI ---
colA, colB = st.columns(2)

with colA:
    if st.button("💾 Salva / Aggiorna"):
        salva_preventivo()
        st.success("Salvato!")

with colB:
    if st.button("📄 Genera PDF"):
        pdf = genera_pdf()
        with open(pdf, "rb") as f:
            st.download_button("Scarica PDF", f, "preventivo.pdf")

# --- STORICO ---
st.subheader("Storico preventivi")

if preventivi_db:
    df = pd.DataFrame(preventivi_db)
    st.dataframe(df)

    for i, p in enumerate(preventivi_db):
        col1, col2, col3 = st.columns([3,1,1])

        with col1:
            st.write(f"Preventivo {p['numero']} - {p['cliente']}")

            if p.get("voci"):
                df_voci = pd.DataFrame(p["voci"])
                df_voci["totale"] = df_voci["qta"] * df_voci["prezzo"]
                st.table(df_voci)

        with col2:
            if st.button("✏️ Modifica", key=f"edit{i}"):
                carica_preventivo(i)
                st.success("Caricato!")

        with col3:
            if st.button("🗑 Elimina", key=f"del{i}"):
                elimina_preventivo(i)
                st.rerun()

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Scarica CSV", csv, "archivio.csv")