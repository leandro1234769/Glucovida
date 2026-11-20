# CU13. Reportar discrepancia en la información nutricional

## 1. Información general

- **Código:** CU13
- **Nombre:** Reportar discrepancia en la información nutricional.
- **Versión:** 1.0
- **Actor principal:** Usuario autenticado.
- **Actores secundarios:** Administrador técnico de contenidos; profesional competente en nutrición o salud encargado de revisar la discrepancia, cuando corresponda.
- **Objetivo:** Permitir que el usuario reporte posibles errores, inconsistencias o información desactualizada en el catálogo nutricional para que sean revisados por los responsables.
- **Prioridad:** Media-alta.
- **Tipo:** Caso de uso funcional.
- **Relaciones:** CU10. Consultar alimentos; CU11. Consultar información nutricional e impacto glucémico general.
- **Alcance:** Registrar el reporte, asignarle un identificador y permitir su gestión de revisión y estado.
- **Fuera del alcance:** Modificación directa del catálogo por el usuario, registro de consumos, correlación con mediciones personales y recomendaciones clínicas.

## 2. Descripción

El usuario que detecta una posible discrepancia en la información nutricional puede enviar un reporte relacionado con un alimento del catálogo. El reporte debe identificar el alimento y el tipo de inconsistencia observada, junto con una descripción suficiente para facilitar su revisión.

Los reportes podrán referirse a errores tipográficos, unidades inconsistentes, cantidades o porciones dudosas, valores nutricionales presuntamente incorrectos, fuentes incompletas o desactualizadas, o una posible inconsistencia en la clasificación general de impacto glucémico.

El sistema registra el reporte sin modificar automáticamente el alimento ni sustituir sus valores. El administrador técnico de contenidos podrá revisar la solicitud, asignar su estado y derivarla al profesional competente cuando la validación nutricional sea necesaria.

Si la revisión concluye que debe cambiarse un dato, la modificación deberá realizarse mediante el procedimiento de administración del catálogo y generar la auditoría correspondiente. La recepción de un reporte no equivale a la confirmación de que el dato reportado sea incorrecto.

El reporte no debe requerir ni incorporar mediciones de glucosa, diagnósticos, tratamientos, cantidades consumidas por el usuario ni datos sobre una supuesta reacción individual a un alimento.

## 3. Precondiciones

1. La aplicación está disponible.
2. El usuario dispone de una sesión válida.
3. El alimento al que se refiere el reporte existe o puede identificarse en el catálogo.
4. El formulario de reporte está habilitado.
5. El catálogo cuenta con un mecanismo interno para recibir y gestionar los reportes.

## 4. Postcondiciones

### 4.1. Reporte registrado

1. El sistema crea un reporte con identificador único.
2. El reporte queda asociado al alimento seleccionado.
3. El sistema registra la fecha de creación y el estado inicial del reporte.
4. El sistema informa al usuario que el reporte fue recibido.
5. Los valores nutricionales y la clasificación del alimento permanecen sin cambios.

### 4.2. Reporte rechazado por datos insuficientes

1. El sistema informa cuáles datos obligatorios faltan.
2. El reporte no se registra hasta que la información mínima sea válida.
3. No se modifica el catálogo.

### 4.3. Reporte atendido

1. El reporte puede avanzar por los estados del flujo de revisión.
2. La decisión y la justificación de cierre quedan registradas.
3. Si se necesita cambiar un dato, la actualización se realiza por el procedimiento autorizado de mantenimiento del catálogo.
4. Toda corrección confirmada genera el registro de auditoría correspondiente.

## 5. Datos de entrada

- Identificador del alimento, seleccionado desde el catálogo.
- Tipo de discrepancia.
- Descripción del problema observado.
- Valor o dato cuestionado, opcional cuando corresponda.
- Fuente o referencia que apoye el reporte, opcional.
- Información complementaria estrictamente necesaria para entender la discrepancia.

Los tipos de discrepancia podrán incluir:

- Valor nutricional posiblemente incorrecto.
- Unidad de medida inconsistente.
- Cantidad o porción de referencia dudosa.
- Fuente ausente, incompleta o desactualizada.
- Error en el nombre o la categoría del alimento.
- Posible inconsistencia en la clasificación general de impacto glucémico.
- Error de presentación o tipográfico.
- Otro problema relacionado con la exactitud o interpretación del registro.

La interfaz no debe solicitar información sobre glucosa personal, diagnóstico, medicamentos, alimentos consumidos o respuestas fisiológicas individuales.

