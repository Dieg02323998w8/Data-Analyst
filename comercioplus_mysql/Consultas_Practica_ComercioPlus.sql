-- Banco adicional de consultas para ComercioPlus (MySQL 8.0+)
USE ComercioPlus;

-- 1. Top 10 productos mas vendidos por unidades
SELECT pr.id_producto, pr.nombre, SUM(dp.cantidad) unidades
FROM detalle_pedido dp JOIN productos pr USING(id_producto)
GROUP BY pr.id_producto, pr.nombre ORDER BY unidades DESC LIMIT 10;

-- 2. Total facturado por vendedor
SELECT e.id_empleado, u.nombre, u.apellido, COUNT(p.id_pedido) pedidos,
       SUM(p.total) facturado
FROM empleados e JOIN usuarios u USING(id_usuario)
LEFT JOIN pedidos p ON p.id_empleado=e.id_empleado AND p.estado<>'Cancelado'
GROUP BY e.id_empleado,u.nombre,u.apellido ORDER BY facturado DESC;

-- 3. Clientes frecuentes con mas de cinco pedidos
SELECT c.id_cliente,u.nombre,u.apellido,COUNT(p.id_pedido) pedidos
FROM clientes c JOIN usuarios u USING(id_usuario)
JOIN pedidos p USING(id_cliente)
GROUP BY c.id_cliente,u.nombre,u.apellido
HAVING COUNT(p.id_pedido)>5 ORDER BY pedidos DESC;

-- 4. Ventas por categoria
SELECT ca.nombre categoria,SUM(dp.subtotal) ventas
FROM detalle_pedido dp JOIN productos pr USING(id_producto)
JOIN categorias ca USING(id_categoria)
GROUP BY ca.id_categoria,ca.nombre ORDER BY ventas DESC;

-- 5. Valor promedio de los pedidos por estado
SELECT estado,COUNT(*) cantidad,ROUND(AVG(total),2) promedio
FROM pedidos GROUP BY estado;

-- 6. Pedidos superiores al promedio general
SELECT id_pedido,id_cliente,total
FROM pedidos WHERE total>(SELECT AVG(total) FROM pedidos)
ORDER BY total DESC;

-- 7. Productos con inventario total consolidado
SELECT p.id_producto,p.nombre,SUM(i.existencia) stock_total
FROM productos p JOIN inventario i USING(id_producto)
GROUP BY p.id_producto,p.nombre ORDER BY stock_total;

-- 8. Devoluciones por motivo
SELECT motivo,COUNT(*) cantidad,SUM(valor_reembolso) reembolsado
FROM devoluciones GROUP BY motivo ORDER BY cantidad DESC;

-- 9. Clientes que han comprado tecnologia
SELECT DISTINCT c.id_cliente,u.nombre,u.apellido
FROM clientes c JOIN usuarios u USING(id_usuario)
JOIN pedidos pe USING(id_cliente)
JOIN detalle_pedido dp USING(id_pedido)
JOIN productos pr USING(id_producto)
JOIN categorias ca USING(id_categoria)
WHERE ca.nombre='Tecnologia';

-- 10. Ranking de productos por ventas (funcion de ventana)
SELECT id_producto,nombre,ventas,
       DENSE_RANK() OVER(ORDER BY ventas DESC) ranking
FROM (
  SELECT pr.id_producto,pr.nombre,SUM(dp.subtotal) ventas
  FROM productos pr JOIN detalle_pedido dp USING(id_producto)
  GROUP BY pr.id_producto,pr.nombre
) x;

-- 11. Compras acumuladas por cliente
SELECT id_cliente,fecha_pedido,total,
       SUM(total) OVER(PARTITION BY id_cliente ORDER BY fecha_pedido) acumulado
FROM pedidos WHERE estado<>'Cancelado';

-- 12. Transportadoras y cantidad de envios
SELECT t.nombre,COUNT(e.id_envio) envios,
       SUM(e.costo_envio) costo_total
FROM transportadoras t LEFT JOIN envios e USING(id_transportadora)
GROUP BY t.id_transportadora,t.nombre ORDER BY envios DESC;

-- 13. Productos sin resenas
SELECT p.id_producto,p.nombre
FROM productos p LEFT JOIN resenas r USING(id_producto)
WHERE r.id_resena IS NULL;

-- 14. Cupones mas utilizados
SELECT cu.codigo,cu.porcentaje_descuento,COUNT(pc.id_pedido) usos
FROM cupones cu LEFT JOIN pedido_cupon pc USING(id_cupon)
GROUP BY cu.id_cupon,cu.codigo,cu.porcentaje_descuento ORDER BY usos DESC;

-- 15. Comparacion mensual de ventas (incluye año)
SELECT YEAR(fecha_pedido) anio,MONTH(fecha_pedido) mes,
       COUNT(*) pedidos,SUM(total) ventas
FROM pedidos WHERE estado<>'Cancelado'
GROUP BY YEAR(fecha_pedido),MONTH(fecha_pedido)
ORDER BY anio,mes;

-- 16. Proveedores con cantidad de productos
SELECT pr.id_proveedor,pr.razon_social,COUNT(p.id_producto) productos
FROM proveedores pr LEFT JOIN productos p USING(id_proveedor)
GROUP BY pr.id_proveedor,pr.razon_social ORDER BY productos DESC;

-- 17. Pedidos sin envio registrado
SELECT p.id_pedido,p.fecha_pedido,p.estado
FROM pedidos p LEFT JOIN envios e USING(id_pedido)
WHERE p.estado IN ('Enviado','Entregado') AND e.id_envio IS NULL;

-- 18. Resumen general de indicadores
SELECT
 (SELECT COUNT(*) FROM clientes) total_clientes,
 (SELECT COUNT(*) FROM productos) total_productos,
 (SELECT COUNT(*) FROM pedidos) total_pedidos,
 (SELECT ROUND(SUM(total),2) FROM pedidos WHERE estado<>'Cancelado') ventas_no_canceladas,
 (SELECT COUNT(*) FROM devoluciones) total_devoluciones;
