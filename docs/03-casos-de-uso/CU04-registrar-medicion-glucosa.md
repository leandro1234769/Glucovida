# CU04. Registrar medición de glucosa

## 1. Identificación

| Campo | Descripción |
|---|---|
| **ID** | CU04 |
| **Nombre** | Registrar medición de glucosa |
| **Actor principal** | Usuario |
| **Actores secundarios** | Sistema de GlucoVida |
| **Objetivo** | Permitir que un usuario registre una medición de glucosa con sus datos asociados para conservar un historial personal y facilitar su consulta posterior. |
| **Prioridad** | Alta |
| **Tipo** | Caso de uso principal |

## 2. Descripción

El usuario autenticado ingresa el valor de una medición de glucosa, selecciona la unidad de medida y registra la fecha y hora correspondientes. También puede indicar el contexto en el que se realizó la medición, por ejemplo, en ayunas o después de comer.

El sistema valida los datos, verifica que la operación esté autorizada y almacena la medición asociada a la cuenta del usuario.

GlucoVida registra y organiza la información proporcionada, pero no diagnostica enfermedades ni recomienda cambios de medicamentos a partir de una medición individual.

## 3. Precondiciones

- El usuario debe tener una cuenta activa.
- El usuario debe haber iniciado sesión.
- La sesión debe encontrarse vigente.
- El servicio de registro y la base de datos deben estar disponibles.

## 4. Disparador

El usuario selecciona la opción **«Registrar medición»** desde el panel principal o desde la sección de seguimiento de glucosa.

## 5. Datos que debe ingresar el usuario

| Campo | Obligatorio | Descripción |
|---|---|---|
| Valor de glucosa | Sí | Valor numérico obtenido de la medición. |
| Unidad de medida | Sí | Unidad utilizada para expresar el valor, inicialmente mg/dL o mmol/L. |
| Fecha de la medición | Sí | Día en que se realizó la medición. |
| Hora de la medición | Sí | Hora aproximada o exacta en que se realizó. |
| Contexto de la medición | No | Circunstancia de la medición, como ayunas, antes de comer, después de comer u otro contexto. |
| Observaciones | No | Comentario breve que el usuario quiera asociar al registro. |

**Decisión de diseño:** la fecha y la hora de la medición deben ser distintas del momento en que el usuario registra la información en GlucoVida. Por ejemplo, puede ingresar hoy una medición que tomó ayer.

## 6. Flujo principal

| Paso | Actor | Acción |
|---|---|---|
| 1 | Usuario | Selecciona «Registrar medición». |
| 2 | Sistema | Verifica que el usuario tenga una sesión válida y permiso para registrar información. |
| 3 | Sistema | Muestra el formulario de registro de glucosa. |
| 4 | Usuario | Ingresa el valor de glucosa. |
| 5 | Usuario | Selecciona la unidad de medida. |
| 6 | Usuario | Ingresa la fecha y hora de la medición. |
| 7 | Usuario | Selecciona el contexto de la medición, si desea especificarlo. |
| 8 | Usuario | Agrega observaciones opcionales, si corresponde. |
| 9 | Usuario | Envía el formulario. |
| 10 | Sistema | Valida los campos obligatorios, los formatos, la unidad y las reglas de consistencia. |
| 11 | Sistema | Comprueba que el valor sea válido según los límites técnicos configurados y que la fecha y hora sean admisibles. |
| 12 | Sistema | Asocia la medición con la cuenta autenticada, sin confiar en un identificador de usuario enviado libremente desde el formulario. |
| 13 | Sistema | Guarda la medición en la base de datos. |
| 14 | Sistema | Confirma que el registro fue guardado y ofrece la opción de consultar el historial. |

## 7. Flujos alternativos

### FA01. Datos incompletos

- En el paso 10, el sistema identifica que falta uno o más campos obligatorios.
- El sistema indica qué información debe completar el usuario.
- El usuario corrige los datos.
- El flujo continúa desde el paso 9.

### FA02. Unidad de medida diferente

- El usuario selecciona mg/dL o mmol/L.
- El sistema valida el valor según la unidad seleccionada.
- Si GlucoVida presenta posteriormente los valores en una unidad diferente, deberá realizar una conversión explícita y consistente.
- El sistema conserva la unidad original o almacena una representación normalizada, según la estrategia definida para la base de datos.

