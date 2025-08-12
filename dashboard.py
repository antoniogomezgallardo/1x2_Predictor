import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Configuration
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Quiniela Predictor Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .prediction-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .result-1 { background-color: #d4edda; border-left: 4px solid #28a745; }
    .result-X { background-color: #fff3cd; border-left: 4px solid #ffc107; }
    .result-2 { background-color: #f8d7da; border-left: 4px solid #dc3545; }
</style>
""", unsafe_allow_html=True)


def make_api_request(endpoint: str, params: dict = None, method: str = "GET"):
    """Make request to API"""
    try:
        if method == "POST":
            response = requests.post(f"{API_BASE_URL}{endpoint}", json=params)
        else:
            response = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None


def display_prediction_card(prediction):
    """Display a prediction card"""
    result_class = f"result-{prediction['predicted_result']}"
    
    confidence_color = "green" if prediction['confidence'] > 0.7 else "orange" if prediction['confidence'] > 0.5 else "red"
    
    st.markdown(f"""
    <div class="prediction-card {result_class}">
        <h4>Partido {prediction['match_number']}: {prediction['home_team']} vs {prediction['away_team']}</h4>
        <p><strong>Predicción:</strong> {prediction['predicted_result']} 
           <span style="color: {confidence_color}">({prediction['confidence']:.1%} confianza)</span></p>
        <div style="display: flex; justify-content: space-between;">
            <span>Local: {prediction['probabilities']['home_win']:.1%}</span>
            <span>Empate: {prediction['probabilities']['draw']:.1%}</span>
            <span>Visitante: {prediction['probabilities']['away_win']:.1%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.title("⚽ Quiniela Predictor Dashboard")
    st.markdown("Sistema de predicción de resultados para la Quiniela Española")
    
    # Sidebar
    st.sidebar.title("Configuración")
    current_season = st.sidebar.selectbox("Temporada", [2024, 2023, 2022], index=0)
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Predicciones Actuales", 
        "📈 Rendimiento", 
        "💰 Análisis Financiero",
        "🔧 Gestión de Datos",
        "🤖 Modelo ML"
    ])
    
    with tab1:
        st.header("Predicciones de la Semana Actual")
        
        # Get current predictions
        predictions_data = make_api_request("/predictions/current-week", {"season": current_season})
        
        if predictions_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Temporada", predictions_data['season'])
            
            with col2:
                st.metric("Jornada", predictions_data['week_number'])
            
            with col3:
                avg_confidence = sum(p['confidence'] for p in predictions_data['predictions']) / len(predictions_data['predictions'])
                st.metric("Confianza Media", f"{avg_confidence:.1%}")
            
            with col4:
                st.metric("Versión Modelo", predictions_data.get('model_version', 'N/A'))
            
            st.subheader("Predicciones por Partido")
            
            # Display predictions
            for prediction in predictions_data['predictions']:
                display_prediction_card(prediction)
            
            # Betting strategy
            st.subheader("Estrategia de Apuestas Recomendada")
            betting = predictions_data['betting_strategy']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total a Apostar", f"€{betting['total_stake']:.2f}")
            with col2:
                st.metric("Número de Apuestas", betting['number_of_bets'])
            with col3:
                st.metric("% del Bankroll", f"{betting['percentage_of_bankroll']:.1f}%")
            
            if betting['recommended_bets']:
                st.subheader("Apuestas Recomendadas")
                bet_df = pd.DataFrame(betting['recommended_bets'])
                st.dataframe(bet_df[['match_number', 'home_team', 'away_team', 'predicted_result', 'confidence', 'recommended_bet']])
        
        else:
            st.warning("No se pudieron obtener las predicciones. Verifica que el modelo esté entrenado.")
    
    with tab2:
        st.header("Rendimiento Histórico")
        
        # Get historical data
        history_data = make_api_request("/predictions/history", {"season": current_season, "limit": 20})
        
        if history_data:
            # Create dataframe
            df_history = pd.DataFrame([
                {
                    "Jornada": h['week_number'],
                    "Precisión": h['accuracy'],
                    "Aciertos": h['correct_predictions'],
                    "Total": h['total_predictions'],
                    "Beneficio": h['profit_loss'],
                    "Completada": h['is_completed']
                }
                for h in history_data
            ])
            
            if not df_history.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Accuracy over time
                    fig_accuracy = px.line(df_history, x='Jornada', y='Precisión', 
                                         title='Precisión por Jornada',
                                         markers=True)
                    fig_accuracy.update_layout(yaxis_tickformat='.1%')
                    st.plotly_chart(fig_accuracy, use_container_width=True)
                
                with col2:
                    # Profit/Loss over time
                    fig_profit = px.bar(df_history, x='Jornada', y='Beneficio', 
                                      title='Beneficio por Jornada',
                                      color='Beneficio',
                                      color_continuous_scale=['red', 'green'])
                    st.plotly_chart(fig_profit, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                completed_weeks = df_history[df_history['Completada']]
                
                with col1:
                    avg_accuracy = completed_weeks['Precisión'].mean() if not completed_weeks.empty else 0
                    st.metric("Precisión Media", f"{avg_accuracy:.1%}")
                
                with col2:
                    total_profit = completed_weeks['Beneficio'].sum() if not completed_weeks.empty else 0
                    st.metric("Beneficio Total", f"€{total_profit:.2f}")
                
                with col3:
                    best_week = completed_weeks['Precisión'].max() if not completed_weeks.empty else 0
                    st.metric("Mejor Semana", f"{best_week:.1%}")
                
                with col4:
                    total_weeks = len(completed_weeks)
                    st.metric("Semanas Completadas", total_weeks)
                
                # Detailed table
                st.subheader("Historial Detallado")
                st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No hay datos históricos disponibles.")
    
    with tab3:
        st.header("Análisis Financiero")
        
        financial_data = make_api_request("/analytics/financial-summary", {"season": current_season})
        
        if financial_data:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Apostado", f"€{financial_data['total_bet']:.2f}")
            
            with col2:
                st.metric("Total Ganado", f"€{financial_data['total_winnings']:.2f}")
            
            with col3:
                profit_color = "normal" if financial_data['total_profit'] >= 0 else "inverse"
                st.metric("Beneficio Total", f"€{financial_data['total_profit']:.2f}")
            
            with col4:
                roi_color = "normal" if financial_data['roi_percentage'] >= 0 else "inverse"
                st.metric("ROI", f"{financial_data['roi_percentage']:.1f}%")
            
            # Weekly performance chart
            if financial_data['weekly_performance']:
                df_weekly = pd.DataFrame(financial_data['weekly_performance'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Cumulative profit
                    df_weekly['Beneficio_Acumulado'] = df_weekly['profit_loss'].cumsum()
                    fig_cumulative = px.line(df_weekly, x='week_number', y='Beneficio_Acumulado',
                                           title='Beneficio Acumulado por Semana',
                                           markers=True)
                    fig_cumulative.update_traces(line_color='green')
                    st.plotly_chart(fig_cumulative, use_container_width=True)
                
                with col2:
                    # Weekly ROI
                    df_weekly['ROI_Semanal'] = (df_weekly['profit_loss'] / df_weekly['bet_amount'] * 100).fillna(0)
                    fig_roi = px.bar(df_weekly, x='week_number', y='ROI_Semanal',
                                   title='ROI Semanal (%)',
                                   color='ROI_Semanal',
                                   color_continuous_scale=['red', 'green'])
                    st.plotly_chart(fig_roi, use_container_width=True)
                
                # Performance table
                st.subheader("Rendimiento Semanal Detallado")
                st.dataframe(df_weekly[['week_number', 'bet_amount', 'winnings', 'profit_loss', 'accuracy']], 
                           use_container_width=True)
        else:
            st.info("No hay datos financieros disponibles.")
    
    with tab4:
        st.header("Gestión de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Actualizar Datos")
            
            if st.button("Actualizar Equipos", type="primary"):
                with st.spinner("Actualizando equipos..."):
                    result = make_api_request(f"/data/update-teams/{current_season}", method="POST")
                    if result:
                        st.success("Actualización de equipos iniciada")
            
            if st.button("Actualizar Partidos"):
                with st.spinner("Actualizando partidos..."):
                    result = make_api_request(f"/data/update-matches/{current_season}", method="POST")
                    if result:
                        st.success("Actualización de partidos iniciada")
            
            if st.button("Actualizar Estadísticas"):
                with st.spinner("Actualizando estadísticas..."):
                    result = make_api_request(f"/data/update-statistics/{current_season}", method="POST")
                    if result:
                        st.success("Actualización de estadísticas iniciada")
        
        with col2:
            st.subheader("Estado de los Datos")
            
            # Get teams count
            teams_data = make_api_request("/teams/")
            if teams_data:
                st.metric("Total Equipos", len(teams_data))
            
            # Get matches count (would need API endpoint)
            st.metric("Partidos Temporada", "N/A")
            
            st.metric("Última Actualización", "N/A")
    
    with tab5:
        st.header("Gestión del Modelo de Machine Learning")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Estado del Modelo")
            
            model_data = make_api_request("/analytics/model-performance")
            
            if model_data:
                st.metric("Modelo Entrenado", "✅ Sí" if model_data['is_trained'] else "❌ No")
                st.metric("Versión", model_data.get('model_version', 'N/A'))
                st.metric("Características", model_data['feature_count'])
                
                # Feature importance
                if model_data.get('feature_importance'):
                    st.subheader("Importancia de Características")
                    df_features = pd.DataFrame(model_data['feature_importance'])
                    
                    fig_features = px.bar(df_features.head(10), 
                                        x='importance', y='feature',
                                        orientation='h',
                                        title='Top 10 Características Más Importantes')
                    fig_features.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_features, use_container_width=True)
        
        with col2:
            st.subheader("Entrenar Modelo")
            
            if st.button("Entrenar Nuevo Modelo", type="primary"):
                with st.spinner("Entrenando modelo... Esto puede tomar varios minutos."):
                    result = make_api_request("/model/train", {"season": current_season}, method="POST")
                    if result:
                        st.success(f"Entrenamiento iniciado con {result['training_samples']} muestras")
                        st.info("El entrenamiento se ejecuta en segundo plano. Actualiza la página en unos minutos.")
            
            st.subheader("Configuración del Modelo")
            st.info("Configuración actual:")
            st.code("""
Algoritmos: Random Forest + XGBoost (Ensemble)
Características: ~30 variables
Validación: 5-fold cross-validation
Métricas: Accuracy, Precision, Recall, F1-Score
            """)


if __name__ == "__main__":
    main()