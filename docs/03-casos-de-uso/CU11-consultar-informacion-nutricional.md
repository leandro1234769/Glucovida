# CU11. Consultar información nutricional e impacto glucémico general

## 1. Información general

- **Código:** CU11
- **Nombre:** Consultar información nutricional e impacto glucémico general.
- **Estado:** Cerrado funcionalmente.
- **Actor principal:** Usuario autenticado.
- **Objetivo:** Permitir que el usuario consulte información nutricional general de un alimento y, cuando exista una clasificación validada, su categoría informativa de posible impacto glucémico.
- **Prioridad:** Alta.
- **Caso de uso relacionado:** CU10. Consultar alimentos.
- **Alcance:** Consulta de datos nutricionales, cantidades de referencia, fuente y clasificación general cuando proceda.
- **Fuera del alcance:** Dietas, planes de alimentación, prescripciones, recomendaciones clínicas individualizadas y asociaciones entre alimentos y mediciones personales.

## 2. Descripción

El usuario selecciona un alimento desde CU10 y consulta los datos nutricionales disponibles en el catálogo de GlucoVida. La información se presenta por cada 100 gramos y por porción cuando existan datos suficientes y referencias válidas.

Los datos podrán incluir energía, carbohidratos totales, azúcares, proteínas, grasas y otros nutrientes documentados. Cada valor debe indicar su unidad y su cantidad de referencia.

Cuando exista una clasificación general de impacto glucémico respaldada por una metodología documentada y validada profesionalmente, el sistema podrá mostrar una categoría informativa de impacto bajo, moderado o alto. La categoría describirá el alimento bajo los criterios de esa metodología y no se utilizará para predecir la respuesta de glucosa de un usuario.

El sistema también podrá calcular valores nutricionales aproximados para una cantidad introducida por el usuario, siempre que los datos de referencia y el método de cálculo lo permitan. Este cálculo será exclusivamente informativo: introducir una cantidad no significa que el usuario la haya consumido.

CU11 no consulta el historial de glucosa, no registra hábitos alimenticios ni asocia alimentos con mediciones personales.

## 3. Precondiciones

1. El usuario dispone de una sesión válida.
2. El alimento existe y está habilitado en el catálogo.
3. Los datos nutricionales disponibles tienen unidades y referencias de cantidad que permitan interpretarlos correctamente.
4. Si se muestra una categoría de impacto glucémico, esta cuenta con una metodología documentada y validada.
5. Si se solicita calcular una cantidad personalizada, debe existir una referencia nutricional válida para realizar el cálculo.

## 4. Postcondiciones

### 4.1. Consulta exitosa

1. El usuario visualiza la información nutricional disponible.
2. Cada valor se presenta con su unidad y referencia de cantidad.
3. La fuente y la fecha de actualización se muestran cuando estén registradas.
4. La categoría de impacto glucémico se muestra únicamente cuando existe una clasificación validada.
5. La consulta no modifica el catálogo ni las mediciones personales.

### 4.2. Información incompleta o no disponible

1. El sistema identifica los datos faltantes.
2. No sustituye valores faltantes por datos inventados.
3. No presenta datos inconsistentes como si fueran valores verificados.
4. Si no existe clasificación de impacto validada, los valores nutricionales disponibles pueden consultarse sin mostrar una categoría de impacto.

## 5. Datos de entrada

- Identificador del alimento seleccionado.
- Cantidad personalizada, opcional, si el usuario solicita calcular los valores nutricionales para otra cantidad.

El identificador debe corresponder a un registro existente y habilitado. La cantidad personalizada deberá ser numérica, positiva y estar dentro de los límites definidos por la aplicación.

La cantidad introducida se utilizará exclusivamente para el cálculo solicitado. No se almacenará como consumo ni se asociará a las mediciones del usuario.

## 6. Datos de salida

Según la disponibilidad y calidad de los datos, el sistema podrá mostrar:

- Nombre del alimento.
- Categoría.
- Valor energético o calorías.
- Carbohidratos totales.
- Azúcares.
- Proteínas.
- Grasas totales.
- Otros nutrientes registrados.
- Cantidad de referencia de 100 gramos.
- Porción de referencia y medida casera correspondiente, cuando esté documentada.
- Fuente nutricional.
- Fecha de actualización, cuando esté registrada.
- Valores calculados para la cantidad solicitada, identificados como tales.
- Categoría general de impacto glucémico y explicación de sus límites, cuando exista una clasificación validada.

Los valores deben distinguir con claridad entre datos por 100 gramos, datos por porción y resultados derivados mediante cálculo. No se deben comparar cantidades diferentes como si fueran equivalentes.

## 7. Flujo principal

