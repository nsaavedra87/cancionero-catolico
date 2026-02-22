import streamlit as st
import pandas as pd
import os
import re
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(titulo, autor, letra, color_acorde_hex):
    pdf = FPDF()
    pdf.add_page()
    
    # Título y Autor
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo.upper(), ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Autor: {autor}", ln=True, align='C')
    pdf.ln(10)
    
    # Letra y Acordes (Usamos Courier para mantener alineación monoespaciada)
    pdf.set_font("Courier", '', 12)
    
    # Convertir Hex a RGB para el PDF
    h = color_acorde_hex.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    lineas = letra.split('\n')
    for linea in lineas:
        # Detectar si es una línea de acordes (heurística simple)
        es_acorde = re.search(r'\b[A-G][#bmM79]*\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#bmM79]*\b', linea)
        
        if es_acorde:
            pdf.set_text_color(rgb[0], rgb[1], rgb[2])
            pdf.set_font("Courier", 'B', 12)
        else:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Courier", '', 12)
            
        pdf.cell(0, 6, linea, ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- MOTOR DE RENDERIZADO ESTRICTO ---
def procesar_texto_estricto(texto, color_acorde):
    if not texto: return ""
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?\b"
    
    def reemplazar(match):
        acorde = match.group(0)
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
    
    lineas = texto.split('\n')
    lineas_procesadas = []
    for linea in lineas:
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue
        linea_color = re.sub(patron, reemplazar, linea)
        linea_final = linea_color.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", page_icon="🎸", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 16px !important; background-color: #000 !important; color: #ddd !important; }
    .visor-musical { border-radius: 8px; padding: 20px; background-color: #121212; border: 1px solid #333; font-family: 'JetBrains Mono', monospace !important; line-height: 1.2; overflow-x: auto; color: white; }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster PDF")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar", "➕ Agregar / Importar", "📂 Exportar PDF"])
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Letra", 12, 45, 20)

# --- MÓDULO: AGREGAR ---
if menu == "➕ Agregar / Importar":
    st.header("➕ Cargar Canción")
    archivo_subido = st.file_uploader("Subir .txt", type=["txt"])
    if archivo_subido:
        st.session_state.texto_temp = archivo_subido.read().decode("utf-8")
    
    if 'texto_temp' not in st.session_state: st.session_state.texto_temp = ""

    titulo_n = st.text_input("Título")
    letra_n = st.text_area("Editor:", value=st.session_state.texto_temp, height=400)
    
    if letra_n:
        st.subheader("👀 Vista Previa")
        preview_html = procesar_texto_estricto(letra_n, c_chord)
        st.markdown(f'<div class="visor-musical" style="font-size:{f_size}px;">{preview_html}</div>', unsafe_allow_html=True)

        if st.button("💾 GUARDAR", use_container_width=True):
            nueva_fila = pd.DataFrame([[titulo_n, "Anon", "General", letra_n]], columns=df.columns)
            df = pd.concat([df, nueva_fila], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!")

# --- MÓDULO: EXPORTAR PDF ---
elif menu == "📂 Exportar PDF":
    st.header("📂 Generar Cancionero PDF")
    if not df.empty:
        sel_export = st.selectbox("Selecciona la canción para el PDF:", df['Título'])
        data_exp = df[df['Título'] == sel_export].iloc[0]
        
        if st.button("🚀 Generar y Descargar PDF"):
            pdf_bytes = generar_pdf(data_exp['Título'], data_exp['Autor'], data_exp['Letra'], c_chord)
            b64 = base64.b64encode(pdf_bytes).decode('latin-1')
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{sel_export}.pdf" style="padding:20px; background-color:green; color:white; text-decoration:none; border-radius:5px;">⬇️ Descargar Archivo PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("No hay canciones para exportar.")

# --- MÓDULO: CANTAR ---
elif menu == "🏠 Cantar":
    if not df.empty:
        sel_c = st.selectbox("Canción:", df['Título'])
        data_c = df[df['Título'] == sel_c].iloc[0]
        final_html = procesar_texto_estricto(data_c['Letra'], c_chord)
        st.markdown(f'<div class="visor-musical" style="font-size:{f_size}px;">{final_html}</div>', unsafe_allow_html=True)
