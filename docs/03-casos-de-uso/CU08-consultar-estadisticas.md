# CU08. Consultar estadísticas

## 1. Información general

- **Código:** CU08
- **Nombre:** Consultar estadísticas
- **Actor principal:** Usuario autenticado.
- **Objetivo:** Permitir que el usuario consulte estadísticas descriptivas calculadas a partir de sus propias mediciones de glucosa.
- **Prioridad:** Alta.
- **Relaciones:** CU04. Registrar medición de glucosa; CU05. Consultar mediciones; CU06. Editar medición; CU07. Eliminar medición.
- **Alcance:** Cálculo y presentación de cantidad de registros, promedio, valor mínimo y máximo en un período seleccionado.
- **Exclusiones:** Diagnósticos, predicciones, interpretación clínica y asociaciones entre mediciones y alimentos consultados.

## 2. Descripción

El usuario accede a la sección de estadísticas para revisar un resumen numérico de sus mediciones de glucosa. El sistema permite seleccionar un período y filtrar los datos por contexto de medición.

Por defecto, se presentan las estadísticas correspondientes a los últimos 30 días. El sistema calcula la cantidad de mediciones, el promedio, el valor mínimo y el máximo a partir de los registros válidos que correspondan a los filtros seleccionados.

Cuando el historial contiene valores en ambas unidades, el sistema permite seleccionar la unidad de presentación y realiza una conversión explícita para el cálculo y visualización de las estadísticas. La conversión no modifica los valores originales de las mediciones.

Las estadísticas son descriptivas. No identifican causas de una variación, no determinan un diagnóstico, no establecen tratamientos y no realizan asociaciones con alimentos. El catálogo nutricional no interviene en los cálculos de CU08.

## 3. Precondiciones

1. El usuario tiene una sesión válida.
2. El usuario dispone de permiso para consultar sus propias mediciones.
3. El sistema puede recuperar los registros que no estén eliminados.
4. La unidad de cada medición disponible está identificada de forma explícita.

## 4. Postcondiciones

### Consulta exitosa

- El usuario visualiza las estadísticas correspondientes a sus mediciones y filtros.
- Se muestra el período y la unidad utilizados.
- Los registros originales permanecen sin cambios.

### Sin datos suficientes

- El sistema informa que no hay mediciones que coincidan con el período y los filtros.
- No inventa ni completa valores faltantes.
- No presenta estadísticas de otro usuario.

## 5. Datos de entrada

- Fecha de inicio y fecha de fin, opcionales; el período predeterminado es de 30 días.
- Contexto de medición, opcional.
- Unidad de presentación: mg/dL o mmol/L.
- Parámetros de paginación solo si se necesitan para la consulta de registros asociados.

El sistema obtiene la identidad del usuario desde el contexto autenticado. No debe confiar en un identificador de usuario recibido del cliente para determinar de quién son las mediciones.

## 6. Datos de salida

- Cantidad de mediciones incluidas.
- Promedio de los valores.
- Valor mínimo.
- Valor máximo.
- Período consultado.
- Contexto seleccionado, si se aplicó un filtro.
- Unidad de presentación.
- Mensaje de estado cuando no existan registros adecuados.

Cada estadística debe derivarse de las mediciones que cumplan los filtros seleccionados. Los valores calculados no alteran los registros originales.

## 7. Flujo principal

1. El usuario ingresa a la sección de estadísticas.
2. El sistema identifica al usuario autenticado.
3. El sistema selecciona por defecto los últimos 30 días.
4. El sistema permite elegir un intervalo de fechas y, opcionalmente, un contexto de medición.
5. El usuario selecciona la unidad en la que desea visualizar las estadísticas.
6. El usuario ejecuta la consulta o modifica un filtro.
7. El sistema valida el intervalo de fechas y los filtros.
8. El backend recupera exclusivamente las mediciones del usuario que cumplen los criterios y que no estén eliminadas.
9. El sistema convierte los valores a la unidad elegida para fines de cálculo y presentación cuando sea necesario.
10. El sistema calcula la cantidad, el promedio, el mínimo y el máximo.
11. El sistema presenta los resultados junto con el período, la unidad y el contexto aplicado.
12. El usuario puede modificar los filtros y repetir la consulta.
13. El caso de uso termina sin modificar mediciones ni consultar datos del catálogo de alimentos.

## 8. Flujos alternativos

### FA01. Selección de un intervalo personalizado

1. El usuario selecciona las fechas de inicio y fin.
2. El sistema valida el intervalo.
3. El sistema calcula las estadísticas correspondientes al nuevo período.

### FA02. Filtrar por contexto

1. El usuario selecciona un contexto de medición.
2. El sistema incluye únicamente las mediciones que coincidan con ese contexto dentro del intervalo consultado.
3. El sistema vuelve a calcular las estadísticas.

### FA03. Cambio de unidad de presentación

1. El usuario selecciona mg/dL o mmol/L.
2. El sistema convierte los valores que estén almacenados en otra unidad.
3. El sistema calcula o presenta las estadísticas en la unidad seleccionada.
4. Los registros originales conservan sus valores y unidades.

### FA04. No hay mediciones en el período

1. El sistema no encuentra mediciones para los filtros seleccionados.
2. El sistema presenta un mensaje indicando que no hay datos disponibles.
3. El usuario puede cambiar el intervalo o los filtros.

## 9. Flujos de excepción

### FE01. Intervalo de fechas inválido

El sistema rechaza fechas incompletas o un intervalo cuya fecha inicial sea posterior a la fecha final y solicita su corrección.

