-- =============================================================
-- Datos de ejemplo para desarrollo y pruebas
-- Ejecutar DESPUÉS de schema.sql:
--   mysql -u <user> -p <db> < db/seed.sql
--
-- Credenciales de demo:
--   admin@demo.cl   / Admin1234
--   usuario@demo.cl / Usuario1234
--
-- Los hashes fueron generados con:
--   hashlib.pbkdf2_hmac('sha256', password.encode(), salt_bytes, 200_000)
-- =============================================================

-- Limpiar datos previos (orden inverso de FKs)
DELETE FROM reservas;
DELETE FROM espacios;
DELETE FROM usuarios;

-- Usuarios demo
INSERT INTO usuarios (nombre, email, salt, password_hash, rol) VALUES
(
    'Administrador Demo',
    'admin@demo.cl',
    '8a185f7e5c7c4900f0bfee4b86e328ec',
    'b043954862d28f98e0c3501e970ad442d7d75050697bb68dcc62c68ec54c8fa8',
    'admin'
),
(
    'Usuario Demo',
    'usuario@demo.cl',
    '934acab0cdc73d3bf9fc1827a00237e5',
    '8a1f5c2983126585da23c6cc77000b015edc629d82147d3deebd3c318b63e8f4',
    'usuario'
);

-- Espacios de ejemplo
INSERT INTO espacios (nombre, descripcion, capacidad) VALUES
('Sala de Reuniones A', 'Sala equipada con proyector y pizarra, capacidad para 10 personas.', 10),
('Sala de Reuniones B', 'Sala pequeña para reuniones de equipo, hasta 6 personas.', 6),
('Auditorio Principal', 'Espacio amplio con sistema de sonido y pantalla de proyección.', 80),
('Sala de Capacitación', 'Computadores disponibles, laboratorio de entrenamiento.', 25);