## 6. Datos de salida

- Identificador del reporte.
- Alimento reportado.
- Tipo de discrepancia.
- Fecha y hora de creación.
- Estado actual del reporte.
- Confirmación de recepción.
- Mensaje de validación o error, cuando corresponda.

Los reportes no deben exponer los datos de otros usuarios ni permitir modificar directamente la información nutricional desde el formulario de reporte.

## 7. Flujo principal

1. El usuario accede al catálogo mediante CU10 o consulta un alimento mediante CU11.
2. El usuario selecciona la opción para reportar una discrepancia.
3. El sistema abre el formulario y asocia el reporte con el alimento seleccionado.
4. El usuario selecciona el tipo de discrepancia.
5. El usuario describe el problema observado.
6. Si cuenta con ella, el usuario añade una referencia que pueda ayudar a revisar el dato.
7. El usuario envía el reporte.
8. El sistema valida que el alimento exista y esté habilitado para el proceso de reporte.
9. El sistema valida los campos obligatorios, el tamaño de la descripción y el formato de los datos recibidos.
10. El sistema comprueba los controles de abuso y duplicación aplicables.
11. El sistema crea el reporte con un identificador único, fecha, autor y estado inicial “Recibido”.
12. El sistema conserva la descripción y los metadatos necesarios para la revisión.
13. El sistema confirma al usuario la recepción del reporte.
14. El administrador técnico de contenidos recibe el reporte en la bandeja de gestión.
15. El administrador revisa la clasificación inicial y determina si necesita información adicional o revisión profesional.
16. Si corresponde, el reporte pasa al estado “En revisión profesional”.
17. La discrepancia se revisa contra las fuentes documentadas del catálogo.
18. El responsable registra la decisión y su justificación.
19. Si se confirma que el dato debe cambiarse, se inicia el procedimiento autorizado de actualización del catálogo y se genera la auditoría exigida.
20. El reporte se marca como resuelto o descartado, según el resultado de la revisión.
21. Si existe un canal de notificación habilitado, el usuario recibe el estado final del reporte.
22. El caso de uso termina sin relacionar el reporte con mediciones personales de glucosa.

## 8. Flujos alternativos

### FA01. Reporte con fuente de referencia

1. El usuario incluye una fuente o referencia que apoya su observación.
2. El sistema valida el formato y conserva esa referencia como parte del reporte.
3. El administrador o profesional utiliza la fuente como material de revisión, sin considerarla automáticamente válida.

### FA02. Reporte sobre una clasificación de impacto glucémico

1. El usuario selecciona que la discrepancia se refiere a la categoría general de impacto glucémico.
2. El sistema registra el reporte asociado al alimento y al campo cuestionado.
3. El administrador deriva el caso al profesional competente para revisar la metodología y su aplicación.
4. La clasificación vigente no cambia hasta que se complete la revisión y se apruebe una modificación.

### FA03. Reporte duplicado

1. El sistema detecta un reporte reciente que parece referirse al mismo alimento, campo y problema.
2. El sistema informa que puede existir un reporte similar.
3. Cuando corresponda, permite al usuario continuar o vincular su observación al reporte existente.
4. Si se crea un nuevo reporte, se conserva su identificador y la trazabilidad respectiva.

### FA04. Se requiere información adicional

1. El administrador determina que los datos suministrados no son suficientes para revisar la discrepancia.
2. El reporte cambia al estado “Requiere información”.
3. Si existe un mecanismo de comunicación habilitado, el usuario recibe la solicitud de información adicional.
4. La gestión continúa una vez que se suministre la información requerida, de acuerdo con la política de atención definida.

### FA05. La discrepancia no se confirma

1. El responsable revisa el dato contra las fuentes disponibles.
2. No encuentra evidencia suficiente para justificar el cambio.
3. El reporte se marca como “Descartado” con una justificación.
4. El catálogo permanece sin modificaciones.

## 9. Flujos de excepción

### FE01. Datos obligatorios incompletos

1. El usuario intenta enviar un reporte sin alimento identificado, tipo de discrepancia o descripción.
2. El sistema rechaza el envío.
3. El sistema señala los campos requeridos.

### FE02. Alimento no disponible

1. El sistema no encuentra el alimento o determina que no puede ser reportado mediante el flujo ordinario.
2. El sistema informa que el registro no está disponible.
3. El sistema no crea un reporte asociado a un identificador inválido.

### FE03. Error al guardar el reporte