### FE02. Error de recuperación de datos

El sistema informa que no pudo completar la consulta. No presenta resultados parciales como si fueran estadísticas completas.

### FE03. Error de unidad o valor inconsistente

El sistema excluye los datos que no puedan interpretarse correctamente y aplica un manejo controlado del error. No debe convertir unidades a partir de un dato ambiguo.

### FE04. Sesión expirada

El sistema solicita una nueva autenticación y no devuelve mediciones hasta validar la sesión.

## 10. Reglas de negocio

- **RN-CU08-01.** El usuario solo puede consultar estadísticas derivadas de sus propias mediciones.
- **RN-CU08-02.** Las mediciones eliminadas no se incluyen en las estadísticas ordinarias.
- **RN-CU08-03.** El período predeterminado corresponde a los últimos 30 días.
- **RN-CU08-04.** El sistema permite definir un intervalo personalizado de fechas.
- **RN-CU08-05.** El sistema permite filtrar por contexto de medición.
- **RN-CU08-06.** Las estadísticas disponibles serán cantidad, promedio, mínimo y máximo.
- **RN-CU08-07.** Los cálculos deberán utilizar únicamente los registros que cumplan los filtros seleccionados.
- **RN-CU08-08.** La unidad de presentación podrá seleccionarse entre mg/dL y mmol/L.
- **RN-CU08-09.** La conversión de unidades no modificará el valor ni la unidad originales almacenados.
- **RN-CU08-10.** Los resultados deberán indicar el período y la unidad utilizados.
- **RN-CU08-11.** Si no existen registros coincidentes, el sistema mostrará un estado vacío en lugar de valores inventados.
- **RN-CU08-12.** El sistema no incorporará información del catálogo nutricional a los cálculos.
- **RN-CU08-13.** El sistema no vinculará una estadística con alimentos consultados ni inferirá motivos de los cambios observados.
- **RN-CU08-14.** Los resultados tendrán carácter descriptivo y no constituirán diagnóstico ni recomendación clínica.

## 11. Requisitos funcionales asociados

- **RF-CU08-01.** El sistema debe permitir acceder a la sección de estadísticas.
- **RF-CU08-02.** Debe utilizar los últimos 30 días como período predeterminado.
- **RF-CU08-03.** Debe permitir seleccionar un intervalo de fechas personalizado.
- **RF-CU08-04.** Debe permitir filtrar por contexto de medición.
- **RF-CU08-05.** Debe permitir seleccionar mg/dL o mmol/L para la presentación.
- **RF-CU08-06.** Debe calcular la cantidad de mediciones incluidas.
- **RF-CU08-07.** Debe calcular el promedio, el mínimo y el máximo.
- **RF-CU08-08.** Debe excluir las mediciones eliminadas.
- **RF-CU08-09.** Debe convertir valores para presentar estadísticas en la unidad seleccionada, sin alterar los registros originales.
- **RF-CU08-10.** Debe indicar el período y la unidad usados en el cálculo.
- **RF-CU08-11.** Debe informar cuando no existan datos coincidentes.
- **RF-CU08-12.** Debe impedir el acceso a las mediciones de otros usuarios.
- **RF-CU08-13.** No debe utilizar datos del catálogo para producir estadísticas o explicaciones sobre la glucosa.
- **RF-CU08-14.** Debe gestionar errores de consulta sin exponer información técnica sensible.

## 12. Seguridad y privacidad

El backend debe obtener la identidad del usuario a partir de la sesión autenticada y verificar la autorización para consultar cada registro. No debe confiar únicamente en un identificador enviado desde la interfaz.

Las consultas deberán ejecutarse de forma segura. La aplicación debe proteger los datos de salud y evitar que las estadísticas se envíen a servicios de terceros no autorizados.

El sistema no debe construir perfiles de alimentación a partir de las consultas al catálogo ni relacionar esas consultas con estadísticas de glucosa.

## 13. Criterios de aceptación

- **CA-CU08-01.** Al ingresar a estadísticas, el sistema selecciona por defecto los últimos 30 días.
- **CA-CU08-02.** El usuario puede seleccionar un intervalo personalizado.
- **CA-CU08-03.** El usuario puede filtrar por contexto.
- **CA-CU08-04.** El sistema presenta cantidad, promedio, mínimo y máximo de las mediciones coincidentes.
- **CA-CU08-05.** El usuario puede seleccionar la unidad de presentación.
- **CA-CU08-06.** Las conversiones necesarias no alteran los registros originales.
- **CA-CU08-07.** Las mediciones eliminadas no intervienen en el cálculo ordinario.
- **CA-CU08-08.** El período y la unidad aparecen identificados junto a los resultados.
- **CA-CU08-09.** Sin datos coincidentes, el sistema presenta un mensaje informativo.
- **CA-CU08-10.** Un usuario no puede obtener estadísticas derivadas de mediciones de otra cuenta.
- **CA-CU08-11.** El sistema no incorpora el catálogo a los cálculos.
- **CA-CU08-12.** El sistema no produce diagnóstico, predicción ni correlación con alimentos.

## 14. Fuera del alcance

- Interpretación clínica de los resultados.
- Predicción de mediciones futuras.
- Identificación de causas de cambios en la glucosa.
- Correlación de mediciones con alimentos consultados.
- Registro de consumo de alimentos.
- Recomendaciones nutricionales, dietas o tratamientos.
- Indicadores adicionales que no hayan sido incluidos en el alcance vigente.