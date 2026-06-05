-- =============================================================
-- Sistema de Reservas — DDL
-- Motor: MySQL 5.7+ / MariaDB 10.3+
-- Ejecutar: mysql -u <user> -p <db> < db/schema.sql
-- =============================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- -------------------------------------------------------------
-- Tabla: usuarios
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id            INT          NOT NULL AUTO_INCREMENT,
    nombre        VARCHAR(120) NOT NULL,
    email         VARCHAR(200) NOT NULL,
    salt          VARCHAR(32)  NOT NULL,          -- 16 bytes → 32 hex chars
    password_hash VARCHAR(64)  NOT NULL,           -- SHA-256 → 32 bytes → 64 hex
    rol           ENUM('admin','usuario') NOT NULL DEFAULT 'usuario',
    creado_en     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuarios_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- Tabla: espacios
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS espacios (
    id          INT          NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(120) NOT NULL,
    descripcion TEXT,
    capacidad   INT          NOT NULL DEFAULT 1,
    creado_en   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- Tabla: reservas
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservas (
    id         INT      NOT NULL AUTO_INCREMENT,
    usuario_id INT      NOT NULL,
    espacio_id INT      NOT NULL,
    inicio     DATETIME NOT NULL,
    fin        DATETIME NOT NULL,
    estado     ENUM('activa','cancelada') NOT NULL DEFAULT 'activa',
    creado_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_reservas_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_reservas_espacio FOREIGN KEY (espacio_id)
        REFERENCES espacios (id) ON DELETE CASCADE,
    -- Índice compuesto para acelerar la consulta de solapamiento:
    --   WHERE espacio_id = ? AND estado = 'activa' AND inicio < ? AND fin > ?
    INDEX idx_reservas_solapamiento (espacio_id, estado, inicio, fin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
