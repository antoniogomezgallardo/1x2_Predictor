-- Agregar columnas faltantes a la tabla user_quinielas
-- Este script corrige el error: column user_quinielas.pleno_al_15_home does not exist

-- Verificar si las columnas ya existen antes de agregarlas
DO $$
BEGIN
    -- Agregar columna pleno_al_15_home si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_quinielas' 
                   AND column_name = 'pleno_al_15_home') THEN
        ALTER TABLE user_quinielas ADD COLUMN pleno_al_15_home VARCHAR(1);
    END IF;
    
    -- Agregar columna pleno_al_15_away si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_quinielas' 
                   AND column_name = 'pleno_al_15_away') THEN
        ALTER TABLE user_quinielas ADD COLUMN pleno_al_15_away VARCHAR(1);
    END IF;
END
$$;

-- Verificar que las columnas se agregaron correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_quinielas' 
AND column_name IN ('pleno_al_15_home', 'pleno_al_15_away');