1. El usuario consulta el catálogo mediante CU10.
2. El usuario selecciona un alimento.
3. El sistema recibe el identificador y verifica que el alimento exista y esté habilitado.
4. El sistema recupera los datos nutricionales asociados.
5. El sistema verifica la disponibilidad, la unidad y la cantidad de referencia de cada dato.
6. El sistema presenta los datos por 100 gramos y por porción cuando existan datos suficientes.
7. El sistema muestra la fuente y la fecha de actualización si están registradas.
8. Si existe una categoría general de impacto glucémico validada, el sistema presenta la categoría y una explicación breve de su alcance.
9. El sistema aclara que la categoría general no predice la respuesta individual de glucosa y no constituye una recomendación clínica.
10. El usuario puede introducir una cantidad personalizada para obtener valores calculados, si la funcionalidad está habilitada.
11. El sistema valida la cantidad y comprueba que los datos disponibles permiten realizar el cálculo.
12. El sistema presenta los valores derivados, identificándolos como cálculos informativos.
13. El usuario puede regresar al catálogo.
14. El caso de uso finaliza sin modificar los datos originales, registrar consumo ni consultar las mediciones personales de glucosa.

## 8. Flujos alternativos

### FA01. Información nutricional parcialmente disponible

1. El usuario consulta un alimento cuyo registro contiene algunos nutrientes, pero no todos.
2. El sistema identifica los valores disponibles.
3. El sistema presenta los valores válidos y señala los campos sin información.
4. El sistema no inventa ni estima valores faltantes sin identificarlos como estimaciones y sin respaldo metodológico.

### FA02. Información nutricional no disponible

1. El usuario selecciona un alimento sin datos nutricionales suficientes.
2. El sistema informa que no dispone de información nutricional verificable para ese alimento.
3. El usuario puede regresar al catálogo.

### FA03. Clasificación de impacto glucémico no disponible

1. El usuario consulta un alimento que no dispone de clasificación validada.
2. El sistema presenta la información nutricional disponible.
3. El sistema no muestra una categoría de impacto glucémico ni la deduce automáticamente a partir de un solo nutriente.

### FA04. Consulta de cantidad personalizada

1. El usuario introduce una cantidad positiva y válida.
2. El sistema verifica que los datos nutricionales permitan calcular los valores para esa cantidad.
3. El sistema realiza el cálculo con la referencia correspondiente.
4. El sistema presenta los resultados como valores calculados.
5. El sistema no registra la cantidad como alimento consumido.

### FA05. Regreso al catálogo

1. El usuario termina de consultar los datos nutricionales.
2. El usuario selecciona la opción para regresar.
3. El sistema vuelve a CU10 y conserva los criterios de búsqueda anteriores cuando sea técnicamente posible.

## 9. Flujos de excepción

### FE01. Identificador inválido

El sistema no encuentra un alimento válido, informa que el registro no está disponible y ofrece regresar al catálogo.

### FE02. Alimento deshabilitado

El sistema impide la consulta ordinaria y muestra un mensaje de indisponibilidad.

### FE03. Error de recuperación

El sistema informa que no pudo completar la consulta. No presenta información antigua o no verificada como si acabara de comprobarla.

### FE04. Datos inconsistentes

Si un valor carece de unidad, referencia de cantidad o información necesaria para interpretarlo, el sistema evita presentarlo como un dato confiable. El registro queda sujeto al proceso interno de revisión.

### FE05. Cantidad personalizada inválida

El sistema rechaza cantidades no numéricas, negativas, iguales a cero o superiores a los límites permitidos. Solicita un valor válido sin guardar un registro de consumo.

### FE06. Datos insuficientes para calcular una cantidad

El sistema informa que no es posible calcular el valor solicitado con los datos disponibles y presenta la información de referencia que sí puede validarse.

## 10. Reglas de negocio

- **RN-CU11-01.** Los valores nutricionales deben corresponder al alimento seleccionado.
- **RN-CU11-02.** Cada valor debe mostrar su unidad y referencia de cantidad.
- **RN-CU11-03.** La información se presentará por 100 gramos y por porción cuando existan datos suficientes y comparables.
- **RN-CU11-04.** Los valores faltantes deben identificarse como no disponibles.
- **RN-CU11-05.** La información nutricional se obtendrá de fuentes oficiales o institucionales confiables, de acuerdo con el criterio definido para la primera versión.
- **RN-CU11-06.** La fuente y la fecha de actualización se mostrarán cuando estén registradas.
- **RN-CU11-07.** Los datos nutricionales deben ser revisados antes de incorporarse al catálogo maestro.
- **RN-CU11-08.** La clasificación general de impacto glucémico solo se mostrará si cuenta con una metodología documentada y validada.
- **RN-CU11-09.** No se asignará una categoría de impacto a partir de una regla improvisada ni de un único nutriente, salvo que la metodología validada lo establezca expresamente.
- **RN-CU11-10.** La categoría general no se interpretará como predicción de la respuesta individual de glucosa.
- **RN-CU11-11.** La categoría no afirmará que un alimento es universalmente seguro o peligroso.
- **RN-CU11-12.** Los cálculos para cantidades personalizadas se permitirán solo cuando existan datos de referencia válidos y un procedimiento de cálculo aplicable.
- **RN-CU11-13.** Los valores calculados se identificarán como derivados y no modificarán los datos originales.
- **RN-CU11-14.** Introducir una cantidad para consultar sus valores nutricionales no se interpretará como un registro de consumo.
- **RN-CU11-15.** El sistema no consultará ni relacionará las mediciones personales de glucosa con los alimentos mostrados.
- **RN-CU11-16.** El sistema no generará dietas, menús, recomendaciones clínicas ni prescripciones personalizadas.
- **RN-CU11-17.** Las correcciones de los datos nutricionales generarán una auditoría con responsable, fecha y justificación.
- **RN-CU11-18.** El contenido educativo y la metodología de clasificación deberán respetar los límites de la evidencia disponible.

