import streamlit as st
import pandas as pd
import requests

# ID de Publicação da sua Planilha (obtido da sua URL pubhtml)
PUB_ID = "2PACX-1vRHCcyhfmA0iw5CKm-jcTqb1_VYoCdHpxWWkjTQJqJK7beldA0KRgLKveiEqxV0xJs_VfXh_pTI33rF"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Procrastinação Organizada",
    page_icon="🍿",
    layout="wide"
)

# Estilo Dark / Letterboxd
st.markdown("""
<style>
    .stApp { background-color: #14181c; color: #9ab; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .stProgress > div > div > div > div { background-color: #00e054; }
</style>
""", unsafe_allow_html=True)

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")

# --- APIs DE CAPA ---
@st.cache_data(ttl=86400)
def get_book_cover(title, author=""):
    try:
        query = f"{title} {author}".strip()
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"
        res = requests.get(url, timeout=5).json()
        if "items" in res and len(res["items"]) > 0:
            image_links = res["items"][0].get("volumeInfo", {}).get("imageLinks", {})
            cover = image_links.get("thumbnail") or image_links.get("smallThumbnail")
            if cover:
                return cover.replace("http://", "https://")
    except Exception:
        pass
    return f"https://placehold.co/300x450/1c252f/FFF?text={title.replace(' ', '+')}"

@st.cache_data(ttl=86400)
def get_tmdb_poster(title, media_type="movie"):
    if not TMDB_API_KEY:
        return f"https://placehold.co/300x450/1c252f/FFF?text={title.replace(' ', '+')}"
    try:
        search_type = "tv" if str(media_type).lower() in ["série", "tv"] else "movie"
        url = f"https://api.themoviedb.org/3/search/{search_type}?api_key={TMDB_API_KEY}&query={title}&language=pt-BR"
        res = requests.get(url, timeout=5).json()
        if "results" in res and len(res["results"]) > 0:
            poster_path = res["results"][0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        pass
    return f"https://placehold.co/300x450/1c252f/FFF?text={title.replace(' ', '+')}"

# --- CARREGAMENTO DIRETO VIA CSV PÚBLICO ---
@st.cache_data(ttl=300)
def load_data(sheet_name):
    try:
        # URL de exportação direta do Google Sheets publicado
        sheet_encoded = requests.utils.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/e/{PUB_ID}/pub?single=true&output=csv&sheet={sheet_encoded}"
        
        data = pd.read_csv(url, header=None)
        
        if sheet_name == "LIVROS":
            df = data.iloc[3:, [1, 2, 3, 4]].copy()
            df.columns = ["Título", "Autor", "Gênero", "Status"]
            df = df[df["Título"].astype(str).str.strip() != ""]
            return df

        elif sheet_name == "SÉRIES":
            df = data.iloc[3:, [0, 1, 2, 3]].copy()
            df.columns = ["Série", "Temporada", "Streaming", "Status"]
            df["Série"] = df["Série"].replace("", None).ffill()
            df = df[df["Série"].astype(str).str.strip() != ""]
            return df

        elif sheet_name == "UNIVERSO MARVEL":
            df = data.iloc[2:, [0, 1, 2, 3]].copy()
            df.columns = ["Título", "Tipo", "Ano", "Status"]
            df = df[df["Título"].astype(str).str.strip() != ""]
            return df

    except Exception as e:
        st.error(f"Erro ao carregar {sheet_name}: {e}")
        return pd.DataFrame()

# --- INTERFACE ---
st.title("🍿 Procrastinação Organizada")
st.caption("Seu Hub Pessoal de Entretenimento")

aba_livros, aba_series, aba_marvel = st.tabs(["📚 Biblioteca Virtual", "📺 Tracker de Séries", "🦸 Universo Marvel"])

# --- 1. ABA LIVROS ---
with aba_livros:
    df_l = load_data("LIVROS")
    if not df_l.empty:
        lidos = len(df_l[df_l["Status"].astype(str).str.upper().str.strip() == "LIDO"])
        total = len(df_l)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Livros Lidos", lidos)
        c2.metric("Total na Lista", total)
        c3.metric("Progresso Geral", f"{(lidos/total)*100:.1f}%" if total > 0 else "0%")
        st.progress(lidos / total if total > 0 else 0)
        st.divider()

        generos = ["Todos"] + [g for g in df_l["Gênero"].unique() if g]
        gen_selected = st.selectbox("Filtrar por Gênero:", generos)
        if gen_selected != "Todos":
            df_l = df_l[df_l["Gênero"] == gen_selected]

        cols = st.columns(4)
        for idx, (_, row) in enumerate(df_l.head(24).iterrows()):
            with cols[idx % 4]:
                cover_url = get_book_cover(row["Título"], row["Autor"])
                st.image(cover_url, use_container_width=True)
                st.subheader(row["Título"])
                st.caption(f"✍️ {row['Autor']} | {row['Gênero']}")
                st.write(f"Status: **{row['Status']}**")
                st.markdown("---")

# --- 2. ABA SÉRIES ---
with aba_series:
    df_s = load_data("SÉRIES")
    if not df_s.empty:
        fin = len(df_s[df_s["Status"].astype(str).str.upper().str.strip() == "FINALIZADA"])
        tot = len(df_s)
        
        st.subheader(f"Progresso de Séries: {fin}/{tot} Temporadas Finalizadas ({int(fin/tot*100) if tot > 0 else 0}%)")
        st.progress(fin / tot if tot > 0 else 0)
        st.divider()

        series_unicas = df_s.drop_duplicates(subset=["Série"])

        cols_s = st.columns(4)
        for idx, (_, row) in enumerate(series_unicas.iterrows()):
            with cols_s[idx % 4]:
                poster_url = get_tmdb_poster(row["Série"], media_type="tv")
                st.image(poster_url, use_container_width=True)
                st.subheader(row["Série"])
                st.caption(f"📺 {row['Temporada']} ({row['Streaming']})")
                st.write(f"Status: **{row['Status']}**")
                st.markdown("---")

# --- 3. ABA MARVEL ---
with aba_marvel:
    df_m = load_data("UNIVERSO MARVEL")
    if not df_m.empty:
        ass = len(df_m[df_m["Status"].astype(str).str.upper().str.strip() == "SIM"])
        tot_m = len(df_m)
        
        st.subheader(f"Maratona MCU: {ass}/{tot_m} assistidos ({int(ass/tot_m*100) if tot_m > 0 else 0}%)")
        st.progress(ass / tot_m if tot_m > 0 else 0)
        st.divider()

        cols_m = st.columns(4)
        for idx, (_, row) in enumerate(df_m.iterrows()):
            with cols_m[idx % 4]:
                poster_url = get_tmdb_poster(row["Título"], media_type=row["Tipo"])
                st.image(poster_url, use_container_width=True)
                st.write(f"**#{idx+1} - {row['Título']}**")
                st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                is_checked = (str(row["Status"]).upper().strip() == "SIM")
                st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