### FA03. El usuario registra una medición anterior

- El usuario ingresa una fecha y hora anteriores al momento actual.
- El sistema valida que la fecha no sea futura y que se encuentre dentro de los límites de registro retroactivo definidos.
- Si cumple las reglas, el sistema guarda la medición con la fecha y hora indicadas por el usuario.

### FA04. Contexto de medición no especificado

- El usuario decide no seleccionar un contexto.
- El sistema permite continuar porque el campo es opcional.
- La medición se guarda con el contexto sin especificar.
- El sistema no debe asumir que fue tomada en ayunas ni después de comer.

### FA05. Posible registro duplicado

- El sistema detecta una medición que coincide con otra en campos como valor, fecha y hora.
- El sistema informa que podría tratarse de un registro duplicado y solicita confirmación.
- El usuario puede regresar y revisar los datos o confirmar que desea guardar la nueva medición.
- El sistema permite registros similares cuando corresponden a mediciones distintas.

## 8. Flujos de excepción

### FE01. Valor numérico inválido

- El sistema detecta que el valor no es numérico, es negativo, es cero o no cumple los límites técnicos definidos.
- El sistema rechaza el registro.
- El sistema informa que debe ingresarse un valor válido para la unidad seleccionada.
- No se guarda la medición.

### FE02. Fecha u hora inválida

- El sistema detecta una fecha inexistente, una hora inválida o una fecha futura no permitida.
- El sistema informa el problema.
- El usuario debe corregir los datos antes de continuar.
- No se guarda la medición hasta superar las validaciones.

### FE03. Sesión expirada

- El usuario intenta enviar el formulario con una sesión vencida.
- El sistema rechaza la operación.
- El usuario debe iniciar sesión nuevamente.
- La medición no se guarda sin una autenticación válida.

### FE04. Acceso no autorizado

- El sistema detecta que la solicitud intenta asociar la medición a una cuenta distinta de la autenticada.
- El sistema rechaza la operación y registra el evento de seguridad cuando corresponda.
- No se almacena la medición bajo una cuenta no autorizada.

### FE05. Error de base de datos

- El sistema no logra guardar la medición.
- El sistema informa que no fue posible completar el registro.
- No debe confirmar el éxito si la transacción no se completó.
- El usuario puede volver a intentarlo.

## 9. Postcondiciones

### Si el registro es exitoso:

- La medición queda almacenada en la base de datos.
- La medición queda asociada a la cuenta autenticada.
- Se conservan el valor, la unidad, la fecha y hora de la medición y los campos opcionales suministrados.
- El registro queda disponible para las funcionalidades autorizadas de historial y estadísticas.

### Si el registro falla:

- No se crea una medición incompleta o inválida.
- No se modifica información perteneciente a otros usuarios.
- El sistema informa que la operación no pudo completarse.

## 10. Reglas de negocio relacionadas

| Código | Regla |
|---|---|
| **RN27** | Solo un usuario autenticado con cuenta activa puede registrar mediciones de glucosa. |
| **RN28** | Cada medición debe asociarse a la cuenta autenticada en el servidor. |
| **RN29** | El valor de glucosa, la unidad, la fecha y la hora son campos obligatorios. |
| **RN30** | El valor debe ser numérico y cumplir los límites técnicos definidos para la unidad seleccionada. |
| **RN31** | La fecha y hora de la medición deben representar el momento en que se obtuvo el valor, no necesariamente el momento de su registro en GlucoVida. |
| **RN32** | El contexto y las observaciones son opcionales y no deben inferirse si el usuario no los proporciona. |
| **RN33** | Una medición registrada no debe quedar accesible para usuarios distintos de su propietario, salvo que exista una funcionalidad explícita y autorizada que lo permita. |
| **RN34** | El sistema debe validar la información en el backend, aunque también existan validaciones en la interfaz. |
| **RN35** | GlucoVida no debe presentar una medición aislada como diagnóstico médico ni utilizarla por sí sola para recomendar cambios de medicación. |
| **RN36** | Los registros de mediciones deben conservar la trazabilidad necesaria para distinguir la fecha de la medición de la fecha de creación del registro. |
| **RN37** | Los datos de salud deben tratarse como información sensible y protegerse mediante controles de acceso, transmisión segura y almacenamiento adecuado. |

