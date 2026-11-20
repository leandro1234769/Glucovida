# CU05. Consultar mediciones de glucosa

## 1. Identificación

| Campo | Descripción |
|---|---|
| **ID** | CU05 |
| **Nombre | Consultar mediciones de glucosa |
| **Actor principal** | Usuario |
| **Actores secundarios** | Sistema de GlucoVida |
| **Objetivo** | Permitir que el usuario consulte sus mediciones de glucosa registradas, revise sus detalles y localice registros mediante filtros y ordenamiento. |
| **Prioridad** | Alta |
| **Tipo** | Caso de uso principal |

## 2. Descripción

El usuario autenticado accede al historial de mediciones de glucosa. El sistema consulta los registros asociados a su cuenta y los presenta en una lista ordenada cronológicamente. El usuario puede filtrar las mediciones por un intervalo de fechas, seleccionar una medición para consultar sus detalles y cambiar el orden de visualización.

Cada registro debe mostrar explícitamente su unidad de medida. El sistema no debe interpretar una medición inusual como un diagnóstico médico ni generar alertas clínicas automáticas desde este caso de uso.

## 3. Precondiciones

- El usuario debe tener una cuenta activa.
- El usuario debe haber iniciado sesión.
- La sesión debe estar vigente.
- El sistema y la base de datos deben estar disponibles.

No es obligatorio que el usuario tenga mediciones registradas previamente.

## 4. Disparador

El usuario selecciona la opción **«Historial de mediciones»** o **«Consultar mediciones»** desde el panel principal de GlucoVida.

## 5. Información que se muestra

| Campo | Descripción |
|---|---|
| Fecha y hora de medición | Momento en que el usuario obtuvo la medición. |
| Valor | Valor numérico registrado. |
| Unidad | `mg/dL` o `mmol/L`, mostrada junto al valor. |
| Contexto | Ayunas, antes de comer, después de comer, otro o sin especificar, cuando esté disponible. |
| Fecha de registro | Momento en que la medición fue guardada en GlucoVida, si se muestra en el detalle. |
| Observaciones | Comentario ingresado por el usuario, si existe. |

La fecha de medición y la fecha de registro representan momentos diferentes y no deben confundirse.

## 6. Flujo principal

| Paso | Actor | Acción |
|---|---|---|
| 1 | Usuario | Selecciona «Historial de mediciones». |
| 2 | Sistema | Verifica que la sesión esté vigente y que el usuario tenga autorización. |
| 3 | Sistema | Consulta las mediciones asociadas a la cuenta autenticada. |
| 4 | Sistema | Ordena los registros por fecha y hora de medición, del más reciente al más antiguo. |
| 5 | Sistema | Muestra el historial con el valor, la unidad y la fecha y hora de cada medición. |
| 6 | Usuario | Selecciona una medición para consultar sus detalles. |
| 7 | Sistema | Verifica nuevamente que la medición pertenezca al usuario autenticado. |
| 8 | Sistema | Muestra los detalles disponibles de la medición seleccionada. |

## 7. Flujos alternativos

### FA01. El usuario no tiene mediciones registradas

- En el paso 3, el sistema determina que la cuenta no tiene mediciones.
- El sistema muestra un mensaje indicando que todavía no existen registros.
- El sistema ofrece la opción de registrar la primera medición.
- No se presenta información ficticia ni valores de ejemplo como si fueran datos reales.

### FA02. Filtrar por intervalo de fechas

- El usuario selecciona un filtro por fecha inicial y fecha final.
- El sistema verifica que ambas fechas sean válidas y que la fecha inicial no sea posterior a la final.
- El sistema consulta únicamente las mediciones propias cuyo momento de medición esté dentro del intervalo seleccionado.
- El sistema muestra los resultados ordenados cronológicamente.

### FA03. Cambiar el orden de visualización

- El usuario selecciona el orden más reciente o más antiguo.
- El sistema actualiza el orden de los resultados.
- Los filtros activos se mantienen.

### FA04. Consultar una medición específica

- El usuario selecciona un registro de la lista.
- El sistema valida la autorización sobre ese registro.
- El sistema muestra la información detallada disponible.
- El usuario puede regresar al historial sin perder los filtros activos, si la interfaz lo permite.

### FA05. Cambiar la unidad de visualización

- Si GlucoVida implementa una opción para visualizar valores en otra unidad, el usuario selecciona la unidad deseada.
- El sistema realiza una conversión explícita y consistente, si corresponde.
- La interfaz identifica claramente la unidad mostrada.
- La conversión no debe modificar silenciosamente el valor original almacenado.
- Si la funcionalidad de conversión no está implementada, se muestra el valor en su unidad original.

## 8. Flujos de excepción

### FE01. Intervalo de fechas inválido

- El sistema detecta que la fecha inicial es posterior a la fecha final o que el formato es inválido.
- El sistema informa cómo corregir el intervalo.
- No ejecuta la consulta con parámetros inválidos.

### FE02. Sesión expirada

- El usuario intenta consultar el historial con una sesión vencida.
- El sistema rechaza la solicitud.
- El usuario debe iniciar sesión nuevamente.

### FE03. Acceso a una medición no autorizada

- La solicitud intenta consultar una medición que no pertenece al usuario autenticado.
- El sistema rechaza el acceso sin revelar el contenido del registro.
- El evento se registra cuando corresponda según la política de seguridad.

