# CU06. Editar medición de glucosa

## 1. Información general

- **Código:** CU06
- **Nombre:** Editar medición de glucosa
- **Actor principal:** Usuario registrado y autenticado.
- **Objetivo:** Permitir que el usuario corrija los datos de una medición propia registrada previamente, manteniendo la integridad de la información y la trazabilidad de los cambios.
- **Prioridad:** Alta.
- **Tipo:** Caso de uso funcional.
- **Relaciones:** CU04. Registrar medición de glucosa; CU05. Consultar mediciones; CU07. Eliminar medición de glucosa.

## 2. Descripción

El usuario consulta su historial de mediciones, selecciona un registro propio y solicita modificarlo. El sistema presenta los datos actuales, valida los cambios y guarda la actualización cuando se cumplen las reglas de negocio.

La edición conserva la identidad del registro y su fecha de creación. Además, registra la fecha de modificación y los valores anteriores y nuevos de los campos modificados, con acceso restringido a la información de auditoría.

El usuario puede editar una medición en cualquier momento mientras el registro exista y se encuentre disponible para edición. No se establece un límite temporal para la edición.

## 3. Precondiciones

1. El usuario debe tener una cuenta activa.
2. El usuario debe haber iniciado sesión y disponer de una sesión válida.
3. Debe existir la medición que se desea modificar.
4. La medición debe pertenecer al usuario autenticado.
5. La medición no debe encontrarse en estado eliminado.
6. El usuario debe tener permiso para ejecutar la operación.

## 4. Postcondiciones

**Éxito:**

- Se actualizan los campos autorizados de la medición.
- Se conserva el identificador original del registro.
- Se conserva la fecha y hora de creación.
- Se actualiza la fecha y hora de modificación.
- Se registra la auditoría con el usuario responsable, la fecha del cambio y los valores anteriores y nuevos de los campos modificados.
- El usuario recibe una confirmación y puede consultar los datos actualizados.

**Fallo:**

- La medición conserva los datos que tenía antes de la operación.
- No se genera una confirmación de éxito si los cambios no se guardaron.
- El sistema informa el motivo del rechazo sin exponer información sensible.

## 5. Flujo principal

1. El usuario ingresa a la sección de historial de mediciones.
2. El sistema presenta sus registros conforme a los criterios de consulta definidos en CU05.
3. El usuario selecciona una medición.
4. El sistema verifica que el registro exista, se encuentre disponible y pertenezca al usuario autenticado.
5. El usuario selecciona la opción **Editar**.
6. El sistema muestra los datos actuales de la medición.
7. El usuario modifica uno o varios campos permitidos.
8. El usuario confirma la actualización.
9. El sistema valida los datos, los permisos y las reglas de negocio.
10. El sistema comprueba que el registro no haya cambiado desde que se abrió el formulario.
11. Si no existen conflictos, el sistema guarda los cambios de manera consistente.
12. El sistema actualiza la fecha y hora de modificación.
13. El sistema registra los valores anteriores y nuevos de los campos modificados, junto con los metadatos de auditoría.
14. El sistema informa que la actualización se realizó correctamente.
15. Cuando el usuario vuelve al historial, el sistema presenta la información actualizada.

## 6. Flujos alternativos

### A1. El usuario cancela la edición

1. El usuario selecciona la opción de cancelar.
2. El sistema descarta los cambios que no se hayan guardado.
3. El registro original permanece sin modificaciones.

### A2. Los datos ingresados no son válidos

1. El sistema identifica campos obligatorios vacíos, valores no numéricos o datos que incumplen los límites técnicos configurados.
2. El sistema informa cuáles campos deben corregirse.
3. El usuario modifica los datos y vuelve a intentar guardar.

### A3. El registro cambió desde que se abrió el formulario

1. El sistema detecta que la medición fue modificada después de cargar el formulario.
2. El sistema rechaza la actualización desactualizada para evitar sobrescribir los cambios más recientes.
3. El sistema informa que el registro cambió y solicita consultarlo nuevamente.
4. El usuario recarga la medición y decide si necesita efectuar otra modificación.

### A4. El registro no existe o ya no está disponible

1. El sistema detecta que la medición no existe o se encuentra eliminada.
2. El sistema informa que no es posible editarla.
3. No se realiza ninguna modificación.

## 7. Excepciones

- **E1. Sesión expirada:** el sistema solicita autenticarse nuevamente.
- **E2. Acceso no autorizado:** el sistema rechaza la operación si la medición no pertenece al usuario autenticado.
- **E3. Error de persistencia:** el sistema informa que no fue posible guardar los cambios y conserva los datos anteriores.
- **E4. Error de conexión:** el sistema no confirma una actualización que no haya sido verificada.
- **E5. Conflicto de actualización:** el sistema rechaza la modificación desactualizada y solicita recargar el registro.
- **E6. Registro eliminado:** el sistema impide editar una medición que ya fue eliminada lógicamente.
- **E7. Error de auditoría:** la actualización no debe quedar confirmada si no se puede registrar la auditoría obligatoria de forma consistente con el cambio.

## 8. Datos que pueden modificarse

El usuario puede modificar todos los siguientes campos de la medición:

- Valor de glucosa.
- Unidad de medida: mg/dL o mmol/L.
- Fecha y hora en que se tomó la medición.
- Contexto de la medición, cuando corresponda: ayunas, antes de comer, después de comer, otro o sin especificar.
- Observaciones.

Los siguientes campos no son editables directamente desde el formulario:

