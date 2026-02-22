import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

# --- FUNCIONES DE DATOS ---
def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if df.empty:
            return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])
        return df
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    if os.path.exists(CAT_FILE):
        return pd.read_csv(CAT_FILE)['Nombre'].tolist()
    return ["General", "Alabanza", "Rock", "Pop"]

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

def guardar_categorias(lista):
    pd.DataFrame(lista, columns=['Nombre']).to_csv(CAT_FILE, index=False)

# --- LÓGICA MUSICAL (TRANSPOSICIÓN) ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
def transponer_texto(texto, semitonos):
    if semitonos == 0 or not texto: return texto
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        resto = acorde[len(nota_original):]
        if nota_base in NOTAS:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            return nueva_nota + resto
        return acorde
    return re.sub(patron, reemplazar, texto)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro v2", page_icon="🎸", layout="wide")

# Fuentes adicionales y estilos CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Roboto+Slab&family=Montserrat:wght@700&display=swap');
    .main { background-color: #0e1117; }
    .stButton>button { border-radius: 20px; text-transform: uppercase; font-weight: bold; }
    .song-card { border: 1px solid #333; padding: 20px; border-radius: 15px; background: #161b22; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar sesión
if 'setlist' not in st.session_state: st.session_state.setlist = []

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR MEJORADO ---
st.sidebar.title("🎸 ChordMaster Pro")
menu = st.sidebar.selectbox("Menú Principal", 
    ["🏠 Inicio / Cantar", "📸 Importar por Foto", "📝 Registro Manual", "⚙️ Gestionar Categorías", "📋 Mi Setlist"])

st.sidebar.divider()
st.sidebar.subheader("🎨 Personalización Visual")
c_bg = st.sidebar.color_picker("Color de Fondo", "#1e1e1e")
c_txt = st.sidebar.color_picker("Color de Texto", "#00ff00")
f_size = st.sidebar.slider("Tamaño", 16, 40, 22)
f_family = st.sidebar.selectbox("Fuente Musical", 
    ["'JetBrains Mono', monospace", "'Roboto Slab', serif", "'Courier New', Courier", "sans-serif"])

# --- MÓDULO: GESTIÓN DE CATEGORÍAS ---
if menu == "⚙️ Gestionar Categorías":
    st.header("⚙️ Configuración de Categorías")
    nueva_cat = st.text_input("Nombre de la nueva categoría")
    if st.button("➕ Crear Categoría"):
        if nueva_cat and nueva_cat not in categorias:
            categorias.append(nueva_cat)
            guardar_categorias(categorias)
            st.success(f"Categoría '{nueva_cat}' creada.")
            st.rerun()
    
    st.divider()
    st.subheader("Categorías Actuales")
    for c in categorias:
        st.text(f"• {c}")

# --- MÓDULO: REGISTRO MANUAL ---
elif menu == "📝 Registro Manual":
    st.header("📝 Nueva Canción")
    with st.form("reg"):
        col1, col2 = st.columns(2)
        t = col1.text_input("Título")
        a = col2.text_input("Autor")
        cat = st.selectbox("Categoría", categorias)
        let = st.text_area("Letra y Acordes", height=300)
        if st.form_submit_button("Guardar Canción"):
            nueva = pd.DataFrame([[t, a, cat, let]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!")

# --- MÓDULO: IMPORTAR POR FOTO ---
elif menu == "📸 Importar por Foto":
    st.header("📸 Escáner OCR")
    try:
        import pytesseract
        img_file = st.camera_input("Capturar Hoja")
        if img_file:
            img = Image.open(img_file)
            with st.spinner("Leyendo..."):
                texto = pytesseract.image_to_string(img, lang='spa')
                t_f = st.text_input("Título")
                a_f = st.text_input("Autor")
                c_f = st.selectbox("Categoría", categorias)
                let_f = st.text_area("Letra detectada (Edita los acordes):", texto, height=300)
                if st.button("Guardar Escaneo"):
                    nueva = pd.DataFrame([[t_f, a_f, c_f, let_f]], columns=df.columns)
                    df = pd.concat([df, nueva], ignore_index=True)
                    guardar_datos(df)
                    st.success("¡Importado!")
    except:
        st.error("OCR no disponible. Verifica 'packages.txt'.")

# --- MÓDULO: INICIO / FILTRADO ---
elif menu == "🏠 Inicio / Cantar":
    st.header("🎶 Biblioteca Musical")
    
    # FILTROS EN PANTALLA PRINCIPAL
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        busq = st.text_input("🔍 Buscar por título o autor")
    with col_f2:
        cat_filtro = st.multiselect("🏷️ Filtrar por Categoría", categorias)

    # Lógica de filtrado
    df_f = df.copy()
    if busq:
        df_f = df_f[df_f['Título'].str.contains(busq, case=False) | df_f['Autor'].str.contains(busq, case=False)]
    if cat_filtro:
        df_f = df_f[df_f['Categoría'].isin(cat_filtro)]

    if not df_f.empty:
        seleccion = st.selectbox("Selecciona para abrir visor:", df_f['Título'])
        c_data = df_f[df_f['Título'] == seleccion].iloc[0]
        
        st.divider()
        
        # Panel Live
        c1, c2, c3 = st.columns(3)
        transp = c1.number_input("Semitonos", -6, 6, 0)
        scroll = c2.slider("Auto-Scroll", 0, 10, 0)
        if c3.button("⭐ Añadir al Setlist", use_container_width=True):
            st.session_state.setlist.append(seleccion)
            st.toast("Añadida")

        if scroll > 0:
            st.components.v1.html(f"<script>setInterval(()=>window.scrollBy(0,1),{100/scroll});</script>", height=0)

        # Visor Estilizado
        letra_f = transponer_texto(c_data['Letra'], transp)
        st.markdown(f"""
            <div style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; 
            font-family:{f_family}; padding:40px; border-radius:20px; 
            line-height:1.7; white-space:pre-wrap; border: 1px solid #444; box-shadow: 0px 10px 30px rgba(0,0,0,0.5);">
            <h1 style="color:white; font-family:'Montserrat', sans-serif; margin:0;">{c_data['Título']}</h1>
            <p style="color:#888;">{c_data['Autor']} | <span style="color:#555;">{c_data['Categoría']}</span></p>
            <hr style="border-color:#333;">
            {letra_f}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No hay canciones que coincidan con los filtros.")

# --- MÓDULO: SETLIST ---
elif menu == "📋 Mi Setlist":
    st.header("📋 Lista de Hoy")
    if st.session_state.setlist:
        for i, s in enumerate(st.session_state.setlist):
            st.subheader(f"{i+1}. {s}")
        if st.button("Vaciar Setlist"):
            st.session_state.setlist = []
            st.rerun()
    else:
        st.info("Tu setlist está vacío.")
