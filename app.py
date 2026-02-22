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
        return df if not df.empty else pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    if os.path.exists(CAT_FILE):
        return pd.read_csv(CAT_FILE)['Nombre'].tolist()
    return ["General", "Alabanza", "Rock", "Pop"]

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

def guardar_categorias(lista):
    pd.DataFrame(lista, columns=['Nombre']).to_csv(CAT_FILE, index=False)

# --- LÓGICA MUSICAL ---
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
st.set_page_config(page_title="ChordMaster Ultra", page_icon="🎸", layout="wide")

# JS para Pantalla Completa y CSS Premium
st.markdown("""
    <script>
    function toggleFullScreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
    </script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Roboto+Slab&family=Montserrat:wght@700&display=swap');
    
    /* Ocultar elementos innecesarios en modo presentación */
    [data-testid="stHeader"] { visibility: hidden; }
    
    .visor-container {
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
        border: 1px solid #444;
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)

if 'setlist' not in st.session_state: st.session_state.setlist = []

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster Ultra")
menu = st.sidebar.selectbox("Menú", ["🏠 Cantar / Vivo", "📸 Importar Foto", "📝 Registro Manual", "⚙️ Categorías", "📋 Setlist"])

st.sidebar.divider()
st.sidebar.subheader("🎨 Estilo Escenario")
c_bg = st.sidebar.color_picker("Fondo", "#121212")
c_txt = st.sidebar.color_picker("Texto", "#00FF00")
f_size = st.sidebar.slider("Tamaño", 18, 45, 24)
f_family = st.sidebar.selectbox("Fuente", ["'JetBrains Mono', monospace", "'Roboto Slab', serif", "sans-serif"])

# Botón JS de Pantalla Completa
if st.sidebar.button("📺 Activar Pantalla Completa"):
    st.components.v1.html("<script>window.parent.document.documentElement.requestFullscreen();</script>", height=0)

# --- LÓGICA DE MENÚS ---

if menu == "⚙️ Categorías":
    st.header("⚙️ Gestión de Categorías")
    nueva_cat = st.text_input("Nombre")
    if st.button("Crear"):
        if nueva_cat and nueva_cat not in categorias:
            categorias.append(nueva_cat)
            guardar_categorias(categorias)
            st.rerun()
    st.write(categorias)

elif menu == "📝 Registro Manual":
    st.header("📝 Nueva Canción")
    with st.form("reg"):
        t = st.text_input("Título")
        a = st.text_input("Autor")
        cat = st.selectbox("Categoría", categorias)
        let = st.text_area("Letra y Acordes", height=300)
        if st.form_submit_button("Guardar"):
            nueva = pd.DataFrame([[t, a, cat, let]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!")

elif menu == "📸 Importar Foto":
    st.header("📸 Escáner de Letras")
    try:
        import pytesseract
        img_file = st.camera_input("Tomar foto")
        if img_file:
            img = Image.open(img_file)
            texto = pytesseract.image_to_string(img, lang='spa')
            with st.form("edit_foto"):
                t_f = st.text_input("Título", value="Nueva Canción")
                let_f = st.text_area("Letra extraída", value=texto, height=300)
                if st.form_submit_button("Guardar Escaneo"):
                    nueva = pd.DataFrame([[t_f, "Desconocido", "Escaner", let_f]], columns=df.columns)
                    df = pd.concat([df, nueva], ignore_index=True)
                    guardar_datos(df)
                    st.success("Guardado")
    except: st.error("OCR no configurado.")

elif menu == "🏠 Cantar / Vivo":
    col_a, col_b = st.columns([2,1])
    with col_a:
        busq = st.text_input("Buscar canción...")
    with col_b:
        filtro_cat = st.multiselect("Filtrar Categoría", categorias)

    df_f = df.copy()
    if busq: df_f = df_f[df_f['Título'].str.contains(busq, case=False)]
    if filtro_cat: df_f = df_f[df_f['Categoría'].isin(filtro_cat)]

    if not df_f.empty:
        sel = st.selectbox("Abrir:", df_f['Título'])
        c = df_f[df_f['Título'] == sel].iloc[0]
        
        st.divider()
        
        # Controles
        c1, c2, c3 = st.columns(3)
        transp = c1.number_input("Tono", -6, 6, 0)
        scroll = c2.slider("Auto-Scroll", 0, 10, 0)
        if c3.button("⭐ Al Setlist"):
            st.session_state.setlist.append(sel)
            st.toast("Añadida")

        if scroll > 0:
            st.components.v1.html(f"<script>setInterval(()=>window.parent.scrollBy(0,1),{100/scroll});</script>", height=0)

        # Visor Premium
        letra_f = transponer_texto(c['Letra'], transp)
        st.markdown(f"""
            <div class="visor-container" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; font-family:{f_family}; white-space:pre-wrap;">
            <h1 style="color:white; margin:0;">{c['Título']}</h1>
            <p style="color:#666; margin-bottom:20px;">{c['Autor']} | {c['Categoría']}</p>
            {letra_f}
            </div>
        """, unsafe_allow_html=True)

elif menu == "📋 Setlist":
    st.header("📋 Mi Setlist")
    for s in st.session_state.setlist: st.write(f"• {s}")
    if st.button("Vaciar"): st.session_state.setlist = []; st.rerun()
