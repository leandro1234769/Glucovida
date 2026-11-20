# CU09. Visualizar evolución

## 1. Información general

- **Código:** CU09
- **Nombre:** Visualizar evolución.
- **Actor principal:** Usuario autenticado.
- **Objetivo:** Permitir que el usuario explore una representación gráfica cronológica de sus mediciones de glucosa.
- **Prioridad:** Alta.
- **Relaciones:** CU04. Registrar medición de glucosa; CU05. Consultar mediciones; CU06. Editar medición; CU07. Eliminar medición.
- **Alcance:** Visualización temporal de las mediciones del usuario y exploración de períodos.
- **Exclusiones:** Predicciones, diagnósticos, interpretación clínica y asociación con alimentos consultados.

## 2. Descripción

El usuario accede a la sección de evolución y visualiza una gráfica de sus mediciones registradas. El eje horizontal representa el tiempo y el eje vertical representa el valor de glucosa en la unidad elegida.

El sistema ofrece períodos de 7, 30 y 90 días, además de un intervalo personalizado. El período predeterminado será de 30 días. El usuario puede seleccionar mg/dL o mmol/L para la presentación de los datos.

La representación incluirá los puntos de las mediciones existentes y una línea que los conecte en orden cronológico como guía visual. La línea no representa valores medidos entre puntos, no supone una progresión continua y no se utilizará para estimar mediciones futuras.

La gráfica muestra exclusivamente datos del historial de glucosa. No incorporará información nutricional ni asociará puntos con los alimentos consultados.

## 3. Precondiciones

1. El usuario tiene una sesión válida.
2. El usuario puede consultar sus propias mediciones.
3. Los registros incluyen valores y unidades identificables.
4. El sistema dispone de mediciones para el intervalo seleccionado o puede presentar un estado vacío.

## 4. Postcondiciones

### Visualización exitosa

- El usuario visualiza una gráfica construida con mediciones propias y no eliminadas.
- La gráfica identifica el período y la unidad de presentación.
- Los registros originales permanecen sin cambios.

### Sin mediciones disponibles

- El sistema informa que no hay datos para el período consultado.
- La gráfica no presenta puntos inventados ni líneas que sugieran mediciones inexistentes.

## 5. Datos de entrada

- Período: 7 días, 30 días, 90 días o intervalo personalizado.
- Unidad de presentación: mg/dL o mmol/L.
- Controles de navegación de la gráfica, como zoom o desplazamiento temporal.

El servidor identifica al usuario desde la sesión autenticada y no depende de un identificador de usuario proporcionado por el cliente.

## 6. Datos de salida

- Gráfica cronológica de mediciones.
- Eje de tiempo con fechas u horas según el intervalo y la densidad de los datos.
- Eje de valores de glucosa con la unidad seleccionada.
- Representación de cada medición recuperada.
- Indicadores de detalle para consultar fecha, hora, valor y contexto disponible.
- Mensaje informativo cuando no existen registros para el intervalo seleccionado.

## 7. Flujo principal

1. El usuario ingresa a la sección de evolución.
2. El sistema identifica al usuario autenticado.
3. El sistema selecciona por defecto los últimos 30 días.
4. El sistema recupera las mediciones del usuario que correspondan al período y que no estén eliminadas.
5. El sistema permite elegir la unidad de presentación.
6. Si existen valores almacenados en otra unidad, el sistema los convierte para su representación, sin modificar los valores originales.
7. El sistema ordena las mediciones cronológicamente.
8. El sistema construye la gráfica con los puntos de mediciones registradas y una línea visual que los conecta en orden temporal.
9. El sistema identifica los ejes, el período y la unidad.
10. Si el volumen de puntos dificulta la lectura, el sistema proporciona mecanismos de zoom o navegación temporal sin eliminar registros de la consulta.
11. El usuario puede modificar el período o la unidad y consultar nuevamente.
12. El sistema actualiza la visualización.
13. El caso de uso finaliza sin modificar los registros ni acceder a datos del catálogo.

## 8. Flujos alternativos

### FA01. Selección de período predefinido

1. El usuario selecciona 7, 30 o 90 días.
2. El sistema actualiza el intervalo temporal.
3. La gráfica se reconstruye con las mediciones coincidentes.

### FA02. Intervalo personalizado

1. El usuario selecciona una fecha de inicio y una fecha de fin.
2. El sistema valida el intervalo.
3. La gráfica presenta los registros correspondientes.

### FA03. Cambio de unidad

1. El usuario selecciona mg/dL o mmol/L.
2. El sistema convierte los valores para su representación cuando sea necesario.
3. La gráfica y sus etiquetas reflejan la unidad seleccionada.
4. Los valores almacenados permanecen intactos.

### FA04. Densidad elevada de mediciones

1. El sistema detecta que la cantidad de puntos dificulta la lectura.
2. La interfaz permite ampliar una región de la gráfica o navegar por el período.
3. El usuario puede explorar el intervalo con mayor detalle.
4. Los registros subyacentes continúan disponibles y no se eliminan del conjunto de datos consultado.

### FA05. No hay registros

1. El sistema no encuentra mediciones dentro del intervalo.
2. La interfaz informa que no hay datos disponibles.
3. El usuario puede cambiar el período.

