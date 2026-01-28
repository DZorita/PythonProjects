-- Ejecuta esto en tu PostgreSQL
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    foto_cara BYTEA NOT NULL, -- La foto recortada para entrenamiento
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
