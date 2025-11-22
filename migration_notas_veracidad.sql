-- Migración para agregar el campo es_veraz a la tabla Notas_Comunidad
-- Este campo permite que las notas indiquen si el usuario considera el reporte veraz o falso
-- Valores: TRUE = veraz, FALSE = falso, NULL = neutral/sin opinión

-- Agregar la columna es_veraz a la tabla Notas_Comunidad
ALTER TABLE public."Notas_Comunidad" 
ADD COLUMN IF NOT EXISTS es_veraz BOOLEAN DEFAULT NULL;

-- Agregar comentario a la columna para documentación
COMMENT ON COLUMN public."Notas_Comunidad".es_veraz IS 
'Indica si el usuario considera el reporte veraz (TRUE), falso (FALSE) o neutral (NULL)';

-- Esta migración permite que las notas de comunidad afecten el porcentaje de veracidad del reporte
-- La fórmula de cálculo es:
-- - 60% basado en upvotes/downvotes
-- - 40% basado en notas de comunidad con es_veraz definido