## 11. Requisitos funcionales asociados

- **RF-CU11-01.** El sistema debe mostrar la información nutricional de un alimento seleccionado desde CU10.
- **RF-CU11-02.** Debe validar que el alimento exista y esté habilitado.
- **RF-CU11-03.** Debe presentar los nutrientes disponibles con sus unidades y cantidades de referencia.
- **RF-CU11-04.** Debe presentar valores por 100 gramos y por porción cuando existan datos suficientes.
- **RF-CU11-05.** Debe mostrar la fuente y la fecha de actualización cuando estén registradas.
- **RF-CU11-06.** Debe identificar los datos que no estén disponibles.
- **RF-CU11-07.** Debe mostrar una categoría general de impacto glucémico únicamente si está validada.
- **RF-CU11-08.** Debe explicar que la categoría general no predice la respuesta individual de glucosa.
- **RF-CU11-09.** Debe permitir calcular valores para una cantidad personalizada cuando existan datos suficientes.
- **RF-CU11-10.** Debe validar la cantidad introducida.
- **RF-CU11-11.** Debe distinguir los valores originales de los valores derivados.
- **RF-CU11-12.** Debe impedir que una cantidad consultada se registre como consumo.
- **RF-CU11-13.** Debe evitar modificar los datos originales durante la consulta o el cálculo.
- **RF-CU11-14.** Debe permitir regresar a CU10.
- **RF-CU11-15.** Debe manejar errores sin exponer información técnica interna.
- **RF-CU11-16.** No debe cruzar los datos nutricionales con las mediciones personales de glucosa.
- **RF-CU11-17.** No debe generar dietas ni recomendaciones clínicas individualizadas.

## 12. Seguridad, privacidad y calidad

1. El servidor validará el identificador y las cantidades recibidas.
2. Las consultas utilizarán mecanismos seguros para recuperar los registros.
3. Los permisos se comprobarán en el backend cuando la funcionalidad requiera autenticación.
4. Los valores nutricionales se presentarán únicamente cuando las unidades y las cantidades de referencia permitan interpretarlos de forma fiable.
5. Los resultados calculados se distinguirán visualmente de los datos originales.
6. Las consultas y los cálculos nutricionales no accederán a las mediciones personales de glucosa.
7. Los errores de consulta no expondrán información interna.
8. Las correcciones de datos del catálogo deberán quedar trazadas mediante el procedimiento de auditoría.

## 13. Criterios de aceptación

- **CA-CU11-01.** Un alimento habilitado permite consultar su información nutricional.
- **CA-CU11-02.** Los valores disponibles se presentan con unidad y cantidad de referencia.
- **CA-CU11-03.** Se muestran datos por 100 gramos y por porción cuando existan datos suficientes.
- **CA-CU11-04.** Los valores faltantes se identifican como no disponibles.
- **CA-CU11-05.** La fuente y fecha se muestran cuando están registradas.
- **CA-CU11-06.** La categoría general de impacto solo se presenta si cuenta con validación documentada.
- **CA-CU11-07.** La categoría no se muestra como una predicción individual.
- **CA-CU11-08.** El sistema permite calcular valores para cantidades personalizadas si los datos lo permiten.
- **CA-CU11-09.** Los valores calculados se identifican como derivados.
- **CA-CU11-10.** Un cálculo no modifica los datos nutricionales originales.
- **CA-CU11-11.** La cantidad personalizada no se guarda como consumo.
- **CA-CU11-12.** El sistema no consulta ni cruza mediciones personales durante el flujo.
- **CA-CU11-13.** El usuario puede regresar al catálogo.
- **CA-CU11-14.** Los errores no exponen información técnica interna.
- **CA-CU11-15.** El sistema no genera dietas, menús, tratamientos ni recomendaciones clínicas personalizadas.

## 14. Fuera del alcance

- Registro de alimentos consumidos.
- Correlación entre alimentos consultados y mediciones individuales.
- Predicción del efecto de un alimento en la glucosa del usuario.
- Elaboración de dietas o planes alimenticios.
- Recomendaciones de menús o porciones con fines terapéuticos.
- Diagnósticos o tratamientos.
- Modificación del catálogo desde la interfaz de consulta.