## 9. Flujos de excepción

### FE01. Intervalo inválido

El sistema rechaza un rango de fechas incorrecto y solicita que se corrija.

### FE02. Error al recuperar las mediciones

El sistema informa que no pudo cargar la gráfica y evita presentar resultados incompletos como una visualización completa.

### FE03. Unidad no interpretable

El sistema no representa como válido un registro cuya unidad no pueda determinarse con seguridad.

### FE04. Sesión expirada

El sistema requiere una autenticación válida antes de recuperar las mediciones.

## 10. Reglas de negocio

- **RN-CU09-01.** La gráfica debe contener únicamente mediciones del usuario autenticado.
- **RN-CU09-02.** Las mediciones eliminadas se excluyen de la visualización ordinaria.
- **RN-CU09-03.** El período predeterminado será de 30 días.
- **RN-CU09-04.** El usuario podrá consultar períodos de 7, 30 y 90 días, además de un intervalo personalizado.
- **RN-CU09-05.** Las mediciones se representarán en orden cronológico.
- **RN-CU09-06.** La unidad de presentación podrá seleccionarse entre mg/dL y mmol/L.
- **RN-CU09-07.** Las conversiones para la gráfica no modificarán los valores originales.
- **RN-CU09-08.** Cada punto debe corresponder a una medición existente.
- **RN-CU09-09.** La línea que conecta puntos solo facilitará la visualización cronológica y no representará mediciones intermedias.
- **RN-CU09-10.** La gráfica no generará predicciones ni valores inferidos.
- **RN-CU09-11.** Cuando la densidad de puntos dificulte la lectura, podrá ofrecerse zoom o navegación temporal sin eliminar mediciones del conjunto consultado.
- **RN-CU09-12.** El sistema presentará un estado vacío cuando no existan registros coincidentes.
- **RN-CU09-13.** El sistema no incorporará nutrientes, categorías de impacto glucémico ni consultas del catálogo a la gráfica.
- **RN-CU09-14.** La aplicación no establecerá relaciones ni correlaciones entre alimentos y mediciones personales.

## 11. Requisitos funcionales asociados

- **RF-CU09-01.** El sistema debe mostrar la gráfica de evolución de las mediciones del usuario.
- **RF-CU09-02.** Debe utilizar los últimos 30 días como período predeterminado.
- **RF-CU09-03.** Debe permitir elegir 7, 30 o 90 días.
- **RF-CU09-04.** Debe permitir seleccionar un intervalo personalizado.
- **RF-CU09-05.** Debe ordenar cronológicamente las mediciones.
- **RF-CU09-06.** Debe permitir seleccionar mg/dL o mmol/L.
- **RF-CU09-07.** Debe convertir valores para su visualización cuando sea necesario, sin alterar los originales.
- **RF-CU09-08.** Debe mostrar el período y la unidad en los ejes o etiquetas correspondientes.
- **RF-CU09-09.** Debe permitir explorar gráficos densos mediante zoom o navegación temporal.
- **RF-CU09-10.** Debe excluir mediciones eliminadas de la consulta ordinaria.
- **RF-CU09-11.** Debe mostrar un estado vacío cuando no existan mediciones.
- **RF-CU09-12.** Debe impedir el acceso a las mediciones de otras cuentas.
- **RF-CU09-13.** No debe crear datos interpolados ni predicciones.
- **RF-CU09-14.** No debe vincular la gráfica con consultas de alimentos ni información nutricional.

## 12. Seguridad y privacidad

El backend debe comprobar la identidad y autorización del usuario antes de recuperar mediciones. Las consultas y los controles de acceso deben proteger los datos sensibles.

La gráfica no enviará mediciones a servicios de terceros sin autorización y no utilizará datos del catálogo para etiquetar o explicar puntos de la evolución.

## 13. Criterios de aceptación

- **CA-CU09-01.** Al abrir la sección, el sistema presenta por defecto los últimos 30 días.
- **CA-CU09-02.** El usuario puede alternar entre 7, 30 y 90 días.
- **CA-CU09-03.** El usuario puede seleccionar un intervalo personalizado.
- **CA-CU09-04.** Cada punto representa una medición almacenada.
- **CA-CU09-05.** Los puntos se presentan en orden cronológico.
- **CA-CU09-06.** El usuario puede elegir la unidad de presentación.
- **CA-CU09-07.** Las conversiones no alteran los valores originales.
- **CA-CU09-08.** El usuario puede explorar períodos densos mediante zoom o navegación temporal.
- **CA-CU09-09.** La línea entre puntos no se presenta como una medición ni como una predicción.
- **CA-CU09-10.** No se muestran mediciones eliminadas.
- **CA-CU09-11.** Si no hay datos, el sistema presenta un mensaje informativo.
- **CA-CU09-12.** La gráfica no contiene información ni correlaciones con alimentos consultados.

## 14. Fuera del alcance

- Pronosticar la glucosa futura.
- Diagnosticar condiciones médicas.
- Interpretar clínicamente la evolución.
- Correlacionar mediciones con alimentos.
- Registrar alimentos consumidos.
- Recomendar dietas o tratamientos.
- Presentar umbrales clínicos como alertas automáticas.