- Identificador de la medición.
- Identificador del usuario propietario.
- Fecha y hora de creación.
- Fecha y hora de la última modificación, que establece el sistema.
- Datos técnicos de auditoría.

La fecha y hora de la medición representan cuándo se tomó la medición. No deben confundirse con la fecha de creación del registro ni con la fecha de su última modificación.

## 9. Reglas de negocio

- **RN-CU06-01. Propiedad del registro:** únicamente el usuario propietario puede editar una medición.
- **RN-CU06-02. Autorización en el servidor:** la propiedad y los permisos se verifican en el backend en cada solicitud.
- **RN-CU06-03. Validación de datos:** los campos deben cumplir las validaciones técnicas documentadas en CU04.
- **RN-CU06-04. Unidad explícita:** el sistema debe mostrar y conservar la unidad correspondiente al valor registrado, sin conversiones silenciosas.
- **RN-CU06-05. Identidad del registro:** editar una medición no crea un nuevo registro ni cambia su identificador.
- **RN-CU06-06. Fecha de creación inmutable:** la edición no cambia la fecha y hora originales de creación.
- **RN-CU06-07. Fecha de actualización:** toda edición exitosa actualiza la marca temporal de modificación.
- **RN-CU06-08. Auditoría obligatoria:** el sistema registra quién realizó el cambio, cuándo se realizó y los valores anteriores y nuevos de cada campo modificado.
- **RN-CU06-09. Acceso restringido a la auditoría:** los valores anteriores y nuevos deben protegerse como información sensible y no exponerse en las consultas ordinarias.
- **RN-CU06-10. Sin límite temporal de edición:** el usuario puede editar una medición en cualquier momento mientras exista y no esté eliminada, sujeto a las validaciones aplicables.
- **RN-CU06-11. Sin edición de eliminados:** una medición eliminada lógicamente no puede editarse desde la interfaz ordinaria.
- **RN-CU06-12. Prevención de sobrescritura:** el sistema rechaza las actualizaciones desactualizadas y exige consultar nuevamente el registro.
- **RN-CU06-13. Sin interpretación clínica automática:** la edición no genera diagnósticos ni recomendaciones médicas automáticas.
- **RN-CU06-14. Consistencia de los cambios:** la actualización de la medición y el registro de auditoría deben ejecutarse de forma consistente.

## 10. Requisitos funcionales relacionados

- **RF-CU06-01:** el sistema debe permitir seleccionar una medición propia para editarla.
- **RF-CU06-02:** el sistema debe mostrar los datos actuales antes de permitir su modificación.
- **RF-CU06-03:** el sistema debe permitir modificar valor, unidad, fecha y hora de medición, contexto y observaciones.
- **RF-CU06-04:** el sistema debe validar los campos modificados antes de guardarlos.
- **RF-CU06-05:** el sistema debe impedir que un usuario modifique mediciones de terceros.
- **RF-CU06-06:** el sistema debe conservar el identificador y la fecha de creación del registro.
- **RF-CU06-07:** el sistema debe actualizar la fecha de modificación después de una edición exitosa.
- **RF-CU06-08:** el sistema debe registrar los valores anteriores y nuevos de los campos modificados.
- **RF-CU06-09:** el sistema debe restringir el acceso a los registros de auditoría.
- **RF-CU06-10:** el sistema debe impedir la edición de mediciones eliminadas.
- **RF-CU06-11:** el sistema debe detectar conflictos de actualización y rechazar cambios desactualizados.
- **RF-CU06-12:** el sistema debe informar el resultado de la operación.

## 11. Seguridad y protección de datos

- Utilizar HTTPS para proteger la comunicación.
- Validar los permisos en el backend, sin depender únicamente de controles visuales.
- Obtener la identidad del usuario desde el contexto de autenticación, no de un identificador enviado libremente por el cliente.
- Aplicar las medidas de protección contra CSRF que correspondan al esquema de autenticación mediante cookies.
- Restringir el acceso a los registros de auditoría.
- Evitar almacenar información sensible innecesaria en los registros técnicos.
- Utilizar transacciones o un mecanismo equivalente para mantener la consistencia entre la actualización y la auditoría.
- Implementar control de concurrencia mediante una versión del registro o una marca de actualización verificable.
- No presentar valores de glucosa como diagnósticos ni utilizar su modificación para emitir recomendaciones médicas automáticas.

## 12. Criterios de aceptación

1. El usuario puede abrir y editar una medición propia que se encuentre disponible.
2. El sistema muestra los datos actuales antes de guardar.
3. El usuario puede modificar cualquiera de los campos editables definidos.
4. Los datos inválidos son rechazados con mensajes comprensibles.
5. Un usuario no puede editar la medición de otra persona, aunque conozca su identificador.
6. Una edición exitosa conserva el identificador y la fecha de creación.
7. La fecha de modificación cambia después de una actualización exitosa.
8. La unidad de medida se conserva de manera explícita.
9. La cancelación no modifica el registro.
10. Los valores anteriores y nuevos de los campos modificados quedan registrados en la auditoría.
11. La auditoría no queda expuesta en las consultas ordinarias del usuario.
12. Una actualización desactualizada es rechazada y requiere recargar el registro.
13. Una medición eliminada no puede editarse desde la interfaz ordinaria.
14. Un error de persistencia o auditoría no produce una confirmación falsa de éxito.
15. Los cambios guardados se reflejan correctamente al volver a consultar el historial.
