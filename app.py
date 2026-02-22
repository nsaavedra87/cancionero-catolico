import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN Y DICCIONARIO ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

# Diccionario de notas para iluminar el piano (0=Do, 1=Do#, etc.)
PIANO_MAP = {
    "C": [0, 4, 7], "Cm": [0, 3, 7], "C7": [0, 4, 7, 10],
    "C#": [1, 5, 8], "C#m": [1, 4, 8],
    "D": [2, 6, 9], "Dm": [2, 5, 9], "D7": [2, 6, 9, 0],
    "D#": [3, 7, 10], "Eb": [3, 7, 10],
    "E": [4, 8, 11], "Em": [4, 7, 11], "E7": [4, 8, 11, 2],
    "F": [5, 9, 0], "Fm": [5, 8, 0], "F7": [5, 9, 0, 3],
    "F#": [6, 10, 1], "F#m": [6, 9, 1],
    "G": [7, 11, 2], "Gm": [7, 10, 2], "G7": [7, 11, 2, 5],
    "G#": [8, 0, 3], "Ab": [8, 0, 3],
    "A": [9, 1, 4], "Am": [9, 0, 4], "A7": [9, 1, 4, 7],
    "A#": [10, 2, 5], "Bb": [10, 2, 5],
    "B": [11, 3, 6], "Bm": [11, 2, 6], "B7": [11, 3, 6, 9]
}

NOTAS_BASE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def cargar_datos():
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- FUNCIÓN DEL TECLADO VISUAL (HTML/CSS) ---
def dibujar_piano(notas_activas):
    # Definición de teclas (blancas y negras)
    teclas = [
        (0, "white"), (1, "black"), (2, "white"), (3, "black"), (4, "white"),
        (5, "white"), (6, "black"), (7, "white"), (8, "black"), (9, "white"),
        (10, "black"), (11, "white")
    ]
    
    html_piano = '<div style="display: flex; position: relative; height: 120px; width: 320px; background: #222; padding: 10px; border-radius: 10px;">'
    
    offset_izq = 0
    for nota, color in teclas:
        is_active = nota in notas_activas
        bg_color = "#00FF00" if is_active else ("white" if color == "white" else "black")
        
        if color == "white":
            html_piano += f'<div style="width: 40px; height: 100%; background: {bg_color}; border: 1px solid #ccc; z-index: 1;"></div>'
        else:
            html_piano += f'<div style="width: 24px; height: 60%; background: {bg_color}; border: 1px solid #000; position: absolute; left: {offset_izq - 12}px; z-index: 2;"></div>'
        
        if color == "white": offset_izq += 40

    html_piano += '</div>'
    return html_piano

# --- MOTOR DE RENDERIZADO DE TEXTO ---
def renderizar_cifrado(texto_marcado, color_acorde):
    if not texto_marcado: return ""
    lineas = texto_marcado.split('\n')
    resultado_html = ""
    for linea in lineas:
        if "[" in linea:
            partes = re.split(r'(\[[^\]]+\])', linea)
            l_acordes = ""
            l_letra = ""
            for parte in partes:
                if parte.startswith("[") and parte.endswith("]"):
                    acorde = parte[1:-1]
                    l_acordes += f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
                else:
                    l_letra += parte
                    l_acordes += "&nbsp;" * len(parte)
            resultado_html += f'<div style="margin-bottom:8px;"><div style="white-space:pre; line-height:1;">{l_acordes}</div><div style="white-space:pre; line-height:1;">{l_letra}</div></div>'
        else:
            resultado_html += f'<div style="white-space:pre; margin-bottom:8px;">{linea}</div>'
    return resultado_html

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Piano Pro", layout="wide")

# JavaScript para inserción en cursor
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

if 'acorde_actual' not in st.session_state: st.session_state.acorde_actual = "C"

df = cargar_datos()

# --- SIDEBAR ---
menu = st.sidebar.selectbox("Menú", ["🏠 Cantar", "➕ Editor Pro", "📂 Biblioteca"])
c_chord = st.sidebar.color_picker("Color Acordes", "#00FF00")
f_size = st.sidebar.slider("Tamaño Fuente", 15, 50, 22)

if menu == "➕ Editor Pro":
    st.header("🎹 Editor con Guía de Piano Activa")
    
    col_ed, col_pre = st.columns([1, 1])
    
    with col_ed:
        titulo = st.text_input("Título")
        
        # VISUALIZADOR DE PIANO
        st.write("### 🎹 Digitación")
        notas_a_iluminar = PIANO_MAP.get(st.session_state.acorde_actual, [])
        st.markdown(dibujar_piano(notas_a_iluminar), unsafe_allow_html=True)
        st.caption(f"Acorde: **{st.session_state.acorde_actual}** | Notas: {', '.join([str(n) for n in notas_a_iluminar])}")

        # BOTONES DE ACORDES
        t1, t2, t3 = st.tabs(["Mayores", "Menores", "7mas"])
        for tab, sufijo in zip([t1, t2, t3], ["", "m", "7"]):
            with tab:
                cols = st.columns(6)
                for i, n in enumerate(NOTAS_BASE):
                    nombre_ac = f"{n}{sufijo}"
                    if cols[i % 6].button(nombre_ac, key=f"btn_{nombre_ac}"):
                        st.session_state.acorde_actual = nombre_ac
                        st.components.v1.html(f"<script>insertarAcorde('{nombre_ac}');</script>", height=0)
                        st.rerun() # Para actualizar el piano inmediatamente

        letra_input = st.text_area("Letra (Ancla los acordes tocando los botones):", height=300)

    with col_pre:
        st.subheader("👀 Vista Previa")
        if letra_input:
            html = renderizar_cifrado(letra_input, c_chord)
            st.markdown(f'<div style="background:#121212; padding:20px; border-radius:10px; font-family:\'JetBrains Mono\', monospace; color:white; font-size:{f_size}px;">{html}</div>', unsafe_allow_html=True)
            if st.button("💾 GUARDAR", use_container_width=True):
                nueva = pd.DataFrame([[titulo, "Desconocido", "General", letra_input]], columns=df.columns)
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success("¡Guardada!")

elif menu == "🏠 Cantar":
    if not df.empty:
        sel = st.selectbox("Canción:", df['Título'])
        c = df[df['Título'] == sel].iloc[0]
        st.markdown(f'<div style="background:#121212; padding:20px; border-radius:10px; font-family:\'JetBrains Mono\', monospace; color:white; font-size:{f_size}px;">{renderizar_cifrado(c["Letra"], c_chord)}</div>', unsafe_allow_html=True)
