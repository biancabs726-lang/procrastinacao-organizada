import streamlit as st
import pandas as pd
import requests
import urllib.parse

# ID da Planilha e GIDs
DOC_ID = "1Dq9BXjt9tbsdFQryC3NBYJTXvhHjZbtEGdG_ZXpWdp0"

GIDS = {
    "LIVROS": "1591861167",
    "SÉRIES": "1513581778",
    "UNIVERSO MARVEL": "1360927897"
}

# --- MAPEAMENTO DIRETO DE LINKS PÚBLICOS E ESTÁVEIS ---
MANUAL_POSTERS = {
    # Séries
    "olhos que condenam": "https://m.media-amazon.com/images/M/MV5BMjA3NjYzMzE1MV5BMl5BanBnXkFtZTgwNTA4NDY4NzM@._V1_SX300.jpg",
    "cavaleiro da lua": "https://m.media-amazon.com/images/M/MV5BYTc5OWU4ZjktM2M0Ni00N2JhLWE3ZjAtMTBrNWQ01mEwX123XkFtZTgw._V1_SX300.jpg",
    "she-ra": "https://m.media-amazon.com/images/M/MV5BNzA2MjA1NzA0N15BMl5BanBnXkFtZTgwOTM5NDY4NzM@._V1_SX300.jpg",
    "gavião arqueiro": "https://m.media-amazon.com/images/M/MV5BZGEzMDJjN2EtYTZiZS00M2I2LTk2ZjktNTlmOThjZTI3MGJiXkFtZTgw._V1_SX300.jpg",
    "round 6": "https://m.media-amazon.com/images/M/MV5BYWE3MDVkN2EtNjQ5MS00ZDQ4LTliNzYtMjc2YWMzMDg1ODE3XkFtZTgw._V1_SX300.jpg",
    "falcão e o soldado invernal": "https://m.media-amazon.com/images/M/MV5BMyNmYzA3Y2EtMWE4OS00NGJiLTk0NmMtYTI5NjA0YjM2N2M2XkFtZTgw._V1_SX300.jpg",
    
    # Marvel Títulos com Problema
    "capitão américa: o primeiro vingador": "https://m.media-amazon.com/images/M/MV5BMTYzOTc2Njg1N15BMl5BanBnXkFtZTcwZDkzNjU1MQ@@._V1_SX300.jpg",
    "agente carter": "https://m.media-amazon.com/images/M/MV5BMTY3NjE2MTgwMl5BMl5BanBnXkFtZTgwNTU3NTM3MjE@._V1_SX300.jpg",
    "homem de ferro": "https://m.media-amazon.com/images/M/MV5BMTczNTI2ODUwOF5BMl5BanBnXkFtZTcwMTU0NTIzMw@@._V1_SX300.jpg",
    "homem de ferro 2": "https://m.media-amazon.com/images/M/MV5BMTM0MDgwNjMyMl5BMl5BanBnXkFtZTcwNTg3NzAzMw@@._V1_SX300.jpg",
    "o incrível hulk": "https://m.media-amazon.com/images/M/MV5BMTUyNzk3MjA1OF5BMl5BanBnXkFtZTcwMTE1Njg2MQ@@._V1_SX300.jpg",
    "os vingadores": "https://m.media-amazon.com/images/M/MV5BNDYyNjA3Mzg5MV5BMl5BanBnXkFtZTgwMDUyNTkwNzE@._V1_SX300.jpg"
}

st.set_page_config(
    page_title="Procrastinação Organizada",
    page_icon="🍿",
    layout="wide"
)

# Estilização CSS para o layout compacto em lista
st.markdown("""
<style>
    .stApp { background-color: #14181c; color: #9ab; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .stProgress > div > div > div > div { background-color: #00e054; }
    
    div[data-testid="stImage"] img {
        border-radius: 6px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
        object-fit: cover !important;
        height: 110px !important;
        width: 75px !important;
    }
</style>
""", unsafe_allow_html=True)

def generate_card_url(title, bg_color="1e293b", text_color="ffffff"):
    clean_title = str(title).strip()[:15] if pd.notna(title) else "Item"
    encoded_text = urllib.parse.quote(clean_title)
    return f"https://dummyimage.com/150x225/{bg_color}/{text_color}.png&text={encoded_text}"

