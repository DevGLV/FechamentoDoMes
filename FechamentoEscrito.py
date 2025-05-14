import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# Configurações iniciais
st.set_page_config(page_title="Relatório Estratégico", layout="wide", page_icon="📈")
st.title("📊 Painel Estratégico de Reclamações")

# Mapeamento de meses
MESES = {
    'jan': 'janeiro', 'fev': 'fevereiro', 'mar': 'março',
    'abr': 'abril', 'mai': 'maio', 'jun': 'junho',
    'jul': 'julho', 'ago': 'agosto', 'set': 'setembro',
    'out': 'outubro', 'nov': 'novembro', 'dez': 'dezembro'
}

# Estilos CSS personalizados
st.markdown("""
<style>
    .header-box {background: #2c3e50; color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
    .positive {background: #e8f5e9!important; border-left: 5px solid #27ae60!important;}
    .negative {background: #fde8e8!important; border-left: 5px solid #e74c3c!important;}
    .neutral {background: #f0f8ff!important; border-left: 5px solid #3498db!important;}
    .metric-card {padding: 1.5rem; border-radius: 10px; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .warning {background: #fff3cd!important; border: 1px solid #ffd700!important;}
    .segment-title {font-size: 1.4rem!important; color: #2c3e50!important; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem;}
    .high-impact {color: #e74c3c!important; font-weight: 700!important;}
    .positive-text {color: #27ae60!important; font-weight: 600!important;}
    .analysis-section {margin: 2rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)



# Funções de análise
def calcular_variacao(atual, anterior):
    if anterior == 0: return 0, 'neutral'
    variacao = ((atual - anterior)/anterior)*100
    status = 'positive' if variacao < -5 else 'negative' if variacao > 5 else 'neutral'
    return variacao, status

def gerar_diagnostico(variacao, total_atual):
    if variacao < -20:
        return "🔥 Melhora Significativa", "Redução superior a 20% em relação ao período anterior"
    elif variacao < -5:
        return "📉 Tendência Positiva", "Queda nas reclamações dentro da margem esperada"
    elif variacao > 20:
        return "🚨 Alerta Crítico", "Aumento preocupante superior a 20% nas reclamações"
    elif variacao > 5:
        return "📈 Tendência Negativa", "Crescimento nas reclamações requer atenção"
    else:
        return "🔄 Estabilidade", "Números dentro da variação normal esperada"

def analisar_tendencia(df):
    ultimos_3_meses = df.sort_values(['ano', 'mes_num']).tail(3)
    if len(ultimos_3_meses) < 3: return "🔍 Dados Insuficientes"
    diff1 = ultimos_3_meses.iloc[1]['total_atual'] - ultimos_3_meses.iloc[0]['total_atual']
    diff2 = ultimos_3_meses.iloc[2]['total_atual'] - ultimos_3_meses.iloc[1]['total_atual']
    
    if diff2 < 0 and diff1 < 0: return "📉 Queda Consistente"
    if diff2 > 0 and diff1 > 0: return "📈 Crescimento Acelerado"
    if (diff1 < 0 and diff2 > 0) or (diff1 > 0 and diff2 < 0): return "📊 Tendência Volátil"
    return "📌 Padrão Estável"

# Processamento de dados
def processar_dados(df):
    df = df.copy()
    df['mes'] = df['mes'].str.lower().str.strip().map(MESES)
    df['mes_num'] = df['mes'].map({v: k+1 for k, v in enumerate(MESES.values())})
    df['Segmento'] = df['Segmento'].str.upper().str.strip()
    df['Data'] = pd.to_datetime(df['Data_de_Recebimento_da_Ouvidoria'], errors='coerce')
    return df.dropna(subset=['mes', 'ano', 'Segmento', 'Natureza'])

# Geração de narrativa
def criar_storytelling(segmento, dados):
    variação = dados['variação']
    total = dados['total_atual']
    tendencia = dados['tendencia']
    impacto = dados['impacto']
    top_naturezas = dados['top_naturezas']
    
    # Cabeçalho do diagnóstico
    if variação > 20:
        emoji, status = "🔴", "high-alert"
        header = f"<div class='header-box negative'><h3>{segmento} - Situação Crítica</h3></div>"
    elif variação > 5:
        emoji, status = "🟠", "alert"
        header = f"<div class='header-box warning'><h3>{segmento} - Atenção Necessária</h3></div>"
    elif variação < -10:
        emoji, status = "🟢", "positive"
        header = f"<div class='header-box positive'><h3>{segmento} - Melhora Expressiva</h3></div>"
    else:
        emoji, status = "🔵", "neutral"
        header = f"<div class='header-box neutral'><h3>{segmento} - Estabilidade Operacional</h3></div>"
    
    # Construção da narrativa
    story = f"""
    {header}
    <div class='metric-card {status}'>
        <div class='analysis-section'>
            <h4 class='segment-title'>{emoji} Diagnóstico do Segmento</h4>
            <p>O segmento <span class='high-impact'>{segmento}</span> apresenta atualmente:</p>
            <ul>
                <li><b>{dados['total_atual']} reclamações</b> ({dados['impacto']:.1f}% do total)</li>
                <li>Tendência recente: <b>{tendencia}</b></li>
                <li>Variação mensal: <span class={'positive-text' if variação <0 else 'high-impact'}>{variação:.1f}%</span></li>
            </ul>
        </div>
        
        <div class='analysis-section'>
            <h4>🔍 Principais Drivers</h4>
            <p>As naturezas mais críticas representam <b>{dados['top_percent']:.1f}%</b> das ocorrências:</p>
            {''.join([f"<li>{k} ({v} casos)" for k,v in top_naturezas.items()])}
        </div>
        
        <div class='analysis-section warning'>
            <h4>🚨 Recomendações Estratégicas</h4>
            {gerar_recomendacoes(variação, tendencia, impacto)}
        </div>
    </div>
    """
    return story

def gerar_recomendacoes(variação, tendencia, impacto):
    if variação > 15:
        return f"""
        <ul>
            <li>Priorizar análise detalhada das causas do aumento de {variação:.1f}%</li>
            <li>Revisar processos relacionados a: {', '.join(list(top_naturezas.keys())[:2])}</li>
            <li>Implementar ações corretivas imediatas</li>
        </ul>
        """
    elif impacto > 8:
        return f"""
        <ul>
            <li>Otimizar gestão de reclamações para reduzir impacto geral</li>
            <li>Desenvolver plano de ação para as naturezas predominantes</li>
            <li>Monitorar indicadores diariamente</li>
        </ul>
        """
    else:
        return """
        <ul>
            <li>Manter ações de monitoramento contínuo</li>
            <li>Otimizar processos preventivos</li>
            <li>Realizar benchmarking com segmentos similares</li>
        </ul>
        """

# Interface principal
uploaded_file = st.file_uploader("📤 Carregue seu arquivo de dados", type="csv")

if uploaded_file:
    df = processar_dados(pd.read_csv(uploaded_file, delimiter=';'))
    
    # Controles de análise
    st.sidebar.header("🔧 Configurações de Análise")
    mes_atual = st.sidebar.selectbox("Selecione o mês atual:", df['mes'].unique())
    ano_atual = st.sidebar.selectbox("Ano atual:", df['ano'].unique())
    
    # Filtragem de dados
    df_atual = df[(df['mes'] == mes_atual) & (df['ano'] == ano_atual)]
    df_anterior = df[(df['mes'] == MESES[list(MESES.keys())[list(MESES.values()).index(mes_atual)-1]]) 
                   & (df['ano'] == (ano_atual if list(MESES.values()).index(mes_atual) != 0 else ano_atual-1))]
    
    # Métricas gerais
    total_geral = df_atual.shape[0]
    variacao_geral, _ = calcular_variacao(total_geral, df_anterior.shape[0])
    st.markdown(f"""
    <div class='metric-card'>
        <h3>📌 Visão Geral {mes_atual.capitalize()} {ano_atual}</h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
            <div class='metric-card {'positive' if variacao_geral <0 else 'negative'}'>
                <h4>🔢 Total Reclamações</h4>
                <h2>{total_geral}</h2>
                <p>Variação: <span class={'positive-text' if variacao_geral <0 else 'high-impact'}>{variacao_geral:.1f}%</span></p>
            </div>
            <div class='metric-card'>
                <h4>🏷 Segmentos Ativos</h4>
                <h2>{df_atual['Segmento'].nunique()}</h2>
                <p>Principais: {', '.join(df_atual['Segmento'].value_counts().head(2).index.to_list())}</p>
            </div>
            <div class='metric-card'>
                <h4>📌 Naturezas Mais Frequentes</h4>
                <h2>{df_atual['Natureza'].mode()[0]}</h2>
                <p>{df_atual['Natureza'].value_counts().iloc[0]} ocorrências</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Análise por segmento
    st.markdown("---")
    st.markdown("## 🎯 Análise Estratégica por Segmento")
    
    for segmento in df_atual['Segmento'].unique():
        df_seg = df_atual[df_atual['Segmento'] == segmento]
        df_seg_ant = df_anterior[df_anterior['Segmento'] == segmento]
        
        # Cálculo de métricas
        total_atual = df_seg.shape[0]
        total_anterior = df_seg_ant.shape[0]
        variacao, _ = calcular_variacao(total_atual, total_anterior)
        impacto = (total_atual / total_geral) * 100
        tendencia = analisar_tendencia(df[df['Segmento'] == segmento].groupby(['ano','mes_num','mes'])['Natureza'].count().reset_index())
        top_naturezas = df_seg['Natureza'].value_counts().nlargest(3).to_dict()
        top_percent = (sum(top_naturezas.values()) / total_atual) * 100
        
        # Gerar storytelling
        dados_segmento = {
            'variação': variacao,
            'total_atual': total_atual,
            'tendencia': tendencia,
            'impacto': impacto,
            'top_naturezas': top_naturezas,
            'top_percent': top_percent
        }
        
        st.markdown(criar_storytelling(segmento, dados_segmento), unsafe_allow_html=True)
        
        # Gráfico de evolução
        fig = px.line(
            df[df['Segmento'] == segmento].groupby(['ano','mes_num','mes'])['Natureza'].count().reset_index(),
            x='mes', y='Natureza', color='ano',
            title=f'Evolução Histórica - {segmento}',
            labels={'Natureza': 'Reclamações', 'mes': 'Mês'}
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ Carregue um arquivo CSV para iniciar a análise")
