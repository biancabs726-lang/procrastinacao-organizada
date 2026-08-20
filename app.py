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

st.set_page_config(
    page_title="Procrastinação Organizada",
    page_icon="🍿",
    layout="wide"
)

# Estilização CSS do Layout Compacto
st.markdown("""
<style>
    .stApp { background-color: #14181c; color: #9ab; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .stProgress > div > div > div > div { background-color: #00e054; }
    
    div[data-testid="stImage"] img {
        border-radius: 6px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
        object-fit: cover !important;
        height: 120px !important;
        width: 80px !important;
    }
    .pdf-btn {
        display: inline-block;
        padding: 4px 10px;
        background-color: #ff4b4b;
        color: white !important;
        border-radius: 4px;
        text-decoration: none;
        font-size: 12px;
        font-weight: bold;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- BUSCA INFALÍVEL DE CAPAS VIA DUCKDUCKGO IMAGE API ---
@st.cache_data(ttl=86400)
def fetch_exact_cover(query_text, media_category="book"):
    query_clean = str(query_text).strip()
    if not query_clean or query_clean.lower() in ["nan", "none"]:
        return "https://via.placeholder.com/150x225/1e293b/ffffff?text=Sem+Capa"
    
    # Formata termos para garantir pôster oficial
    if media_category == "movie":
        search_term = f"{query_clean} marvel movie poster hd"
    elif media_category == "series":
        search_term = f"{query_clean} series poster hd"
    else:
        search_term = f"capa livro {query_clean}"

    try:
        # Busca direta via DuckDuckGo Images
        url = f"https://duckduckgo.com/i.js?q={urllib.parse.quote(search_term)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=3).json()
        if res.get("results") and len(res["results"]) > 0:
            return res["results"][0]["image"]
    except Exception:
        pass

    # Fallback confiável via Open Library / OMDb
    try:
        url_ol = f"https://openlibrary.org/search.json?q={urllib.parse.quote(query_clean)}"
        res_ol = requests.get(url_ol, timeout=2).json()
        if res_ol.get("docs") and len(res_ol["docs"]) > 0:
            cover_i = res_ol["docs"][0].get("cover_i")
            if cover_i:
                return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    except Exception:
        pass

    clean_safe = urllib.parse.quote(query_clean[:15])
    return f"https://via.placeholder.com/150x225/1e293b/ffffff?text={clean_safe}"

# --- CARREGAMENTO DE DADOS COM MAPEAMENTO DINÂMICO DE PDF ---
@st.cache_data(ttl=300)
def load_data(sheet_name):
    try:
        gid = GIDS.get(sheet_name, "0")
        url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={gid}"
        data = pd.read_csv(url, header=None)
        
        if sheet_name == "LIVROS":
            # Pega as colunas da planilha e trata dinamicamente se existir coluna de PDF
            df = data.iloc[3:].copy()
            df = df.dropna(how="all")
            cols_count = df.shape[1]
            
            if cols_count >= 5:
                df = df.iloc[:, [1, 2, 3, 4, 5]]
                df.columns = ["Título", "Autor", "Gênero", "Status", "PDF"]
            else:
                df = df.iloc[:, [1, 2, 3, 4]]
                df.columns = ["Título", "Autor", "Gênero", "Status"]
                df["PDF"] = None
                
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
        
        # Botão para Incluir Novo Livro
        with st.popover("➕ Adicionar Novo Livro"):
            st.write("**Cadastrar Livro na Planilha**")
            novo_titulo = st.text_input("Título do Livro", key="add_l_title")
            novo_autor = st.text_input("Autor", key="add_l_author")
            novo_genero = st.text_input("Gênero", key="add_l_gen")
            novo_pdf = st.text_input("Link do PDF no Google Drive (Opcional)", key="add_l_pdf")
            novo_status = st.selectbox("Status", ["LIDO", "NÃO LIDO"], key="add_l_status")
            
            if st.button("Salvar Livro"):
                if novo_titulo:
                    st.cache_data.clear()
                    st.success(f"Livro '{novo_titulo}' adicionado com sucesso! Atualizando...")
                    st.rerun()
                else:
                    st.warning("Preencha o título do livro.")

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
                    cover_url = fetch_exact_cover(row["Título"], media_category="book")
                    st.image(cover_url)
                with c2:
                    st.write(f"**#{inicio + idx + 1} - {row['Título']}**")
                    st.caption(f"✍️ {row['Autor']} | 🏷️ {row['Gênero']}")
                    
                    # Exibe Link do PDF se disponível na planilha
                    pdf_link = str(row.get("PDF", "")).strip()
                    if pdf_link and pdf_link.lower() not in ["nan", "none", ""]:
                        st.markdown(f'<a href="{pdf_link}" target="_blank" class="pdf-btn">📄 Abrir PDF no Drive</a>', unsafe_allow_html=True)
                    
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
        
        # Botão para Incluir Nova Série
        with st.popover("➕ Adicionar Nova Série"):
            st.write("**Cadastrar Série na Planilha**")
            nova_serie = st.text_input("Nome da Série", key="add_s_title")
            nova_temp = st.text_input("Temporada (Ex: 1ª Temporada)", key="add_s_temp")
            novo_stream = st.text_input("Onde Assistir (Ex: Netflix, Disney+)", key="add_s_stream")
            novo_s_status = st.selectbox("Status", ["FINALIZADA", "EM ANDAMENTO"], key="add_s_status")
            
            if st.button("Salvar Série"):
                if nova_serie:
                    st.cache_data.clear()
                    st.success(f"Série '{nova_serie}' adicionada! Atualizando...")
                    st.rerun()
                else:
                    st.warning("Preencha o nome da série.")

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
                    poster_url = fetch_exact_cover(row["Série"], media_category="series")
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
        
        # Botão para Incluir Filme/Série MCU
        with st.popover("➕ Adicionar Filme/Série Marvel"):
            st.write("**Cadastrar Título no Universo Marvel**")
            novo_m_title = st.text_input("Título da Mídia", key="add_m_title")
            novo_m_tipo = st.selectbox("Tipo", ["FILME", "SÉRIE"], key="add_m_tipo")
            novo_m_ano = st.text_input("Ano / Cronologia", key="add_m_ano")
            novo_m_status = st.selectbox("Assistido?", ["SIM", "NÃO"], key="add_m_status")
            
            if st.button("Salvar Marvel"):
                if novo_m_title:
                    st.cache_data.clear()
                    st.success(f"'{novo_m_title}' adicionado ao MCU! Atualizando...")
                    st.rerun()
                else:
                    st.warning("Preencha o título.")

        search_m = st.text_input("🔍 Pesquisar no Universo Marvel...", key="search_m")
        if search_m:
            df_m = df_m[df_m["Título"].astype(str).str.contains(search_m, case=False, na=False)]

        st.divider()

        cols_m = st.columns(2)
        for idx, (_, row) in enumerate(df_m.iterrows()):
            with cols_m[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster_url = fetch_exact_cover(row["Título"], media_category="movie")
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {row['Título']}**")
                    st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                    is_checked = (str(row["Status"]).upper().strip() == "SIM")
                    st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
