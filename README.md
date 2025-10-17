## BACKEND SW 2

Reglas de negocio recientes:

- Cuando `veracidad_porcentaje` es menor a 33%, el `estado` del reporte se fuerza automáticamente a "Falso".
	- Aplica en la creación y actualización de reportes (`ReportesService`).
	- También se aplica cuando la veracidad se recalcula por reacciones (`ReaccionesService`).

