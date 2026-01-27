<?php
// 1. Datos de conexión de Railway
$host = getenv('PGHOST') ?: "postgres.railway.internal";
$user = getenv('PGUSER') ?: "postgres";
$password = getenv('PGPASSWORD') ?: "TU_CLAVE_AQUI";
$dbname = getenv('PGDATABASE') ?: "railway";
$port = getenv('PGPORT') ?: "23725";

// 2. Cambiamos $conn por $db_connection para que coincida con el login
$db_connection = pg_connect("host=$host port=$port dbname=$dbname user=$user password=$password");

// 3. Verificación de seguridad
if (!$db_connection) {
        die("Error crítico: No se pudo conectar a la base de datos de GeoMonitor.");
}
?>