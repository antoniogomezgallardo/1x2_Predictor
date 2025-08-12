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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 Mi Quiniela", 
        "📊 Predicciones Actuales", 
        "📈 Rendimiento", 
        "💰 Análisis Financiero",
        "🔧 Gestión de Datos",
        "🤖 Modelo ML"
    ])
    
    with tab1:
        st.header("🎯 Mi Quiniela Personal")
        
        # Sub-tabs para diferentes funciones
        subtab1, subtab2, subtab3 = st.tabs(["📋 Próximos Partidos", "📊 Mi Historial", "✅ Actualizar Resultados"])
        
        with subtab1:
            st.subheader("Próximos Partidos con Predicciones Detalladas")
            
            # Botón para actualizar datos y entrenar modelo
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Actualizar Datos", type="primary"):
                    with st.spinner("Actualizando estadísticas..."):
                        # Actualizar estadísticas
                        stats_result = make_api_request(f"/data/update-statistics/{current_season}", method="POST")
                        if stats_result:
                            st.success("✅ Estadísticas actualizadas")
                        
                        # Entrenar modelo
                        train_result = make_api_request(f"/model/train?season={current_season}", method="POST")
                        if train_result:
                            st.success(f"✅ Modelo entrenado con {train_result.get('training_samples', 0)} muestras")
            
            with col2:
                if st.button("🎯 Obtener Predicciones"):
                    with st.spinner("Generando predicciones detalladas..."):
                        predictions_data = make_api_request(f"/quiniela/next-matches/{current_season}")
                        
                        if predictions_data:
                            st.session_state.current_predictions = predictions_data
                            st.success(f"✅ {len(predictions_data['matches'])} partidos cargados")
            
            # Mostrar predicciones si están disponibles
            if 'current_predictions' in st.session_state:
                predictions = st.session_state.current_predictions
                
                st.subheader(f"Predicciones para {len(predictions['matches'])} Partidos")
                st.write(f"**Modelo:** {predictions.get('model_version', 'N/A')} | **Generado:** {predictions.get('generated_at', 'N/A')}")
                
                # Formulario para crear quiniela personal
                with st.form("quiniela_form"):
                    st.write("### 🎯 Rellena tu Quiniela")
                    
                    user_predictions = []
                    
                    # Mostrar cada partido con explicación y opciones
                    for i, match in enumerate(predictions['matches']):
                        st.write(f"---")
                        st.write(f"**Partido {match['match_number']}: {match['home_team']} vs {match['away_team']}**")
                        st.write(f"🏆 Liga: {match['league']} | 📅 {match.get('match_date', 'Fecha TBD')}")
                        
                        # Predicción del sistema
                        system_pred = match['prediction']
                        confidence = system_pred['confidence']
                        
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.write("**🤖 Predicción del Sistema:**")
                            st.write(f"**{system_pred['result']}** ({confidence:.1%} confianza)")
                            
                            # Probabilidades
                            st.write("**Probabilidades:**")
                            st.write(f"• Local (1): {system_pred['probabilities']['home_win']:.1%}")
                            st.write(f"• Empate (X): {system_pred['probabilities']['draw']:.1%}")
                            st.write(f"• Visitante (2): {system_pred['probabilities']['away_win']:.1%}")
                            
                            # Tu elección
                            st.write("**🎯 Tu Predicción:**")
                            user_choice = st.radio(
                                f"Partido {match['match_number']}:",
                                options=["1", "X", "2"],
                                index=["1", "X", "2"].index(system_pred['result']),
                                horizontal=True,
                                key=f"match_{match['match_number']}"
                            )
                            
                            user_predictions.append({
                                "match_number": match['match_number'],
                                "match_id": match.get('match_id'),
                                "home_team": match['home_team'],
                                "away_team": match['away_team'],
                                "user_prediction": user_choice,
                                "system_prediction": system_pred['result'],
                                "confidence": confidence,
                                "explanation": match.get('explanation', ''),
                                "prob_home": system_pred['probabilities']['home_win'],
                                "prob_draw": system_pred['probabilities']['draw'],
                                "prob_away": system_pred['probabilities']['away_win'],
                                "match_date": match.get('match_date'),
                                "league": match['league']
                            })
                        
                        with col2:
                            # Explicación expandible
                            with st.expander("📖 Ver Explicación Detallada"):
                                st.markdown(match.get('explanation', 'Explicación no disponible'))
                            
                            # Tabla de características
                            if 'features_table' in match:
                                with st.expander("📊 Características del Modelo"):
                                    features_df = pd.DataFrame(match['features_table'])
                                    if not features_df.empty:
                                        st.dataframe(features_df, use_container_width=True)
                            
                            # Estadísticas de equipos
                            if 'statistics' in match:
                                with st.expander("📈 Estadísticas de Equipos"):
                                    stats = match['statistics']
                                    
                                    col_home, col_away = st.columns(2)
                                    with col_home:
                                        st.write(f"**{match['home_team']}**")
                                        home_stats = stats['home_team']
                                        st.write(f"Victorias: {home_stats['wins']}")
                                        st.write(f"Empates: {home_stats['draws']}")
                                        st.write(f"Derrotas: {home_stats['losses']}")
                                        st.write(f"Goles a favor: {home_stats['goals_for']}")
                                        st.write(f"Goles en contra: {home_stats['goals_against']}")
                                        st.write(f"Puntos: {home_stats['points']}")
                                    
                                    with col_away:
                                        st.write(f"**{match['away_team']}**")
                                        away_stats = stats['away_team']
                                        st.write(f"Victorias: {away_stats['wins']}")
                                        st.write(f"Empates: {away_stats['draws']}")
                                        st.write(f"Derrotas: {away_stats['losses']}")
                                        st.write(f"Goles a favor: {away_stats['goals_for']}")
                                        st.write(f"Goles en contra: {away_stats['goals_against']}")
                                        st.write(f"Puntos: {away_stats['points']}")
                    
                    # Pleno al 15
                    st.write("---")
                    st.write("### 🎲 Pleno al 15")
                    st.write("*Solo válido si aciertas los 14 partidos*")
                    pleno_al_15 = st.selectbox(
                        "Predicción de goles:",
                        options=["0", "1", "2", "M"],
                        index=1,
                        help="0=0 goles, 1=1 gol, 2=2 goles, M=más de 2 goles"
                    )
                    
                    # Costo de la quiniela
                    st.write("### 💰 Información de Apuesta")
                    col1, col2 = st.columns(2)
                    with col1:
                        cost = st.number_input("Costo de la quiniela (€):", min_value=0.50, value=1.00, step=0.50)
                    with col2:
                        week_number = st.number_input("Número de jornada:", min_value=1, value=1, step=1)
                    
                    # Guardar quiniela
                    submitted = st.form_submit_button("💾 Guardar Mi Quiniela", type="primary")
                    
                    if submitted:
                        quiniela_data = {
                            "week_number": week_number,
                            "season": current_season,
                            "date": datetime.now().date().isoformat(),
                            "cost": cost,
                            "pleno_al_15": pleno_al_15,
                            "predictions": user_predictions
                        }
                        
                        with st.spinner("Guardando tu quiniela..."):
                            result = make_api_request("/quiniela/user/create", quiniela_data, method="POST")
                            
                            if result:
                                st.success(f"✅ Quiniela guardada exitosamente! ID: {result.get('id')}")
                                st.success(f"💰 Costo registrado: €{cost}")
                                st.balloons()
                                
                                # Limpiar predicciones actuales
                                if 'current_predictions' in st.session_state:
                                    del st.session_state.current_predictions
                            else:
                                st.error("❌ Error al guardar la quiniela")
            
            else:
                st.info("👆 Haz clic en 'Obtener Predicciones' para ver los próximos partidos")
        
        with subtab2:
            st.subheader("📊 Mi Historial de Quinielas")
            
            # Obtener historial
            history_data = make_api_request("/quiniela/user/history", {"season": current_season})
            
            if history_data:
                summary = history_data['summary']
                quinielas = history_data['quinielas']
                
                # Resumen general
                st.write("### 📈 Resumen General")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Quinielas", summary['total_quinielas'])
                with col2:
                    st.metric("Total Gastado", f"€{summary['total_cost']:.2f}")
                with col3:
                    profit_color = "normal" if summary['total_profit'] >= 0 else "inverse"
                    st.metric("Beneficio Total", f"€{summary['total_profit']:.2f}")
                with col4:
                    st.metric("ROI", f"{summary['roi_percentage']:.1f}%")
                
                # Tabla de quinielas
                if quinielas:
                    st.write("### 📋 Historial Detallado")
                    
                    df_quinielas = pd.DataFrame(quinielas)
                    
                    # Formatear columnas
                    df_display = df_quinielas.copy()
                    df_display['date'] = pd.to_datetime(df_display['date']).dt.strftime('%d/%m/%Y')
                    df_display['profit'] = df_display['profit'].apply(lambda x: f"€{x:.2f}")
                    df_display['cost'] = df_display['cost'].apply(lambda x: f"€{x:.2f}")
                    df_display['winnings'] = df_display['winnings'].apply(lambda x: f"€{x:.2f}")
                    df_display['accuracy'] = df_display['accuracy'].apply(lambda x: f"{x:.1%}")
                    
                    # Renombrar columnas
                    df_display = df_display.rename(columns={
                        'week_number': 'Jornada',
                        'date': 'Fecha',
                        'cost': 'Costo',
                        'winnings': 'Ganado',
                        'profit': 'Beneficio',
                        'accuracy': 'Precisión',
                        'is_finished': 'Terminada'
                    })
                    
                    st.dataframe(
                        df_display[['Jornada', 'Fecha', 'Costo', 'Ganado', 'Beneficio', 'Precisión', 'Terminada']], 
                        use_container_width=True
                    )
                    
                    # Gráficos
                    if len(quinielas) > 1:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Gráfico de beneficios acumulados
                            df_quinielas['profit_cumulative'] = df_quinielas['profit'].cumsum()
                            fig_profit = px.line(
                                df_quinielas, 
                                x='week_number', 
                                y='profit_cumulative',
                                title='Beneficio Acumulado por Jornada',
                                markers=True
                            )
                            fig_profit.update_traces(line_color='green')
                            st.plotly_chart(fig_profit, use_container_width=True)
                        
                        with col2:
                            # Gráfico de precisión
                            finished_quinielas = df_quinielas[df_quinielas['is_finished']]
                            if not finished_quinielas.empty:
                                fig_accuracy = px.line(
                                    finished_quinielas,
                                    x='week_number',
                                    y='accuracy',
                                    title='Precisión por Jornada',
                                    markers=True
                                )
                                fig_accuracy.update_layout(yaxis_tickformat='.1%')
                                st.plotly_chart(fig_accuracy, use_container_width=True)
                else:
                    st.info("No tienes quinielas guardadas aún. ¡Crea tu primera quiniela en la pestaña 'Próximos Partidos'!")
            
            else:
                st.info("No se pudieron cargar los datos del historial.")
        
        with subtab3:
            st.subheader("✅ Actualizar Resultados")
            
            # Obtener quinielas pendientes
            history_data = make_api_request("/quiniela/user/history")
            
            if history_data:
                pending_quinielas = [q for q in history_data['quinielas'] if not q['is_finished']]
                
                if pending_quinielas:
                    st.write("### 📋 Quinielas Pendientes de Resultados")
                    
                    # Seleccionar quiniela
                    quiniela_options = {f"Jornada {q['week_number']} - {q['date']} (€{q['cost']})": q for q in pending_quinielas}
                    selected_quiniela_key = st.selectbox("Selecciona la quiniela:", list(quiniela_options.keys()))
                    
                    if selected_quiniela_key:
                        selected_quiniela = quiniela_options[selected_quiniela_key]
                        
                        st.write(f"**Quiniela ID:** {selected_quiniela['id']}")
                        st.write(f"**Jornada:** {selected_quiniela['week_number']}")
                        st.write(f"**Costo:** €{selected_quiniela['cost']}")
                        
                        # Formulario para actualizar resultados
                        with st.form("results_form"):
                            st.write("### 🏆 Resultados Reales")
                            
                            # Aquí necesitarías obtener las predicciones específicas de esta quiniela
                            # Por simplicidad, creamos campos genéricos
                            results = []
                            for i in range(1, 15):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"**Partido {i}:**")
                                with col2:
                                    result = st.selectbox(
                                        f"Resultado:",
                                        options=["1", "X", "2"],
                                        key=f"result_{i}",
                                        label_visibility="collapsed"
                                    )
                                    results.append({"match_number": i, "actual_result": result})
                            
                            # Ganancias
                            winnings = st.number_input("💰 ¿Cuánto ganaste? (€):", min_value=0.0, value=0.0, step=0.1)
                            
                            # Actualizar resultados
                            submitted = st.form_submit_button("💾 Actualizar Resultados", type="primary")
                            
                            if submitted:
                                results_data = {
                                    "winnings": winnings,
                                    "results": results
                                }
                                
                                with st.spinner("Actualizando resultados..."):
                                    result = make_api_request(
                                        f"/quiniela/user/{selected_quiniela['id']}/results", 
                                        results_data, 
                                        method="PUT"
                                    )
                                    
                                    if result:
                                        st.success("✅ Resultados actualizados exitosamente!")
                                        st.success(f"🎯 Aciertos: {result.get('correct_predictions', 0)}/14")
                                        st.success(f"📊 Precisión: {result.get('accuracy', 0):.1%}")
                                        st.success(f"💰 Beneficio: €{result.get('profit', 0):.2f}")
                                        st.balloons()
                                    else:
                                        st.error("❌ Error al actualizar los resultados")
                
                else:
                    st.info("No tienes quinielas pendientes de actualizar.")
            
            else:
                st.info("No se pudieron cargar los datos.")

    with tab2:
        st.header("📊 Predicciones del Sistema")
        
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

    with tab3:
        st.header("📈 Rendimiento Histórico")
        
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
    
    with tab4:
        st.header("💰 Análisis Financiero")
        
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
    
    with tab5:
        st.header("🔧 Gestión de Datos")
        
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
    
    with tab6:
        st.header("🤖 Gestión del Modelo de Machine Learning")
        
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