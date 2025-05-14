import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Função auxiliar para calcular variação percentual
def analisar_variacao(count_atual, count_anterior):
    if count_anterior == 0:
        if count_atual == 0:
            return 0, 0
        else:
            return 100.0, 1  # Considera 100% de variação se o anterior for zero e atual positivo
    var = ((count_atual - count_anterior) / count_anterior) * 100
    return var, 1 if var > 0 else -1

# Configurações iniciais do Streamlit
st.set_page_config(page_title="Relatório Estratégico", layout="wide")
st.title("📈 Análise de Reclamações Mensais")

# Ordem correta dos meses
ORDEM_MESES = [
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
]

# Função para processamento seguro dos dados
def processar_dados(df):
    try:
        # Padroniza os nomes das colunas para minúsculas e remove espaços extras
        df.columns = df.columns.str.lower().str.strip()
        # Se a coluna vier como "mês", renomeia para "mes"
        if 'mês' in df.columns:
            df.rename(columns={'mês': 'mes'}, inplace=True)
        
        # Conversão dos campos obrigatórios
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').astype('Int64')
        df['mes'] = df['mes'].str.lower().str.strip()
        
        # Mapeamento de abreviações para nomes completos dos meses
        meses_map = {
            'jan': 'janeiro', 'fev': 'fevereiro', 'mar': 'março', 'abr': 'abril',
            'mai': 'maio', 'jun': 'junho', 'jul': 'julho', 'ago': 'agosto',
            'set': 'setembro', 'out': 'outubro', 'nov': 'novembro', 'dez': 'dezembro'
        }
        df['mes'] = df['mes'].replace(meses_map).astype('category')
        df['mes'] = pd.Categorical(df['mes'], categories=ORDEM_MESES, ordered=True)
        
        # Elimina apenas linhas sem mês ou ano
        df = df.dropna(subset=['mes', 'ano'])
        
        # Preenche os demais campos com 'desconhecido' se estiverem faltando
        for col in ['segmento', 'ds_canal', 'natureza', 'motivo']:
            if col in df.columns:
                df[col] = df[col].fillna('desconhecido')
            else:
                df[col] = 'desconhecido'
        
        # Se a coluna de fato gerador não existir, cria com valor padrão
        if 'fato_gerador_fato_gerador' not in df.columns:
            df['fato_gerador_fato_gerador'] = 'desconhecido'
        
        return df
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return pd.DataFrame()

