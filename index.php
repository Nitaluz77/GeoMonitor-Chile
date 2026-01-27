<?php
session_start();
equire_once __DIR__ . '/config/db.php'; // Llama conexión de Railway

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // 1. Limpiamos los datos para evitar inyecciones básicas
    $user_input = htmlspecialchars($_POST['usuario']);
    $pass_input = $_POST['password'];

    try {
        // 2. Buscamos al usuario en la base de datos PostgreSQL
        $query = "SELECT password, rol FROM usuario WHERE email = $1";
        $result = pg_query_params($db_connection, $query, array($user_input));

        if ($user_data = pg_fetch_assoc($result)) {
            
            // 3. Verificamos la contraseña            
if ($pass_input === $user_data['password']) {
    $_SESSION['usuario'] = $user_input;
    
    // Convertimos el número id_rol en el nombre del perfil
    if ($user_data['id_rol'] == 1) {
        $_SESSION['perfil'] = 'admin';
    } else {
        $_SESSION['perfil'] = 'consultor';
    }
    
    header("Location: mapa.php");
    exit();
}
            else {
                $error = "Contraseña incorrecta.";
            }
        } else {
            $error = "El usuario no existe en el sistema.";
        }
    } catch (Exception $e) {
        $error = "Error de conexión con el servidor de datos.";
    }
}
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Acceso - GeoMonitor Chile</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f0f4f8; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        h2 { color: #1a5f7a; margin-bottom: 1.5rem; }
        input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #1a5f7a; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #13455a; }
        .error { color: #d9534f; font-size: 0.9rem; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>GeoMonitor Chile</h2>
        <p>Control de Acceso</p>
        <form method="POST">
            <input type="email" name="usuario" placeholder="Correo Electrónico" required>
            <input type="password" name="password" placeholder="Contraseña" required>
            <button type="submit">Iniciar Sesión</button>
        </form>
        <?php if(isset($error)) echo "<p class='error'>$error</p>"; ?>
    </div>
</body>
</html>