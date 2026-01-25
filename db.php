<?php
// 1. Datos de conexión de Railway
$host = "postgres.railway.internal"; 
$port = "23725";
$dbname = "railway";
$user = "postgres";
$password = "KEkNqLjIOIcOExyUYAoHjIEtyCzHpZAM";

// 2. Cambiamos $conn por $db_connection para que coincida con el login
$db_connection = pg_connect("host=$host port=$port dbname=$dbname user=$user password=$password");

// 3. Verificación de seguridad
if (!$db_connection) {
        die("Error crítico: No se pudo conectar a la base de datos de GeoMonitor.");
}
?>