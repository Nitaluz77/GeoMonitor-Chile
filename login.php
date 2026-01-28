<?php
//Conecta a la base de datos
require_once __DIR__ . '/config/db.php'; 

//Configuraciones para que el mapa no se rompa
header('Content-Type: application/json');
ini_set('display_errors', 0);

// 1. Configuraciones de seguridad y formato
header('Content-Type: application/json');
ini_set('display_errors', 0); 

try {
    // 2. Conectamos a la base de datos
    $db_path = __DIR__ . '/config/db.php';
    if (!file_exists($db_path)) {
        throw new Exception("Archivo de configuración db.php no encontrado.");
    }
    require_once $db_path;

    // 3. Recibimos los datos 
    $usuario = $_POST['usuario'] ?? '';
    $password = $_POST['password'] ?? '';

    // 4. Validación ---
    if ($usuario === 'admin' && $password === '1234') {
        echo json_encode([
            "success" => true, 
            "message" => "¡Bienvenido al GeoMonitor!",
            "user" => "Administrador"
        ]);
    } else {
        throw new Exception("Usuario o contraseña incorrectos.");
    }

} catch (Exception $e) {
    // 5. Error 
    http_response_code(400);
    echo json_encode([
        "success" => false, 
        "error" => $e->getMessage()
    ]);
}
exit;