## 11. Requisitos funcionales relacionados

- **RF24:** El sistema debe permitir que un usuario autenticado registre una medición de glucosa.
- **RF25:** El sistema debe permitir seleccionar la unidad de medida de la medición.
- **RF26:** El sistema debe permitir registrar la fecha y hora de la medición.
- **RF27:** El sistema debe permitir asociar un contexto opcional a la medición.
- **RF28:** El sistema debe validar los datos antes de guardarlos.
- **RF29:** El sistema debe asociar cada medición con la cuenta autenticada.
- **RF30:** El sistema debe confirmar si el registro se completó correctamente.
- **RF31:** El sistema debe impedir que usuarios no autorizados registren o modifiquen mediciones de otras cuentas.

## 12. Consideraciones de seguridad y privacidad

- Toda comunicación entre el cliente y el servidor debe utilizar HTTPS.
- Las operaciones deben requerir autenticación y autorización en el backend.
- El identificador del propietario debe obtenerse de la identidad autenticada, no confiarse al formulario.
- El acceso a mediciones debe comprobarse en cada consulta o modificación.
- Los registros técnicos no deben incluir innecesariamente valores clínicos ni otros datos sensibles.
- La base de datos debe aplicar controles de acceso y medidas de protección apropiadas para información de salud.
- Si se utiliza autenticación basada en cookies, las solicitudes que modifican información deben contemplar las defensas necesarias contra CSRF.
- Los datos deben utilizarse únicamente para los fines informados al usuario y autorizados por la política de tratamiento de datos.

## 13. Consideraciones clínicas y de validación

- La validación técnica de un número no determina por sí sola si una medición es clínicamente normal o anormal.
- Los límites de entrada deben definirse a partir de fuentes clínicas confiables y revisarse con el alcance real de la aplicación.
- El sistema debe diferenciar entre una advertencia informativa y una conclusión médica.
- Si en una versión futura se muestran alertas relacionadas con valores altos o bajos, sus reglas y mensajes deben definirse por separado y validarse clínicamente.
- GlucoVida no debe sugerir que el usuario cambie o suspenda medicamentos basándose únicamente en la información registrada.

## 14. Modelo de datos preliminar

### Entidad: MedicionGlucosa

| Campo | Tipo lógico | Restricción o descripción |
|---|---|---|
| `id` | Identificador | Clave primaria; identificador único de la medición. |
| `usuario_id` | Identificador | Clave foránea hacia la cuenta propietaria. Obligatorio. |
| `valor` | Decimal | Obligatorio; precisión definida por la unidad y la interfaz. |
| `unidad` | Enumeración | Valores permitidos: `mg/dL`, `mmol/L`. |
| `fecha_hora_medicion` | Fecha y hora | Obligatorio; momento en que se obtuvo la medición. |
| `contexto` | Enumeración nullable | Ayunas, antes de comer, después de comer, otro o sin especificar. |
| `observaciones` | Texto nullable | Comentario opcional con longitud máxima definida. |
| `fecha_hora_creacion` | Fecha y hora | Momento en que el sistema guardó el registro. |
| `fecha_hora_actualizacion` | Fecha y hora nullable | Se completa si la medición se modifica posteriormente. |

### Relaciones

- Un usuario puede tener muchas mediciones de glucosa.
- Cada medición pertenece a un único usuario.
- Una medición no requiere crear un nuevo perfil ni duplicar los datos personales del usuario.

**Relación conceptual:** `Usuario 1 ─── N MedicionGlucosa`

## 15. Criterios de aceptación

1. Un usuario autenticado puede registrar una medición con todos los campos obligatorios válidos.
2. El sistema rechaza un valor que no cumple las validaciones técnicas definidas.
3. El sistema permite registrar una medición anterior si cumple las reglas de fecha retroactiva.
4. El sistema conserva la unidad seleccionada y la fecha y hora de la medición.
5. El sistema no permite asociar la medición a otro usuario manipulando la solicitud.
6. El sistema informa correctamente cuando la operación falla.
7. Un usuario no puede consultar ni modificar mediciones de otra cuenta mediante acceso directo a un identificador.
8. El sistema no presenta el resultado de la validación numérica como diagnóstico médico.