1. El sistema no puede guardar el reporte.
2. El sistema informa que el envío no pudo completarse.
3. No se muestra una confirmación de recepción hasta que el registro se haya guardado correctamente.

### FE04. Error al notificar

1. El reporte se guarda correctamente.
2. El envío de una notificación falla.
3. El sistema conserva el reporte y el estado inicial.
4. La falla de notificación no debe borrar ni duplicar el reporte.

### FE05. Reporte abusivo o contenido no permitido

1. El sistema detecta un envío que supera los límites de frecuencia, tamaño o formato establecidos.
2. El sistema aplica las medidas de protección previstas.
3. El reporte solo se registra si supera las validaciones y controles correspondientes.

### FE06. Error durante la revisión

1. El administrador o profesional no puede completar la revisión por un error interno.
2. El sistema conserva el reporte y su último estado válido.
3. El sistema registra el error operativo para su atención sin exponerlo al usuario como una decisión de fondo.

## 10. Estados del reporte

El flujo de revisión debe utilizar un conjunto de estados consistente:

- **Recibido:** el sistema aceptó el reporte.
- **En revisión:** el administrador está evaluando el caso.
- **En revisión profesional:** requiere validación nutricional o científica.
- **Requiere información:** se necesita información adicional para continuar.
- **Resuelto:** la revisión concluyó y se tomó la acción que correspondía.
- **Descartado:** no se confirmó una discrepancia que justifique modificar el dato.

Los cambios de estado deben respetar las transiciones permitidas y conservar trazabilidad de los eventos relevantes. El reporte no debe considerarse resuelto solo porque se recibió una notificación.

## 11. Reglas de negocio

- **RN-CU13-01.** El reporte debe identificar el alimento y el tipo de discrepancia.
- **RN-CU13-02.** La descripción del problema será obligatoria.
- **RN-CU13-03.** La fuente de referencia será opcional, pero podrá aportarse para facilitar la revisión.
- **RN-CU13-04.** La creación de un reporte no modificará automáticamente el catálogo.
- **RN-CU13-05.** La recepción de un reporte no implica que la discrepancia haya sido confirmada.
- **RN-CU13-06.** Los reportes deben tener un identificador único y un estado inicial definido.
- **RN-CU13-07.** El sistema debe conservar la fecha de creación y el autor del reporte conforme a la política de privacidad.
- **RN-CU13-08.** Solo los roles autorizados podrán consultar y administrar los reportes internos.
- **RN-CU13-09.** Cuando la revisión afecte valores nutricionales o categorías de impacto glucémico, deberá intervenir el profesional competente según el procedimiento establecido.
- **RN-CU13-10.** La clasificación general de impacto glucémico no cambiará hasta que una modificación haya sido revisada y aprobada.
- **RN-CU13-11.** Las correcciones confirmadas se ejecutarán mediante el procedimiento autorizado de mantenimiento del catálogo.
- **RN-CU13-12.** Cada modificación del dato nutricional deberá generar una auditoría con responsable, fecha y justificación.
- **RN-CU13-13.** La resolución del reporte deberá registrar la decisión y una justificación suficiente.
- **RN-CU13-14.** El reporte no debe utilizarse para solicitar datos clínicos ni mediciones personales de glucosa.
- **RN-CU13-15.** El sistema no asociará el reporte con mediciones personales ni inferirá que el usuario consumió el alimento.
- **RN-CU13-16.** El contenido enviado por el usuario debe validarse y tratarse como dato no confiable.
- **RN-CU13-17.** El sistema debe aplicar límites razonables para prevenir envíos automatizados o abusivos.
- **RN-CU13-18.** Los reportes deben conservarse conforme a la política de retención aprobada para esta función.
- **RN-CU13-19.** El sistema debe evitar exponer datos personales del reportante a usuarios que no estén autorizados para consultarlos.
- **RN-CU13-20.** El sistema no debe presentar la existencia de un reporte como prueba de que un alimento o una clasificación sean incorrectos.

## 12. Requisitos funcionales