# --- BUSCA DE LIVROS ---
@st.cache_data(ttl=86400)
def get_book_cover(title, author=""):
    title_str = str(title).strip() if pd.notna(title) else ""
    if not title_str or title_str.lower() in ["nan", "none"]:
        return generate_card_url("Livro")
    
    try:
        query = f"{title_str} {author}".strip()
        encoded = urllib.parse.quote(query)
        url_ol = f"https://openlibrary.org/search.json?q={encoded}"
        res_ol = requests.get(url_ol, timeout=3).json()
        if "docs" in res_ol and len(res_ol["docs"]) > 0:
            cover_i = res_ol["docs"][0].get("cover_i")
            if cover_i:
                return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    except Exception:
        pass
        
    return generate_card_url(title_str, bg_color="0f172a")

# --- BUSCA DE SÉRIES E FILMES ---
@st.cache_data(ttl=86400)
def get_media_poster(title, media_type="movie"):
    title_str = str(title).strip() if pd.notna(title) else ""
    if not title_str or title_str.lower() in ["nan", "none"]:
        return generate_card_url("Mídia")
    
    title_clean = title_str.lower().strip()

    # 1. Verifica no mapa manual infalível da Amazon/IMDb CDN
    for key, url in MANUAL_POSTERS.items():
        if key in title_clean:
            return url

    # 2. OMDb API
    try:
        encoded = urllib.parse.quote(title_str)
        type_param = "series" if any(x in str(media_type).lower() for x in ["série", "serie", "tv"]) else "movie"
        url = f"http://www.omdbapi.com/?t={encoded}&type={type_param}&apikey=trilogy"
        res = requests.get(url, timeout=3).json()
        if res.get("Response") == "True" and res.get("Poster") and res["Poster"] != "N/A":
            return res["Poster"]
    except Exception:
        pass

    return generate_card_url(title_str, bg_color="1e1b4b" if "série" in str(media_type).lower() else "450a0a")

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=300)
def load_data(sheet_name):
    try:
        gid = GIDS.get(sheet_name, "0")
        url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={gid}"
        data = pd.read_csv(url, header=None)
        
        if sheet_name == "LIVROS":
            df = data.iloc[3:, [1, 2, 3, 4]].copy()
            df.columns = ["Título", "Autor", "Gênero", "Status"]
            df = df[df["Título"].fillna("").astype(str).str.strip() != ""]
            df = df[~df["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]
            return df

        elif sheet_name == "SÉRIES":
            df = data.iloc[3:, [0, 1, 2, 3]].copy()
            df.columns = ["Série", "Temporada", "Streaming", "Status"]
            df["Série"] = df["Série"].replace("", None).ffill()
            df = df[df["Série"].fillna("").astype(str).str.strip() != ""]
            df = df[~df["Série"].astype(str).str.upper().isin(["SÉRIIE", "SÉRIE", "SERIE"])]
            return df

        elif sheet_name == "UNIVERSO MARVEL":
            df = data.iloc[4:, [0, 1, 2, 3]].copy()
            df.columns = ["Título", "Tipo", "Ano", "Status"]
            df = df[df["Título"].fillna("").astype(str).str.strip() != ""]
            df = df[~df["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]
            return df

    except Exception as e:
        st.error(f"Erro ao carregar {sheet_name}: {e}")
        return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("🍿 Procrastinação Organizada")
st.caption("Seu Hub Pessoal de Entretenimento")

aba_livros, aba_series, aba_marvel = st.tabs(["📚 Biblioteca Virtual", "📺 Tracker de Séries", "🦸 Universo Marvel"])

# 1. BIBLIOTECA VIRTUAL (LIVROS)
with aba_livros:
    df_l = load_data("LIVROS")
    if not df_l.empty:
        lidos = len(df_l[df_l["Status"].astype(str).str.upper().str.strip() == "LIDO"])
        tot_l = len(df_l)
        pct_l = int((lidos / tot_l) * 100) if tot_l > 0 else 0
        
        st.subheader(f"Biblioteca Virtual: {lidos}/{tot_l} lidos ({pct_l}%)")
        st.progress(lidos / tot_l if tot_l > 0 else 0)
        
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            generos = ["Todos"] + [str(g) for g in df_l["Gênero"].dropna().unique() if str(g).strip()]
            gen_selected = st.selectbox("Gênero:", generos, key="gen_l")
        with col_f2:
            search_l = st.text_input("🔍 Pesquisar livro...", key="search_l")

        if gen_selected != "Todos":
            df_l = df_l[df_l["Gênero"].astype(str) == gen_selected]
        if search_l:
            df_l = df_l[df_l["Título"].astype(str).str.contains(search_l, case=False, na=False)]

        itens_por_pagina = 20
        total_paginas = (len(df_l) - 1) // itens_por_pagina + 1 if len(df_l) > 0 else 1
        
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1, key="pag_l")
        with col_p2:
            st.caption(f"Página {pagina} de {total_paginas} ({len(df_l)} livros encontrados)")

        inicio = (pagina - 1) * itens_por_pagina
        df_pagina = df_l.iloc[inicio:inicio + itens_por_pagina]

        st.divider()

        cols = st.columns(2)
        for idx, (_, row) in enumerate(df_pagina.iterrows()):
            with cols[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    cover_url = get_book_cover(row["Título"], row["Autor"])
                    st.image(cover_url)
                with c2:
                    st.write(f"**#{inicio + idx + 1} - {row['Título']}**")
                    st.caption(f"✍️ {row['Autor']} | 🏷️ {row['Gênero']}")
                    is_lido = (str(row["Status"]).upper().strip() == "LIDO")
                    st.checkbox("Lido", value=is_lido, key=f"livro_{inicio + idx}")
                st.markdown("---")

# 2. TRACKER DE SÉRIES
with aba_series:
    df_s = load_data("SÉRIES")
    if not df_s.empty:
        fin = len(df_s[df_s["Status"].astype(str).str.upper().str.strip() == "FINALIZADA"])
        tot_s = len(df_s)
        pct_s = int((fin / tot_s) * 100) if tot_s > 0 else 0
        
        st.subheader(f"Progresso de Séries: {fin}/{tot_s} Temporadas Finalizadas ({pct_s}%)")
        st.progress(fin / tot_s if tot_s > 0 else 0)
        
        search_s = st.text_input("🔍 Pesquisar série...", key="search_s")
        series_unicas = df_s.drop_duplicates(subset=["Série"])
        
        if search_s:
            series_unicas = series_unicas[series_unicas["Série"].astype(str).str.contains(search_s, case=False, na=False)]

        st.divider()

        cols_s = st.columns(2)
        for idx, (_, row) in enumerate(series_unicas.iterrows()):
            with cols_s[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster_url = get_media_poster(row["Série"], media_type="series")
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {row['Série']}**")
                    st.caption(f"📺 {row['Temporada']} | 🍿 {row['Streaming']}")
                    is_finalizada = (str(row["Status"]).upper().strip() == "FINALIZADA")
                    st.checkbox("Finalizada", value=is_finalizada, key=f"serie_{idx}")
                st.markdown("---")

# 3. UNIVERSO MARVEL
with aba_marvel:
    df_m = load_data("UNIVERSO MARVEL")
    if not df_m.empty:
        ass = len(df_m[df_m["Status"].astype(str).str.upper().str.strip() == "SIM"])
        tot_m = len(df_m)
        pct_m = int((ass / tot_m) * 100) if tot_m > 0 else 0
        
        st.subheader(f"Maratona MCU: {ass}/{tot_m} assistidos ({pct_m}%)")
        st.progress(ass / tot_m if tot_m > 0 else 0)
        
        search_m = st.text_input("🔍 Pesquisar no Universo Marvel...", key="search_m")
        if search_m:
            df_m = df_m[df_m["Título"].astype(str).str.contains(search_m, case=False, na=False)]

        st.divider()

        cols_m = st.columns(2)
        for idx, (_, row) in enumerate(df_m.iterrows()):
            with cols_m[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster_url = get_media_poster(row["Título"], media_type=row["Tipo"])
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {row['Título']}**")
                    st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                    is_checked = (str(row["Status"]).upper().strip() == "SIM")
                    st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
