import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN Y DICCIONARIO DE PIANO ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

# Diccionario de digitación (Notas que componen cada acorde)
PIANO_DICT = {
    "C": "Do - Mi - Sol", "Cm": "Do - Mib - Sol", "C7": "Do - Mi - Sol - Sib",
    "C#": "Do# - Fa - Sol#", "C#m": "Do# - Mi - Sol#", "Db": "Reb - Fa - Lab",
    "D": "Re - Fa# - La", "Dm": "Re - Fa - La", "D7": "Re - Fa# - La - Do",
    "D#": "Re# - Sol - La#", "Eb": "Mib - Sol - Sib", "Ebm": "Mib - Solb - Sib",
    "E": "Mi - Sol# - Si", "Em": "Mi - Sol - Si", "E7": "Mi - Sol# - Si - Re",
    "F": "Fa - La - Do", "Fm": "Fa - Lab - Do", "F7": "Fa - La - Do - Mib",
    "F#": "Fa# - La# - Do#", "F#m": "Fa# - La - Do#", "Gb": "Solb - Sib - Reb",
    "G": "Sol - Si - Re", "Gm": "Sol - Sib - Re", "G7": "Sol - Si - Re - Fa",
    "G#": "Sol# - Do - Re#", "Ab": "Lab - Do - Mib", "Abm": "Lab - Dob - Mib",
    "A": "La - Do# - Mi", "Am": "La - Do - Mi", "A7": "La - Do# - Mi - Sol",
    "A#": "La# - Re - Fa#", "Bb": "Sib - Re - Fa", "Bbm": "Sib - Reb - Fa",
    "B": "Si - Re# - Fa#", "Bm": "Si - Re - Fa#", "B7": "Si - Re# - Fa# - La"
}

NOTAS_BASE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def cargar_datos():
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

def renderizar_cifrado(texto_marcado, color_acorde):
    if not texto_marcado: return ""
    lineas = texto_marcado.split('\n')
    resultado_html = ""
    for linea in lineas:
        if "[" in linea:
            partes = re.split(r'(\[[^\]]+\])', linea)
            linea_acordes = ""
            linea_letra = ""
            for parte in partes:
                if parte.startswith("[") and parte.endswith("]"):
                    acorde = parte[1:-1]
                    linea_acordes += f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
                else:
                    linea_letra += parte
                    linea_acordes += "&nbsp;" * len(parte)
            resultado_html += f'<div style="margin-bottom:12px;"><div style="white-space:pre; line-height:1;">{linea_acordes}</div><div style="white-space:pre; line-height:1;">{linea_letra}</div></div>'
        else:
            resultado_html += f'<div style="white-space:pre; margin-bottom:12px;">{linea}</div>'
    return resultado_html

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Piano Edition", layout="wide")

# JS para insertar acorde en el cursor
st.markdown("""
    <script>
    function insertarAcorde(acorde) {
        const textArea = window.parent.document.querySelector('textarea');
        if (!textArea) return;
        const start = textArea.selectionStart;
        const end = textArea.selectionEnd;
        const text = textArea.value;
        textArea.value = text.substring(0, start) + "[" + acorde + "]" + text.substring(end);
        textArea.selectionStart = textArea.selectionEnd = start + acorde.length + 2;
        textArea.focus();
        textArea.dispatchEvent(new Event('input', { bubbles: true }));
    }
    </script>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .stTextArea textarea { font-family: 'JetBrains Mono', monospace !important; }
    .visor-final { background: #121212; padding: 25px; border-radius: 15px; border: 1px solid #333; }
    /* Estilo para los botones de acordes con ayuda */
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()

# --- PANEL DE EDICIÓN ---
menu = st.sidebar.selectbox("Menú", ["🏠 Cantar", "➕ Editor Pro", "⚙️ Categorías"])
c_chord = st.sidebar.color_picker("Color Acordes", "#00E676")
f_size = st.sidebar.slider("Tamaño Fuente", 15, 45, 22)

if menu == "➕ Editor Pro":
    st.header("🎹 Editor Musical con Guía de Piano")
    
    col_ed, col_pre = st.columns([1, 1])
    
    with col_ed:
        titulo = st.text_input("Título de la canción")
        
        # --- TECLADO DE ACORDES COMPLETO ---
        st.write("### 🎹 Teclado de Acordes")
        st.caption("Pasa el mouse sobre el acorde para ver las notas del piano.")
        
        tab_may, tab_min, tab_7 = st.tabs(["Mayores", "Menores", "Séptimas"])
        
        with tab_may:
            cols = st.columns(6)
            for i, nota in enumerate(NOTAS_BASE):
                info = PIANO_DICT.get(nota, "Desconocido")
                if cols[i % 6].button(nota, help=f"Piano: {info}", key=f"m_{nota}"):
                    st.components.v1.html(f"<script>insertarAcorde('{nota}');</script>", height=0)
        
        with tab_min:
            cols = st.columns(6)
            for i, nota in enumerate(NOTAS_BASE):
                nm = f"{nota}m"
                info = PIANO_DICT.get(nm, "Desconocido")
                if cols[i % 6].button(nm, help=f"Piano: {info}", key=f"min_{nota}"):
                    st.components.v1.html(f"<script>insertarAcorde('{nm}');</script>", height=0)

        with tab_7:
            cols = st.columns(6)
            for i, nota in enumerate(NOTAS_BASE):
                n7 = f"{nota}7"
                info = PIANO_DICT.get(n7, "Desconocido")
                if cols[i % 6].button(n7, help=f"Piano: {info}", key=f"7_{nota}"):
                    st.components.v1.html(f"<script>insertarAcorde('{n7}');</script>", height=0)

        letra_input = st.text_area("Letra (Toca una palabra y luego un acorde arriba):", height=350)

    with col_pre:
        st.subheader("👀 Vista Previa")
        if letra_input:
            html = renderizar_cifrado(letra_input, c_chord)
            st.markdown(f'<div class="visor-final" style="font-size:{f_size}px; font-family:\'JetBrains Mono\', monospace; color:white;">{html}</div>', unsafe_allow_html=True)
            if st.button("💾 Guardar Canción", use_container_width=True):
                nueva = pd.DataFrame([[titulo, "Autor", "General", letra_input]], columns=df.columns)
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success("¡Guardada!")

elif menu == "🏠 Cantar":
    if not df.empty:
        sel = st.selectbox("Canción:", df['Título'])
        c = df[df['Título'] == sel].iloc[0]
        st.markdown(f'<div class="visor-final" style="font-size:{f_size}px; font-family:\'JetBrains Mono\', monospace; color:white;">{renderizar_cifrado(c["Letra"], c_chord)}</div>', unsafe_allow_html=True)
