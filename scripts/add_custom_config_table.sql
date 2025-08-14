-- Script para agregar la tabla custom_quiniela_configs
-- Ejecutar solo si la tabla no existe

CREATE TABLE IF NOT EXISTS custom_quiniela_configs (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    selected_match_ids JSON NOT NULL,
    pleno_al_15_match_id INTEGER NOT NULL,
    total_matches INTEGER DEFAULT 15,
    la_liga_count INTEGER DEFAULT 0,
    segunda_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_by_user BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_custom_quiniela_season_week ON custom_quiniela_configs(season, week_number);
CREATE INDEX IF NOT EXISTS idx_custom_quiniela_active ON custom_quiniela_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_custom_quiniela_created_at ON custom_quiniela_configs(created_at);

-- Comentario sobre la tabla
COMMENT ON TABLE custom_quiniela_configs IS 'Configuraciones personalizadas de Quiniela seleccionadas manualmente por el usuario';
COMMENT ON COLUMN custom_quiniela_configs.selected_match_ids IS 'Array JSON con los IDs de los 15 partidos seleccionados';
COMMENT ON COLUMN custom_quiniela_configs.pleno_al_15_match_id IS 'ID del partido designado como Pleno al 15';