# Interface de upload
uploaded_file = st.file_uploader("Carregar arquivo CSV", type=["csv", "txt"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, delimiter=";", low_memory=False, encoding='utf-8')
        df = processar_dados(df)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {str(e)}")
        df = pd.DataFrame()
    
    if not df.empty:
        # Filtros gerais
        st.sidebar.header("🔍 Filtros de Análise")
        anos_disponiveis = sorted(df['ano'].dropna().unique(), reverse=True)
        ano_atual = st.sidebar.selectbox("Selecione o ano atual:", anos_disponiveis)
        ano_anterior = st.sidebar.selectbox("Selecione o ano anterior:", anos_disponiveis)
        
        mes_atual = st.sidebar.selectbox("Mês atual:", ORDEM_MESES)
        mes_anterior = st.sidebar.selectbox("Mês anterior:", ORDEM_MESES)
        
        # Filtros baseados em mês e ano
        filtro_atual = (df['mes'] == mes_atual) & (df['ano'] == ano_atual)
        filtro_anterior = (df['mes'] == mes_anterior) & (df['ano'] == ano_anterior)
        
        df_atual = df[filtro_atual]
        df_anterior = df[filtro_anterior]
        
        total_atual = len(df_atual)
        total_anterior = len(df_anterior)
        var_diff = total_atual - total_anterior
        variacao = ((var_diff) / total_anterior * 100) if total_anterior != 0 else 0
        
        # Resumo Geral
        st.markdown("### 📊 Resumo Geral")
        st.markdown(f"No mês de **{mes_atual.capitalize()} {ano_atual}**, tivemos uma variação de **{variacao:.2f}%** nas reclamações em comparação a {mes_anterior.capitalize()} {ano_anterior}.")
        st.markdown(f"Total de reclamações: **{total_anterior} → {total_atual}**")
        
        # Impacto Geral por segmento no mês atual
        segmento_contagem = df_atual['segmento'].value_counts(normalize=True) * 100
        if not segmento_contagem.empty:
            top_segmento = segmento_contagem.idxmax()
            top_percentual = segmento_contagem.max()
            st.markdown("📌 Impacto Geral")
            st.markdown(f"O segmento **{top_segmento}** representa **{top_percentual:.2f}%** do total de reclamações em {mes_atual.capitalize()} {ano_atual}.")
        
        # Gráfico de comparação mensal com variação e cores (verde para redução, vermelho para aumento)
        color_atual = '#f44336' if var_diff > 0 else '#4CAF50' if var_diff < 0 else 'gray'
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            x=[mes_anterior.capitalize(), mes_atual.capitalize()],
            y=[total_anterior, total_atual],
            text=[total_anterior, total_atual],
            textposition='auto',
            marker_color=['blue', color_atual]
        ))
        fig_comp.update_layout(
            title="🔄 Comparativo Mensal",
            xaxis_title="Mês",
            yaxis_title="Total de Reclamações",
            template="plotly_white"
        )
        # Adiciona anotação com a variação percentual
        fig_comp.add_annotation(
            x=mes_atual.capitalize(),
            y=total_atual,
            text=f'Variação: {variacao:.2f}%',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40,
            font=dict(color=color_atual, size=14)
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Análise por Segmento e Canal (resumido)
        st.header("📊 Análise por Segmento e Canal")
        for segmento in df['segmento'].dropna().unique():
            st.subheader(f"Segmento: {segmento}")
            for canal in ['Procon', 'Ouvidoria', 'Geral']:
                df_atual_canal = df_atual if canal == 'Geral' else df_atual[df_atual['ds_canal'] == canal]
                df_anterior_canal = df_anterior if canal == 'Geral' else df_anterior[df_anterior['ds_canal'] == canal]
                if df_atual_canal.empty and df_anterior_canal.empty:
                    continue
                st.markdown(f"**{canal} - {mes_atual.capitalize()} {ano_atual} vs {mes_anterior.capitalize()} {ano_anterior}**")
                # Comparação de Natureza
                natureza_atual = df_atual_canal['natureza'].value_counts().rename("Atual")
                natureza_anterior = df_anterior_canal['natureza'].value_counts().rename("Anterior")
                comparacao_natureza = pd.concat([natureza_atual, natureza_anterior], axis=1).fillna(0)
                comparacao_natureza['Variação'] = comparacao_natureza['Atual'] - comparacao_natureza['Anterior']
                st.dataframe(comparacao_natureza)
                # Comparação de Motivo
                motivo_atual = df_atual_canal['motivo'].value_counts().rename("Atual")
                motivo_anterior = df_anterior_canal['motivo'].value_counts().rename("Anterior")
                comparacao_motivo = pd.concat([motivo_atual, motivo_anterior], axis=1).fillna(0)
                comparacao_motivo['Variação'] = comparacao_motivo['Atual'] - comparacao_motivo['Anterior']
                st.dataframe(comparacao_motivo)
        
        # Seção: Evolução Mensal e Análise Detalhada por Natureza
        st.header("📈 Evolução Mensal e Análise Detalhada por Natureza")
        for segmento in df['segmento'].dropna().unique():
            st.subheader(f"Segmento: {segmento}")
            # Evolução Mensal do segmento (agrupando todos os anos)
            df_segmento = df[df['segmento'] == segmento]
            df_evolucao = df_segmento.groupby(['ano', 'mes']).size().reset_index(name='Reclamações')
            # Cria coluna combinada "ano_mes" (ex.: Janeiro 2025)
            df_evolucao['ano_mes'] = df_evolucao['mes'].astype(str).str.capitalize() + ' ' + df_evolucao['ano'].astype(str)
            
            fig_evolucao = px.line(df_evolucao, x='ano_mes', y='Reclamações', 
                                   title=f'Evolução Mensal de Reclamações - {segmento}',
                                   labels={'ano_mes': 'Mês/Ano', 'Reclamações': 'Total de Reclamações'},
                                   text='Reclamações',
                                   color='ano')
            fig_evolucao.update_traces(
                mode='lines+markers+text',
                textposition='top center',
                marker=dict(size=10),
                line=dict(width=2.5),
                textfont=dict(size=14, color='#2c3e50')
            )
            fig_evolucao.update_layout(
                xaxis_title='Mês/Ano',
                yaxis_title='Total de Reclamações',
                template='plotly_white',
                hovermode='x unified',
                showlegend=True,
                legend_title_text='Ano'
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
            # Análise Detalhada por Natureza (comparando período atual e anterior)
            df_segmento_atual = df_atual[df_atual['segmento'] == segmento]
            df_segmento_anterior = df_anterior[df_anterior['segmento'] == segmento]
            
            st.markdown('<div class="natureza-header">🔍 Análise Detalhada por Natureza</div>', unsafe_allow_html=True)
            
            # Calcula a variação nas contagens por natureza
            count_atual_natureza = df_segmento_atual['natureza'].value_counts()
            count_anterior_natureza = df_segmento_anterior['natureza'].value_counts()
            naturezas_positivas = count_atual_natureza.subtract(count_anterior_natureza, fill_value=0)
            
            # Naturezas com Redução
            st.markdown("### ✅ Naturezas com Redução")
            for natureza, variacao in naturezas_positivas.nsmallest(5).items():
                if variacao < 0:
                    with st.expander(f"**{natureza}** (Redução de {abs(int(variacao))} reclamações)", expanded=False):
                        st.markdown("**Motivos relacionados:**")
                        motivos_atual = df_segmento_atual[df_segmento_atual['natureza'] == natureza]['motivo'].value_counts()
                        motivos_anterior = df_segmento_anterior[df_segmento_anterior['natureza'] == natureza]['motivo'].value_counts()
                        for motivo, count_atual in motivos_atual.items():
                            count_anterior = motivos_anterior.get(motivo, 0)
                            var_motivo, _ = analisar_variacao(count_atual, count_anterior)
                            st.markdown(f"""
<div class="motivo-item">
▸ {motivo}: 
<span style="color: {'#4CAF50' if var_motivo < 0 else '#f44336'}">
    {count_anterior} → {count_atual} ({var_motivo:.2f}%)
</span>
</div>
""", unsafe_allow_html=True)
                        st.markdown("**Fatos Geradores mais comuns:**")
                        fatos_geradores = df_segmento_atual[df_segmento_atual['natureza'] == natureza]['fato_gerador_fato_gerador'].value_counts()
                        for fato, count in fatos_geradores.head(5).items():
                            st.markdown(f"- {fato}: {count} ocorrências")
            
            # Naturezas com Aumento
            st.markdown("### 🚨 Naturezas com Aumento")
            for natureza, variacao in naturezas_positivas.nlargest(5).items():
                if variacao > 0:
                    with st.expander(f"**{natureza}** (Aumento de {int(variacao)} reclamações)", expanded=False):
                        st.markdown("**Motivos relacionados:**")
                        motivos_atual = df_segmento_atual[df_segmento_atual['natureza'] == natureza]['motivo'].value_counts()
                        motivos_anterior = df_segmento_anterior[df_segmento_anterior['natureza'] == natureza]['motivo'].value_counts()
                        for motivo, count_atual in motivos_atual.items():
                            count_anterior = motivos_anterior.get(motivo, 0)
                            var_motivo, _ = analisar_variacao(count_atual, count_anterior)
                            st.markdown(f"""
<div class="motivo-item">
▸ {motivo}: 
<span style="color: {'#4CAF50' if var_motivo < 0 else '#f44336'}">
    {count_anterior} → {count_atual} ({var_motivo:.2f}%)
</span>
</div>
""", unsafe_allow_html=True)
                        st.markdown("**Fatos Geradores mais comuns:**")
                        fatos_geradores = df_segmento_atual[df_segmento_atual['natureza'] == natureza]['fato_gerador_fato_gerador'].value_counts()
                        for fato, count in fatos_geradores.head(5).items():
                            st.markdown(f"- {fato}: {count} ocorrências")
    else:
        st.warning("Nenhum dado válido encontrado após o processamento!")
else:
    st.info("Por favor, carregue um arquivo CSV ou TXT para iniciar a análise")
