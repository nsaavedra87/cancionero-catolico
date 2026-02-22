import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# --- MANEJO SEGURO DE OCR ---
try:
    import pytesseract
except ImportError:
    st.error("Instalando componentes de lectura de imagen... Por favor, recarga en 1 minuto.")

# --- CONFIGURACIÓN DE BASE DE DATOS LOCAL ---
DB_FILE = "cancionero.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Temática", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN MUSICAL ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def transponer_texto(texto, semitonos):
    if semitonos == 0 or not texto: return texto
    # Patrón para detectar acordes comunes (Mayores, menores, 7mas, etc.)
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        # Normalizar bemoles para la lógica de la lista NOTAS
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        
        resto = acorde[len(nota_original):]
        if nota_base in NOTAS:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            return nueva_nota + resto
        return acorde
    
    return re.sub(patron, reemplazar, texto)

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="ChordMaster Pro OCR", page_icon="🎸", layout="wide")

# Inicializar Setlist en sesión
if 'setlist' not in st.session_state:
    st.session_state.setlist = []

# --- SIDEBAR: ESTILO Y NAVEGACIÓN ---
st.sidebar.title("🎨 Personalización")
color_bg = st.sidebar.color_picker("Color de Fondo", "#1E1E1E")
color_txt = st.sidebar.color_picker("Color de Texto/Acordes", "#00FF00")
f_size = st.sidebar.slider("Tamaño de Fuente", 14, 40, 22)
fuente_opcion = st.sidebar.selectbox("Fuente", ["monospace", "serif", "sans-serif"])

st.sidebar.divider()
menu = st.sidebar.radio("Menú Principal", ["Cantar (Modo Live)", "Añadir por Foto 📸", "Registro Manual 📝", "Mi Setlist 📋"])

df = cargar_datos()

# --- MÓDULO: AÑADIR POR FOTO (OCR) ---
if menu == "Añadir por Foto 📸":
    st.header("📸 Escanear Letra Manuscrita")
    st.info("Usa la cámara para capturar una letra. Luego edítala para añadir los acordes.")
    
    img_file = st.camera_input("Capturar Hoja")
    if img_file:
        img = Image.open(img_file)
        with st.spinner("Procesando imagen con OCR..."):
            try:
                # Extraer texto usando Tesseract
                texto_ocr = pytesseract.image_to_string(img, lang='spa')
                st.subheader("Texto Extraído")
                
                with st.form("confirmar_foto"):
                    t_foto = st.text_input("Título de la canción")
                    a_foto = st.text_input("Autor")
                    letra_editada = st.text_area("Revisa la letra y añade acordes:", texto_ocr, height=300)
                    if st.form_submit_button("Guardar en mi Cancionero"):
                        if t_foto and letra_editada:
                            nueva = pd.DataFrame([[t_foto, a_foto, "Escaner", letra_editada]], columns=df.columns)
                            df = pd.concat([df, nueva], ignore_index=True)
                            guardar_datos(df)
                            st.success("¡Canción guardada!")
                        else:
                            st.error("Falta título o letra.")
            except Exception as e:
                st.error(f"Error técnico: {e}. Asegúrate de tener 'packages.txt' configurado.")

# --- MÓDULO: REGISTRO MANUAL ---
elif menu == "Registro Manual 📝":
    st.header("📝 Nueva Canción")
    with st.form("registro_manual"):
        c1, c2 = st.columns(2)
        t = c1.text_input("Título")
        a = c2.text_input("Autor")
        tem = st.selectbox("Categoría", ["Rock", "Pop", "Alabanza", "Balada", "Otro"])
        let = st.text_area("Letra y Acordes (Coloca los acordes sobre las sílabas)", height=300)
        if st.form_submit_button("Guardar Canción"):
            if t and let:
                nueva = pd.DataFrame([[t, a, tem, let]], columns=df.columns)
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success("¡Añadida al repertorio!")

# --- MÓDULO: CANTAR (LIVE) ---
elif menu == "Cantar (Live)":
    st.header("🎤 Visor de Interpretación")
    if not df.empty:
        busqueda = st.text_input("🔍 Buscar canción...")
        filtro = df[df['Título'].str.contains(busqueda, case=False, na=False)]
        
        if not filtro.empty:
            sel = st.selectbox("Selecciona para cantar:", filtro['Título'])
            cancion = df[df['Título'] == sel].iloc[0]
            
            # Controles de Escenario
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                transp = st.number_input("Transportar (Semitonos)", -6, 6, 0)
            with col2:
                v_scroll = st.slider("Velocidad de Scroll", 0, 10, 0)
            with col3:
                st.write("")
                if st.button("⭐ Añadir al Setlist"):
                    st.session_state.setlist.append(sel)
                    st.toast("¡Añadido!")

            # Lógica de Auto-scroll JS
            if v_scroll > 0:
                # Intervalo dinámico basado en slider
                ms = 100 / v_scroll
                st.components.v1.html(f"<script>setInterval(()=>window.scrollBy(0,1),{ms});</script>", height=0)

            # Renderizado de la Canción con Estilos
            letra_final = transponer_texto(cancion['Letra'], transp)
            
            st.markdown(f"""
                <div style="
                    background-color: {color_bg}; 
                    color: {color_txt}; 
                    font-size: {f_size}px; 
                    font-family: {fuente_opcion}; 
                    padding: 40px; 
                    border-radius: 20px; 
                    line-height: 1.8; 
                    white-space: pre-wrap;
                    border: 1px solid #444;
                ">
                <h1 style="color: white; margin-bottom: 0;">{cancion['Título']}</h1>
                <small style="color: #888;">{cancion['Autor']} | {cancion['Temática']}</small>
                <hr style="border-color: #444;">
                {letra_final}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Tu biblioteca está vacía. Ve a 'Registro Manual' o 'Añadir por Foto'.")

# --- MÓDULO: SETLIST ---
elif menu == "Mi Setlist 📋":
    st.header("📋 Setlist del Evento")
    if st.session_state.setlist:
        for i, cancion_nombre in enumerate(st.session_state.setlist):
            st.subheader(f"{i+1}. {cancion_nombre}")
        
        if st.button("🗑️ Vaciar Setlist"):
            st.session_state.setlist = []
            st.rerun()
    else:
        st.info("No has añadido canciones a la lista de hoy.")
