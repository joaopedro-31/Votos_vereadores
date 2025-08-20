import streamlit as st
import pandas as pd
import os

# Caminho
path = r"C:\Users\jpkab\OneDrive\Desktop\LÉO COUTO\py\csvs"

@st.cache_data
def carregar_dados():
    all_dfs = []
    for arquivo in os.listdir(path):
        if arquivo.endswith(".csv"):
            df = pd.read_csv(os.path.join(path, arquivo), delimiter=";")
            df = df.drop(index=df.index[-1], errors='ignore')
            colunas_validas = ['Candidato', 'Número', 'Local de Votação', 'Votos']
            if 'Bairro' in df.columns:
                colunas_validas.append('Bairro')
            df = df[colunas_validas]
            all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)

df = carregar_dados()

# Interface
st.title("📊 Análise de Votação para Vereadores")

modo = st.radio("Escolha o tipo de análise:", ["🔍 Por Local de Votação", "🏘️ Por Bairro", "👤 Por Candidato"])

if modo == "🔍 Por Local de Votação":
    locais = sorted(df['Local de Votação'].dropna().unique())
    local_escolhido = st.selectbox("Selecione o Local:", locais)

    if local_escolhido:
        df_filtrado = df[df['Local de Votação'] == local_escolhido]
elif modo == "🏘️ Por Bairro":
    if "Bairro" not in df.columns:
        st.error("⚠️ A coluna 'Bairro' não existe nos seus arquivos.")
    else:
        bairros = sorted(df['Bairro'].dropna().unique())
        bairro_escolhido = st.selectbox("Selecione o Bairro:", bairros)
        if bairro_escolhido:
            df_filtrado = df[df['Bairro'] == bairro_escolhido]
elif modo == "👤 Por Candidato":
    candidatos = sorted(df['Candidato'].dropna().unique())
    candidato_escolhido = st.selectbox("Selecione o Candidato:", candidatos)
    if candidato_escolhido:
        df_filtrado = df[df['Candidato'] == candidato_escolhido]

# Exibição de resultados
if 'df_filtrado' in locals() and not df_filtrado.empty:
    agrupado = None

    if modo == "👤 Por Candidato":
        agrupado = df_filtrado.groupby(['Local de Votação'])['Votos'].sum().reset_index()
        st.subheader(f"📍 Locais onde **{candidato_escolhido}** recebeu votos")
    else:
        agrupado = df_filtrado.groupby(['Candidato', 'Número'])['Votos'].sum().reset_index()
        agrupado = agrupado.sort_values(by='Votos', ascending=False)
        st.subheader("🏆 Vereador mais votado:")
        mais_votado = agrupado.iloc[0]
        st.markdown(f"**{mais_votado['Candidato']}** ({mais_votado['Número']}) com **{mais_votado['Votos']}** votos.")

    # Tabela
    st.subheader("📋 Tabela de Votos")
    st.dataframe(agrupado)

    # Gráfico
    st.subheader("📈 Gráfico")
    if modo == "👤 Por Candidato":
        st.bar_chart(agrupado.set_index('Local de Votação')['Votos'])
    else:
        st.bar_chart(agrupado.set_index('Candidato')['Votos'])

elif 'df_filtrado' in locals():
    st.warning("Nenhum dado encontrado.")