- **RF-CU13-01.** El sistema debe permitir iniciar un reporte desde un alimento del catálogo.
- **RF-CU13-02.** Debe asociar el reporte con el identificador del alimento.
- **RF-CU13-03.** Debe permitir seleccionar un tipo de discrepancia.
- **RF-CU13-04.** Debe solicitar una descripción del problema.
- **RF-CU13-05.** Debe permitir incluir una referencia opcional.
- **RF-CU13-06.** Debe validar el alimento, los campos obligatorios, el formato y los límites de entrada.
- **RF-CU13-07.** Debe crear el reporte con identificador único, fecha, autor y estado.
- **RF-CU13-08.** Debe confirmar la recepción una vez guardado el reporte correctamente.
- **RF-CU13-09.** Debe proporcionar una bandeja interna para consultar y gestionar reportes a los roles autorizados.
- **RF-CU13-10.** Debe permitir actualizar el estado del reporte conforme a las transiciones permitidas.
- **RF-CU13-11.** Debe permitir registrar la decisión de revisión y su justificación.
- **RF-CU13-12.** Debe permitir derivar los casos que requieran validación profesional.
- **RF-CU13-13.** Debe registrar trazabilidad de los cambios de estado y de las decisiones de revisión.
- **RF-CU13-14.** Debe permitir identificar reportes duplicados o similares cuando sea técnicamente viable.
- **RF-CU13-15.** No debe cambiar directamente el dato nutricional a partir del envío del reporte.
- **RF-CU13-16.** Debe impedir que usuarios ordinarios consulten reportes internos ajenos o datos privados del reportante.
- **RF-CU13-17.** No debe solicitar ni relacionar mediciones personales de glucosa.
- **RF-CU13-18.** Debe evitar que el reporte se interprete como registro de consumo.
- **RF-CU13-19.** Debe manejar errores de almacenamiento, revisión y notificación sin perder la trazabilidad del reporte.

## 13. Seguridad, privacidad y calidad

1. La identidad del reportante debe obtenerse desde la sesión autenticada.
2. El sistema debe validar los datos de entrada en el servidor.
3. Las consultas de reportes deben limitarse a los roles autorizados.
4. El contenido libre debe tratarse como no confiable y protegerse frente a inyección de código u otros formatos maliciosos.
5. El sistema debe aplicar medidas razonables contra el abuso y la creación automatizada de reportes.
6. El reporte solo debe almacenar información necesaria para revisar la discrepancia.
7. La descripción no debe usarse como espacio para recopilar datos clínicos del usuario.
8. Los errores operativos no deben revelar información sensible de infraestructura.
9. La corrección del catálogo debe mantener la trazabilidad de quién modificó el registro, cuándo y por qué.
10. El sistema debe conservar los estados previos y las decisiones de revisión requeridas para seguir el proceso.

## 14. Criterios de aceptación

- **CA-CU13-01.** El usuario autenticado puede iniciar un reporte desde un alimento.
- **CA-CU13-02.** El formulario identifica correctamente el alimento reportado.
- **CA-CU13-03.** El sistema permite seleccionar el tipo de discrepancia.
- **CA-CU13-04.** El formulario exige una descripción válida.
- **CA-CU13-05.** El usuario puede agregar una referencia opcional.
- **CA-CU13-06.** Un reporte válido recibe un identificador único y estado inicial.
- **CA-CU13-07.** El sistema confirma la recepción solo después de guardar correctamente el reporte.
- **CA-CU13-08.** La presentación de un reporte no cambia los datos nutricionales.
- **CA-CU13-09.** Un administrador autorizado puede revisar el reporte y actualizar su estado.
- **CA-CU13-10.** El sistema permite registrar una decisión de revisión y su justificación.
- **CA-CU13-11.** Los casos que requieren revisión profesional pueden derivarse conforme al flujo establecido.
- **CA-CU13-12.** Una corrección confirmada mediante el procedimiento autorizado genera auditoría.
- **CA-CU13-13.** Un usuario ordinario no puede ver los reportes internos o datos privados de otros usuarios.
- **CA-CU13-14.** El sistema no solicita ni registra mediciones personales como parte del reporte.
- **CA-CU13-15.** El reporte no se interpreta como evidencia de consumo del alimento.
- **CA-CU13-16.** El sistema no correlaciona el reporte con la glucosa del usuario.
- **CA-CU13-17.** Los errores de almacenamiento o notificación no generan confirmaciones falsas ni borran un reporte guardado.
- **CA-CU13-18.** Los errores no exponen información técnica interna.

## 15. Fuera del alcance

- Modificación directa del catálogo por el usuario.
- Confirmación automática de que un dato reportado es incorrecto.
- Clasificación automática de impacto glucémico sin validación.
- Registro de alimentos consumidos.
- Vinculación con mediciones, estadísticas o gráficas personales de glucosa.
- Diagnósticos, recomendaciones clínicas o planes de alimentación.
- Publicación automática de los reportes de otros usuarios.