### FE04. Error al consultar la base de datos

- El sistema no puede recuperar las mediciones.
- El sistema informa que el historial no está disponible temporalmente.
- No muestra resultados incompletos como si fueran el historial completo.
- El usuario puede volver a intentarlo.

## 9. Postcondiciones

### Si la consulta es exitosa:

- El usuario visualiza únicamente sus propias mediciones.
- Los registros se presentan con sus unidades explícitas.
- Los filtros y el ordenamiento reflejan los criterios seleccionados.
- Consultar los datos no modifica las mediciones almacenadas.

### Si la consulta falla:

- No se revela información de otros usuarios.
- No se alteran ni eliminan mediciones.
- El sistema informa que no fue posible completar la consulta.

## 10. Reglas de negocio relacionadas

| Código | Regla |
|---|---|
| **RN38** | Solo un usuario autenticado con cuenta activa puede consultar su historial de mediciones. |
| **RN39** | El usuario solo puede consultar mediciones asociadas a su propia cuenta, salvo que exista otra funcionalidad explícita y autorizada. |
| **RN40** | Las mediciones se muestran por defecto de la más reciente a la más antigua, según la fecha y hora de medición. |
| **RN41** | Toda medición debe mostrar su unidad de medida de forma explícita. |
| **RN42** | La fecha y hora de medición deben distinguirse de la fecha y hora de creación del registro. |
| **RN43** | El filtro por fechas debe validar el intervalo antes de ejecutar la consulta. |
| **RN44** | Las conversiones de unidades no deben alterar silenciosamente el valor original almacenado. |
| **RN45** | La consulta del historial no debe generar diagnósticos ni alertas clínicas automáticas basadas únicamente en valores inusuales. |
| **RN46** | El sistema debe aplicar controles de autorización en el backend para cada consulta de una medición individual. |

## 11. Requisitos funcionales relacionados

- **RF32:** El sistema debe permitir consultar el historial personal de mediciones de glucosa.
- **RF33:** El sistema debe presentar el valor y la unidad de cada medición.
- **RF34:** El sistema debe mostrar la fecha y hora en que se obtuvo cada medición.
- **RF35:** El sistema debe permitir filtrar mediciones por un intervalo de fechas.
- **RF36:** El sistema debe permitir ordenar las mediciones de forma ascendente o descendente por fecha y hora.
- **RF37:** El sistema debe permitir consultar los detalles de una medición individual.
- **RF38:** El sistema debe impedir el acceso a mediciones que pertenezcan a otros usuarios.
- **RF39:** El sistema debe informar cuando no existan registros o cuando ocurra un error de consulta.

## 12. Consideraciones de seguridad y privacidad

- Toda consulta debe estar autenticada y autorizada en el backend.
- El servidor debe obtener la identidad del usuario desde el contexto autenticado, no confiar en un `usuario_id` enviado por el cliente.
- Las consultas deben limitarse al propietario de los registros.
- Los identificadores de las mediciones no deben considerarse un mecanismo de autorización.
- La interfaz no debe mostrar datos clínicos en notificaciones o registros técnicos innecesarios.
- Si se implementa paginación, el servidor debe aplicar los filtros y las restricciones de propiedad en cada página.
- Las comunicaciones deben estar protegidas mediante HTTPS.
- Si la autenticación utiliza cookies, deben mantenerse las protecciones necesarias frente a solicitudes no autorizadas, incluidos los riesgos de CSRF.

## 13. Modelo de datos relacionado

Este caso de uso utiliza la entidad `MedicionGlucosa` definida en CU04. No necesita una entidad adicional para consultar el historial.

| Campo utilizado | Propósito |
|---|---|
| `id` | Identificar la medición seleccionada. |
| `usuario_id` | Restringir los registros a la cuenta autenticada. |
| `valor` | Mostrar el valor registrado. |
| `unidad` | Identificar la unidad original. |
| `fecha_hora_medicion` | Filtrar y ordenar las mediciones. |
| `contexto` | Mostrar las circunstancias de la medición. |
| `observaciones` | Mostrar comentarios disponibles. |
| `fecha_hora_creacion` | Distinguir cuándo se registró el dato en el sistema. |

### Consideración de rendimiento

Cuando el historial tenga muchos registros, se recomienda implementar paginación en el servidor e índices de base de datos apropiados, especialmente sobre la combinación de `usuario_id` y `fecha_hora_medicion`.

## 14. Criterios de aceptación

1. Un usuario autenticado puede consultar sus mediciones registradas.
2. Un usuario sin mediciones ve un estado vacío con una opción para registrar una medición.
3. Las mediciones aparecen ordenadas de la más reciente a la más antigua por defecto.
4. El usuario puede filtrar por fecha inicial y fecha final.
5. El sistema rechaza intervalos de fechas inválidos.
6. Cada registro muestra explícitamente su unidad de medida.
7. El usuario puede abrir una medición individual y consultar sus detalles.
8. El sistema impide consultar mediciones pertenecientes a otras cuentas, incluso si se modifica manualmente el identificador enviado en la solicitud.
9. La consulta no modifica los datos almacenados ni genera diagnósticos clínicos.
10. Los errores de consulta se comunican sin revelar información sensible.
