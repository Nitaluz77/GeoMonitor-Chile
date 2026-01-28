<?php
session_start();
include('db.php');
if (!isset($_SESSION['perfil'])) { header("Location: index.php"); }

// Sacamos los datos de la base de datos
$query = "SELECT z.nombre, f.temperatura, b.clorofila 
          FROM zonas z 
          LEFT JOIN datos_fisicos f ON z.id = f.id_zona 
          LEFT JOIN datos_bio b ON z.id = b.id_zona 
          ORDER BY f.fecha_medicion DESC LIMIT 15";
$result = pg_query($conn, $query);
?>
<!DOCTYPE html>
<html>
<head><title>Mapa GeoMonitor</title></head>
<body>
    <h1>Bienvenido, Perfil: <?php echo $_SESSION['perfil']; ?></h1>
    
    <?php if ($_SESSION['perfil'] == 'admin'): ?>
        <div style="background:#e3f2fd; padding:10px; border:1px solid blue;">
            <strong>Panel de Administrador:</strong> <button>Agregar Nueva Zona</button> | <button>Forzar Actualización Satelital</button>
        </div>
    <?php endif; ?>

    <h3>Datos Oceanográficos Actuales:</h3>
    <table border="1">
        <tr><th>Zona</th><th>Temp (°C)</th><th>Clorofila</th></tr>
        <?php while($row = pg_fetch_assoc($result)) {
            echo "<tr><td>{$row['nombre']}</td><td>{$row['temperatura']}</td><td>{$row['clorofila']}</td></tr>";
        } ?>
    </table>

    <br><a href="index.php">Cerrar Sesión</a>
</body>
</html>