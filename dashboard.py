import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
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


def make_api_request(endpoint: str, params: dict = None, method: str = "GET", show_debug: bool = False):
    """Make request to API"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if show_debug:
            st.write(f"🔧 DEBUG: Making {method} request to: {url}")
        
        if method == "POST":
            response = requests.post(url, json=params, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, params=params, timeout=30)
        else:
            response = requests.get(url, params=params, timeout=30)
        
        if show_debug:
            st.write(f"🔧 DEBUG: Response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        if show_debug:
            st.write(f"🔧 DEBUG: Response data: {result}")
        return result
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        if show_debug:
            st.write(f"🔧 DEBUG: Full error: {e}")
        return None


def display_prediction_card(prediction):
    """Display a prediction card"""
    # Usar 'prediction' en lugar de 'predicted_result'
    predicted_result = prediction.get('prediction', prediction.get('predicted_result', 'X'))
    result_class = f"result-{predicted_result}"
    
    # Manejo seguro de confianza
    confidence = prediction.get('confidence', 0.5)
    confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.5 else "red"
    
    # Manejo seguro de probabilidades
    probabilities = prediction.get('probabilities', {})
    home_win = probabilities.get('home_win', 0.33)
    draw = probabilities.get('draw', 0.33)
    away_win = probabilities.get('away_win', 0.33)
    
    st.markdown(f"""
    <div class="prediction-card {result_class}">
        <h4>Partido {prediction.get('match_number', '?')}: {prediction.get('home_team', '?')} vs {prediction.get('away_team', '?')}</h4>
        <p><strong>Predicción:</strong> {predicted_result} 
           <span style="color: {confidence_color}">({confidence:.1%} confianza)</span></p>
        <div style="display: flex; justify-content: space-between;">
            <span>Local: {home_win:.1%}</span>
            <span>Empate: {draw:.1%}</span>
            <span>Visitante: {away_win:.1%}</span>
        </div>
        <small>Fecha: {prediction.get('match_date', 'N/A')}</small>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.title("⚽ Quiniela Predictor Dashboard")
    st.markdown("Sistema de predicción de resultados para la Quiniela Española")
    
    # Sidebar
    st.sidebar.title("Configuración")
    current_season = st.sidebar.selectbox("Temporada", [2025, 2024, 2023], index=0)
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎯 Mi Quiniela", 
        "📊 Predicciones Actuales", 
        "📈 Rendimiento", 
        "💰 Análisis Financiero",
        "🔧 Gestión de Datos",
        "🤖 Modelo ML",
        "📋 Reglas Oficiales"
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
                
                # Mostrar nota si se usan datos de temporada anterior
                if predictions.get('note'):
                    st.info(f"ℹ️ {predictions['note']}")
                
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
                    st.write("### 🏆 Pleno al 15")
                    st.write("*Predicción adicional para el partido 15. Se marca con X la casilla del resultado elegido.*")
                    
                    # Obtener datos del partido 15 si están disponibles
                    if len(predictions['matches']) >= 15:
                        partido_15 = predictions['matches'][14]  # Index 14 = partido 15
                        st.write(f"**Partido 15**: {partido_15.get('home_team', 'Equipo A')} vs {partido_15.get('away_team', 'Equipo B')}")
                    else:
                        st.write("**Partido 15**: Equipo A vs Equipo B")
                    
                    pleno_opciones = {
                        "1": "🏠 Equipo local gana",
                        "X": "🤝 Empate",
                        "2": "✈️ Equipo visitante gana", 
                        "M": "⚽ Un equipo marca 3+ goles"
                    }
                    
                    pleno_al_15 = st.selectbox(
                        "Selecciona tu pronóstico para el Pleno al 15:",
                        options=list(pleno_opciones.keys()),
                        format_func=lambda x: pleno_opciones[x],
                        index=1,
                        help="Según las reglas oficiales: 1=Local gana, X=Empate, 2=Visitante gana, M=Un equipo marca 3 o más goles"
                    )
                    
                    # Costo de la quiniela (usando precios oficiales)
                    st.write("### 💰 Información de Apuesta")
                    
                    # Precio oficial fijo
                    precio_oficial = 0.75  # €0.75 según normativa oficial
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Costo por Apuesta", f"€{precio_oficial:.2f}", help="Precio oficial según Loterías y Apuestas del Estado")
                    with col2:
                        num_apuestas = st.number_input("Número de apuestas:", min_value=1, max_value=8, value=1, step=1,
                                                     help="Modalidad Simple: 1-8 apuestas por boleto")
                    with col3:
                        costo_total = precio_oficial * num_apuestas
                        st.metric("🧾 Costo Total", f"€{costo_total:.2f}")
                    
                    st.info(f"ℹ️ **Modalidad**: Simple ({num_apuestas} apuesta{'s' if num_apuestas > 1 else ''}) - Total: €{costo_total:.2f}")
                    
                    week_number = st.number_input("Número de jornada:", min_value=1, value=1, step=1)
                    
                    # Guardar quiniela
                    submitted = st.form_submit_button("💾 Guardar Mi Quiniela", type="primary")
                    
                    if submitted:
                        quiniela_data = {
                            "week_number": week_number,
                            "season": current_season,
                            "date": datetime.now().date().isoformat(),
                            "cost": costo_total,
                            "pleno_al_15": pleno_al_15,
                            "predictions": user_predictions
                        }
                        
                        with st.spinner("Guardando tu quiniela..."):
                            result = make_api_request("/quiniela/user/create", quiniela_data, method="POST")
                            
                            if result:
                                st.success(f"✅ Quiniela guardada exitosamente! ID: {result.get('id')}")
                                st.success(f"💰 Costo registrado: €{costo_total:.2f}")
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
                    
                    # Formulario para actualizar resultados
                    with st.form("results_form"):
                        # Seleccionar quiniela
                        quiniela_options = {f"Jornada {q['week_number']} - {q['date']} (€{q['cost']})": q for q in pending_quinielas}
                        selected_quiniela_key = st.selectbox("Selecciona la quiniela:", list(quiniela_options.keys()))
                        
                        if selected_quiniela_key:
                            selected_quiniela = quiniela_options[selected_quiniela_key]
                            
                            st.write(f"**Quiniela ID:** {selected_quiniela['id']}")
                            st.write(f"**Jornada:** {selected_quiniela['week_number']}")
                            st.write(f"**Costo:** €{selected_quiniela['cost']}")
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
        
        if predictions_data and predictions_data.get('predictions'):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Temporada", predictions_data['season'])
            
            with col2:
                week_num = predictions_data.get('week_number') or 'N/A'
                st.metric("Jornada", week_num)
            
            with col3:
                # Calcular confianza media de forma segura
                predictions = predictions_data['predictions']
                if predictions and len(predictions) > 0:
                    avg_confidence = sum(p.get('confidence', 0.5) for p in predictions) / len(predictions)
                    st.metric("Confianza Media", f"{avg_confidence:.1%}")
                else:
                    st.metric("Confianza Media", "N/A")
            
            with col4:
                st.metric("Versión Modelo", predictions_data.get('model_version', 'N/A'))
            
            st.subheader("Predicciones por Partido")
            
            # Display predictions
            for prediction in predictions_data['predictions']:
                display_prediction_card(prediction)
            
            # Betting strategy (si existe)
            if 'betting_strategy' in predictions_data and predictions_data['betting_strategy']:
                st.subheader("Estrategia de Apuestas Recomendada")
                betting = predictions_data['betting_strategy']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total a Apostar", f"€{betting.get('total_stake', 0):.2f}")
                with col2:
                    st.metric("Número de Apuestas", betting.get('number_of_bets', 0))
                with col3:
                    st.metric("% del Bankroll", f"{betting.get('percentage_of_bankroll', 0):.1f}%")
                
                if betting.get('recommended_bets'):
                    st.subheader("Apuestas Recomendadas")
                    bet_df = pd.DataFrame(betting['recommended_bets'])
                    st.dataframe(bet_df[['match_number', 'home_team', 'away_team', 'predicted_result', 'confidence', 'recommended_bet']])
            else:
                st.info("💡 Estrategia de apuestas disponible cuando el modelo esté entrenado")
        
        else:
            # Manejar casos donde no hay predicciones
            if predictions_data:
                if predictions_data.get('model_trained') == False:
                    st.info("🤖 **Modelo no entrenado**")
                    st.write("Para ver predicciones, primero necesitas entrenar el modelo:")
                    st.write("1. Ve a la pestaña '🤖 Modelo ML'")
                    st.write("2. Haz clic en 'Entrenar Nuevo Modelo'")
                    st.write("3. Espera 10-15 minutos")
                    st.write("4. ¡Regresa aquí para ver las predicciones!")
                elif not predictions_data.get('predictions'):
                    st.warning("📅 **No hay partidos disponibles**")
                    st.write("No se encontraron partidos para mostrar predicciones.")
                    st.write("Esto puede deberse a:")
                    st.write("- No hay partidos próximos en la base de datos")
                    st.write("- Necesitas actualizar los datos de partidos")
                else:
                    st.warning("⚠️ No se pudieron obtener las predicciones")
            else:
                st.error("❌ **Error de conexión**")
                st.write("No se pudo conectar con la API. Verifica que los servicios estén funcionando.")

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
            
            st.write("**Actualizar datos de la temporada:**")
            
            # Función para monitorear progreso
            def monitor_update_progress(update_type, initial_count, expected_count, check_field):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                import time
                for i in range(30):  # Máximo 30 iteraciones (5 minutos)
                    time.sleep(10)  # Esperar 10 segundos entre checks
                    
                    # Obtener estado actual
                    current_status = make_api_request(f"/data/status/{current_season}")
                    if current_status:
                        current_count = current_status.get(check_field, initial_count)
                        
                        # Calcular progreso con límite máximo de 1.0
                        if expected_count <= initial_count:
                            progress = 1.0 if current_count > initial_count else 0.0
                        else:
                            progress = min((current_count - initial_count) / (expected_count - initial_count), 1.0)
                        
                        progress_bar.progress(max(0.0, progress))  # Asegurar que no sea negativo
                        
                        # Determinar si está completo
                        is_complete = (current_count >= expected_count) or (progress >= 1.0) or (current_count > initial_count and i > 3)
                        
                        if is_complete:
                            status_text.success(f"✅ Actualización de {update_type} completada! ({current_count} registros)")
                            progress_bar.progress(1.0)
                            break
                        else:
                            status_text.info(f"⏳ Actualizando {update_type}... ({current_count} registros)")
                    else:
                        status_text.warning("⚠️ No se pudo verificar el progreso")
                        break
                
                return current_count if current_status else initial_count
            
            if st.button("🏈 Actualizar Equipos", type="primary", key="btn_teams"):
                # Obtener estado inicial
                initial_status = make_api_request(f"/data/status/{current_season}")
                initial_teams = initial_status.get('teams_total', 0) if initial_status else 0
                
                # Iniciar actualización
                result = make_api_request(f"/data/update-teams/{current_season}", method="POST")
                if result:
                    st.info(f"🚀 {result.get('message', 'Actualización iniciada')}")
                    
                    # Monitorear progreso
                    with st.container():
                        st.write("**Monitoreando progreso:**")
                        monitor_update_progress("equipos", initial_teams, 40, "teams_total")
                else:
                    st.error("❌ Error al iniciar actualización de equipos")
            
            if st.button("⚽ Actualizar Partidos", key="btn_matches"):
                # Obtener estado inicial
                initial_status = make_api_request(f"/data/status/{current_season}")
                initial_matches = initial_status.get('matches_total', 0) if initial_status else 0
                
                # Iniciar actualización
                result = make_api_request(f"/data/update-matches/{current_season}", method="POST")
                if result:
                    # Check if this is a validation response
                    if 'warning' in result and 'recommendation' in result:
                        # This is a validation message, not a successful start
                        st.warning(f"⚠️ {result.get('message', 'Validación')}")
                        if result.get('warning'):
                            st.info(f"ℹ️ {result['warning']}")
                        if result.get('recommendation'):
                            st.info(f"💡 {result['recommendation']}")
                    else:
                        # This is a successful start, monitor progress
                        st.info(f"🚀 {result.get('message', 'Actualización iniciada')}")
                        
                        # Monitorear progreso
                        with st.container():
                            st.write("**Monitoreando progreso:**")
                            monitor_update_progress("partidos", initial_matches, 760, "matches_total")
                else:
                    st.error("❌ Error al iniciar actualización de partidos")
            
            if st.button("📊 Actualizar Estadísticas", key="btn_stats"):
                # Obtener estado inicial
                initial_status = make_api_request(f"/data/status/{current_season}")
                initial_stats = initial_status.get('team_statistics_total', 0) if initial_status else 0
                
                # Iniciar actualización
                result = make_api_request(f"/data/update-statistics/{current_season}", method="POST")
                if result:
                    # Check if this is a validation response
                    if 'warning' in result and 'recommendation' in result:
                        # This is a validation message, not a successful start
                        st.warning(f"⚠️ {result.get('message', 'Validación')}")
                        if result.get('warning'):
                            st.info(f"ℹ️ {result['warning']}")
                        if result.get('recommendation'):
                            st.info(f"💡 {result['recommendation']}")
                    else:
                        # This is a successful start, monitor progress
                        st.info(f"🚀 {result.get('message', 'Actualización iniciada')}")
                        
                        # Monitorear progreso
                        with st.container():
                            st.write("**Monitoreando progreso:**")
                            monitor_update_progress("estadísticas", initial_stats, 40, "team_statistics_total")
                else:
                    st.error("❌ Error al iniciar actualización de estadísticas")
        
        with col2:
            st.subheader("Estado de los Datos")
            
            # Botón para refrescar estado
            if st.button("🔄 Refrescar Estado", key="btn_refresh"):
                st.rerun()
            
            # Obtener estado actual de los datos
            status_data = make_api_request(f"/data/status/{current_season}")
            
            if status_data:
                # Métricas principales
                col2_1, col2_2 = st.columns(2)
                
                with col2_1:
                    teams_progress = min(status_data['teams_total'] / max(status_data['teams_expected'], 1), 1.0)
                    st.metric(
                        "Equipos", 
                        f"{status_data['teams_total']}/{status_data['teams_expected']}", 
                        delta="✅ Completo" if status_data['teams_total'] >= status_data['teams_expected'] else f"{teams_progress:.1%} completo"
                    )
                    
                    matches_progress = min(status_data['matches_total'] / max(status_data['matches_expected_per_season'], 1), 1.0) if status_data['matches_expected_per_season'] > 0 else 0
                    st.metric(
                        "Partidos", 
                        f"{status_data['matches_total']}", 
                        delta=f"{status_data['matches_total']} cargados"
                    )
                
                with col2_2:
                    st.metric(
                        "Partidos c/Resultados", 
                        f"{status_data['matches_with_results']}"
                    )
                    
                    stats_progress = min(status_data['team_statistics_total'] / max(status_data['stats_expected'], 1), 1.0) if status_data['stats_expected'] > 0 else 0
                    st.metric(
                        "Estadísticas", 
                        f"{status_data['team_statistics_total']}/{status_data['stats_expected']}", 
                        delta="✅ Completo" if status_data['team_statistics_total'] >= status_data['stats_expected'] else f"{stats_progress:.1%} completo"
                    )
                
                # Barras de progreso visuales
                st.write("**Progreso de Datos:**")
                
                st.write("Equipos:")
                st.progress(teams_progress)
                
                st.write("Estadísticas:")
                st.progress(stats_progress)
                
                # Fechas de última actualización
                if status_data['last_match_update']:
                    from datetime import datetime
                    last_update = datetime.fromisoformat(status_data['last_match_update'].replace('Z', '+00:00'))
                    st.write(f"**Última actualización partidos:** {last_update.strftime('%Y-%m-%d %H:%M')}")
                
                if status_data['last_stats_update']:
                    last_stats = datetime.fromisoformat(status_data['last_stats_update'].replace('Z', '+00:00'))
                    st.write(f"**Última actualización estadísticas:** {last_stats.strftime('%Y-%m-%d %H:%M')}")
                
            else:
                st.warning("⚠️ No se pudo obtener el estado de los datos")
                st.info("Asegúrate de que la API esté funcionando correctamente")
            
            # Sección de borrar datos
            st.markdown("---")
            st.subheader("🗑️ Borrar Datos")
            st.error("⚠️ **ZONA PELIGROSA** - Esta acción NO se puede deshacer")
            
            with st.expander("🚨 Borrar TODOS los datos de la base de datos"):
                st.markdown("""
                **Esta acción eliminará TODOS los datos:**
                - ❌ Todos los equipos
                - ❌ Todos los partidos 
                - ❌ Todas las estadísticas
                - ❌ Todas las quinielas guardadas
                - ❌ Todo el historial
                
                **⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️**
                """)
                
                # Requerir confirmación explícita
                confirm_delete = st.text_input(
                    "Para confirmar, escribe: BORRAR_TODO",
                    placeholder="Escribe BORRAR_TODO para confirmar",
                    key="confirm_delete_input"
                )
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    delete_enabled = confirm_delete == "BORRAR_TODO"
                    
                    if st.button(
                        "🗑️ BORRAR TODOS LOS DATOS", 
                        type="primary" if delete_enabled else "secondary",
                        disabled=not delete_enabled,
                        key="btn_delete_all"
                    ):
                        if delete_enabled:
                            with st.spinner("🗑️ Borrando todos los datos..."):
                                # Llamar al endpoint de borrar datos
                                result = make_api_request(
                                    "/data/clear-all?confirm=DELETE_ALL_DATA", 
                                    method="DELETE"
                                )
                                
                                if result:
                                    st.success("✅ Todos los datos han sido borrados exitosamente")
                                    
                                    # Mostrar resumen de lo que se borró
                                    if 'records_deleted' in result:
                                        deleted = result['records_deleted']
                                        st.info(f"""
                                        **Registros eliminados:**
                                        - Equipos: {deleted.get('teams', 0)}
                                        - Partidos: {deleted.get('matches', 0)}  
                                        - Estadísticas: {deleted.get('team_statistics', 0)}
                                        - Quinielas: {deleted.get('user_quinielas', 0)}
                                        - Predicciones: {deleted.get('user_quiniela_predictions', 0)}
                                        """)
                                    
                                    # Mostrar próximos pasos
                                    if 'next_steps' in result:
                                        st.info("**Próximos pasos recomendados:**")
                                        for step in result['next_steps']:
                                            st.write(f"• {step}")
                                    
                                    # Refrescar la página
                                    st.rerun()
                                else:
                                    st.error("❌ Error al borrar los datos")
                        else:
                            st.error("⚠️ Debes escribir 'BORRAR_TODO' para confirmar")
                
                with col_btn2:
                    st.write("")  # Espaciado
                    if st.button("❌ Cancelar", key="btn_cancel_delete"):
                        st.rerun()
    
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
                    # Llamar al endpoint con season como query parameter
                    result = make_api_request(f"/model/train?season={current_season}", method="POST")
                    if result:
                        st.success(f"✅ Entrenamiento iniciado con {result.get('training_samples', 'N/A')} muestras")
                        st.info("⏳ El entrenamiento se ejecuta en segundo plano. Actualiza la página en unos minutos.")
                    else:
                        st.error("❌ Error al iniciar el entrenamiento del modelo")
            
            st.subheader("Configuración del Modelo")
            st.info("Configuración actual:")
            st.code("""
Algoritmos: Random Forest + XGBoost (Ensemble)
Características: ~30 variables
Validación: 5-fold cross-validation
Métricas: Accuracy, Precision, Recall, F1-Score
            """)

    with tab7:
        st.header("📋 Reglas Oficiales de la Quiniela Española")
        
        # Información general
        st.markdown("""
        ### ℹ️ Información General
        La Quiniela es una apuesta deportiva oficial regulada por **Loterías y Apuestas del Estado** donde se pronostican 
        los resultados de partidos de fútbol de **La Liga** y **Segunda División**.
        """)
        
        # Formato de juego
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Formato de Juego")
            st.markdown("""
            - **14 partidos principales**: Pronosticar 1 (local gana), X (empate), o 2 (visitante gana)
            - **Pleno al 15**: Partido especial con opciones adicionales
            - **Precio oficial**: €0.75 por apuesta simple
            - **Modalidades**: Simple, Múltiple, Reducidas, Elige 8
            """)
            
            st.subheader("🏆 Pleno al 15")
            st.markdown("""
            **Opciones disponibles:**
            - **1**: Equipo local gana
            - **X**: Empate  
            - **2**: Equipo visitante gana
            - **M**: Un equipo marca 3 o más goles
            
            *Solo válido si aciertas los 14 partidos principales*
            """)
        
        with col2:
            st.subheader("🏅 Categorías de Premios")
            
            premios_data = [
                {"Categoría": "Especial", "Requisito": "14 aciertos + Pleno al 15", "Color": "🥇"},
                {"Categoría": "1ª", "Requisito": "14 aciertos", "Color": "🥈"},
                {"Categoría": "2ª", "Requisito": "13 aciertos", "Color": "🥉"},
                {"Categoría": "3ª", "Requisito": "12 aciertos", "Color": "🏆"},
                {"Categoría": "4ª", "Requisito": "11 aciertos", "Color": "🎖️"},
                {"Categoría": "5ª", "Requisito": "10 aciertos", "Color": "🎗️"}
            ]
            
            for premio in premios_data:
                st.markdown(f"**{premio['Color']} {premio['Categoría']}**: {premio['Requisito']}")
        
        # Modalidades de juego
        st.subheader("🎲 Modalidades de Juego")
        
        modalidad_tab1, modalidad_tab2, modalidad_tab3, modalidad_tab4 = st.tabs([
            "Simple", "Múltiple Directo", "Múltiple Reducido", "Elige 8"
        ])
        
        with modalidad_tab1:
            st.markdown("""
            ### 📝 Modalidad Simple
            - **Descripción**: De 1 a 8 apuestas diferentes en un mismo boleto
            - **Precio**: €0.75 por cada apuesta
            - **Ejemplo**: 3 apuestas simples = 3 × €0.75 = €2.25
            
            **Implementación actual**: ✅ Disponible en "Mi Quiniela Personal"
            """)
        
        with modalidad_tab2:
            st.markdown("""
            ### 🎯 Múltiple Directo
            - **Descripción**: Combinar varios pronósticos en un mismo partido
            - **Doble**: 2 opciones por partido (ej: 1X significa 1 ó X)
            - **Triple**: 3 opciones por partido (ej: 1X2 significa cualquier resultado)
            - **Costo**: Se multiplican las combinaciones × €0.75
            
            **Ejemplo**: 2 dobles = 2² × €0.75 = 4 × €0.75 = €3.00
            
            **Estado**: ❌ No implementado aún
            """)
        
        with modalidad_tab3:
            st.markdown("""
            ### 📊 Múltiple Reducido (6 Tipos Oficiales)
            
            **Reducidas autorizadas por BOE:**
            """)
            
            reducidas_data = [
                {"Tipo": "1", "Descripción": "4 triples", "Apuestas": "9/81", "Precio": "€6.75"},
                {"Tipo": "2", "Descripción": "7 dobles", "Apuestas": "16/128", "Precio": "€12.00"},
                {"Tipo": "3", "Descripción": "3 dobles + 3 triples", "Apuestas": "24/216", "Precio": "€18.00"},
                {"Tipo": "4", "Descripción": "2 triples + 6 dobles", "Apuestas": "64/576", "Precio": "€48.00"},
                {"Tipo": "5", "Descripción": "8 triples", "Apuestas": "81/6561", "Precio": "€60.75"},
                {"Tipo": "6", "Descripción": "11 dobles", "Apuestas": "132/2048", "Precio": "€99.00"}
            ]
            
            df_reducidas = pd.DataFrame(reducidas_data)
            st.dataframe(df_reducidas, use_container_width=True)
            
            st.info("**Estado**: ❌ No implementado aún - Planificado para futuras versiones")
        
        with modalidad_tab4:
            st.markdown("""
            ### 🎪 Elige 8
            - **Descripción**: Modalidad adicional que se juega junto a una Quiniela normal
            - **Precio**: €0.50 adicional
            - **Mecánica**: Seleccionar 8 de los 14 partidos y apostar sobre ellos
            - **Premios**: Según número de aciertos (1 a 8)
            
            **Estado**: ❌ No implementado aún
            """)
        
        # Implementación actual vs reglas oficiales
        st.subheader("🔄 Estado de Implementación")
        
        implementacion_col1, implementacion_col2 = st.columns(2)
        
        with implementacion_col1:
            st.markdown("""
            ### ✅ **Implementado**
            - ✅ Formato básico (14 + Pleno al 15)
            - ✅ Opciones correctas (1, X, 2, M)
            - ✅ Precios oficiales (€0.75)
            - ✅ Modalidad Simple (1-8 apuestas)
            - ✅ Sistema de validación de temporadas
            - ✅ Interfaz intuitiva para crear quinielas
            """)
        
        with implementacion_col2:
            st.markdown("""
            ### ⏳ **Pendiente de Implementar**
            - ❌ Múltiple Directo
            - ❌ Las 6 Reducidas Oficiales
            - ❌ Múltiple Condicionado  
            - ❌ Modalidad Elige 8
            - ❌ Sistema de premios completo
            - ❌ Cálculo automático de probabilidades de ganar
            """)
        
        # Disclaimers legales
        st.subheader("⚠️ Información Legal")
        st.warning("""
        **Disclaimer**: Esta aplicación es para fines educativos y de análisis. Las reglas mostradas están basadas en la 
        normativa oficial de Loterías y Apuestas del Estado. Para jugar oficialmente, utiliza los canales autorizados.
        
        **Juego Responsable**: Apuesta solo dinero que puedas permitirte perder. Si crees que puedes tener un problema 
        con el juego, busca ayuda profesional.
        """)
        
        st.info("""
        **Fuente**: Reglas basadas en la Resolución de 6 de julio de 2009 de Loterías y Apuestas del Estado, 
        publicada en el BOE el 23 de julio de 2009.
        """)


if __name__ == "__main__":
    main()