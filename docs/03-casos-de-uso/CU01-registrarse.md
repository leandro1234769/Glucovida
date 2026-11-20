# CU01. Registrarse

## 1. Información general

- **Código:** CU01
- **Nombre:** Registrarse
- **Actor principal:** Visitante.
- **Objetivo:** Permitir que una persona cree una cuenta en GlucoVida, verifique su correo electrónico y conozca las condiciones de uso y tratamiento de datos aplicables.
- **Prioridad:** Alta.
- **Disparador:** El visitante selecciona la opción de registro.
- **Relación con otros casos de uso:** CU02. Iniciar sesión; CU03. Gestionar perfil.
- **Alcance:** Creación de cuenta, verificación del correo y registro de las aceptaciones y autorizaciones correspondientes.

## 2. Descripción

El visitante diligencia el formulario de registro con sus datos de identificación básicos, correo electrónico y contraseña. El sistema valida la información, registra la solicitud y envía un enlace de verificación al correo suministrado.

La cuenta solo se activa después de que el visitante complete correctamente la verificación de correo y cumpla las condiciones obligatorias de registro. La autorización para tratar datos sensibles de salud debe presentarse de forma separada y explícita, sin confundirse con la aceptación de los términos del servicio.

El propósito informado para el tratamiento de datos de glucosa comprende permitir al usuario registrar, consultar, editar y eliminar sus propias mediciones conforme a las funcionalidades de GlucoVida, y consultar sus estadísticas descriptivas e historial visual. No incluye elaborar dietas, diagnosticar enfermedades, predecir su respuesta a alimentos ni correlacionar consultas del catálogo con mediciones.

El catálogo de alimentos es una funcionalidad independiente. GlucoVida no debe utilizar las consultas de alimentos como prueba de consumo ni vincular esas consultas con las mediciones personales.

## 3. Precondiciones

1. El visitante puede acceder al formulario público de registro.
2. El sistema de registro está disponible.
3. El servicio de envío de correo electrónico está configurado o cuenta con un mecanismo controlado para gestionar temporalmente su indisponibilidad.
4. Se encuentran disponibles las versiones vigentes de los términos del servicio y de la política de privacidad.

## 4. Postcondiciones

### 4.1. Registro completado

1. Existe una cuenta asociada con los datos válidos suministrados.
2. El correo electrónico ha sido verificado.
3. La cuenta tiene el rol predeterminado de usuario.
4. El sistema conserva evidencia de las aceptaciones requeridas y, cuando se otorgue, de la autorización separada para tratar datos sensibles.
5. El usuario puede iniciar sesión conforme a CU02.

### 4.2. Registro pendiente de verificación

1. La cuenta permanece en estado pendiente de verificación.
2. No se permite iniciar sesión con esa cuenta.
3. El sistema conserva solo la información necesaria para finalizar el proceso durante el período definido por la política de retención.

### 4.3. No se concede autorización para datos sensibles

Si se crea una cuenta sin la autorización requerida para tratar datos sensibles, el sistema no debe procesar mediciones de glucosa ni habilitar las funcionalidades que dependan de ese tratamiento hasta que exista una autorización válida. La disponibilidad final de las funciones no dependientes de datos sensibles debe ajustarse a la política de acceso definida para la aplicación.

## 5. Datos de entrada

Campos del formulario:

- Nombres.
- Apellidos.
- Correo electrónico.
- Contraseña.
- Confirmación de contraseña.
- Aceptación de los términos y condiciones.
- Constancia de haber sido informado sobre la política de privacidad.
- Autorización separada, explícita e inequívoca para el tratamiento de datos sensibles de salud, cuando corresponda a la activación de funcionalidades que los procesan.

Los campos de registro no deben solicitar datos de glucosa, diagnósticos, medicamentos, hábitos alimenticios ni información clínica.

## 6. Datos de salida

- Identificador interno de la cuenta.
- Estado de la cuenta.
- Confirmación de envío del mensaje de verificación.
- Mensajes de validación o error.
- Evidencia de las aceptaciones y autorizaciones registradas, con la versión de los documentos y la fecha correspondiente.

La evidencia de autorización debe almacenarse de forma que pueda demostrarse qué opción aceptó el usuario y bajo qué texto vigente, de acuerdo con la política de protección de datos.

## 7. Flujo principal

1. El visitante selecciona “Registrarse”.
2. El sistema muestra el formulario y las versiones vigentes de los documentos informativos.
3. El visitante completa sus nombres, apellidos, correo y contraseña.
4. El visitante confirma la contraseña.
5. El sistema presenta por separado la aceptación de términos, la información de privacidad y la autorización de tratamiento de datos sensibles.
6. El visitante revisa y confirma las opciones que correspondan.
7. El sistema valida los campos y las reglas de contraseña.
8. El sistema verifica que el correo no esté asociado con otra cuenta registrada.
9. El sistema crea una cuenta con rol predeterminado de usuario y estado pendiente de verificación.
10. El sistema almacena la evidencia de las aceptaciones y autorizaciones otorgadas, junto con la versión de los documentos.
11. El sistema genera un mecanismo de verificación de un solo uso, con caducidad.
12. El sistema envía el mensaje de verificación al correo suministrado.
13. El visitante abre el enlace recibido.
14. El sistema valida la integridad, vigencia y uso del mecanismo de verificación.
15. El sistema marca el correo como verificado y activa la cuenta.
16. El sistema presenta la confirmación y permite continuar a CU02, Iniciar sesión.

## 8. Flujos alternativos

### FA01. El correo ya está registrado

1. El visitante intenta registrarse con un correo que ya existe.
2. El sistema no crea una segunda cuenta.
3. El sistema muestra un mensaje neutral y permite continuar con la recuperación de acceso o con el inicio de sesión.

### FA02. Correo pendiente de verificación

1. El visitante intenta registrarse con un correo que corresponde a una cuenta pendiente.
2. El sistema aplica el proceso de reenvío de verificación, si se cumplen sus límites.
3. El sistema no crea una cuenta duplicada.

### FA03. Reenvío del enlace de verificación

1. El visitante solicita un nuevo mensaje de verificación.
2. El sistema verifica los límites de reenvío.
3. El sistema emite un mecanismo válido y aplica las reglas definidas para los enlaces anteriores.
4. El sistema informa el resultado sin revelar información innecesaria sobre la existencia de cuentas.

### FA04. Autorización de datos sensibles no concedida

1. El visitante no otorga la autorización separada para el tratamiento de datos sensibles.
2. El sistema no debe registrar esa autorización como concedida.
3. No se habilitan las funciones que requieren procesar esos datos.
4. El sistema informa claramente cuáles funcionalidades necesitan autorización, de acuerdo con las condiciones de acceso establecidas.

## 9. Flujos de excepción

### FE01. Campos incompletos o inválidos

El sistema identifica los campos que no cumplen las reglas, informa cómo corregirlos y no crea la cuenta hasta que los datos obligatorios sean válidos.

### FE02. Contraseña no válida

El sistema rechaza la contraseña e informa los requisitos aplicables sin revelar información interna.

### FE03. Error al enviar el correo

El sistema evita activar la cuenta sin verificar el correo, informa que el mensaje no pudo enviarse e implementa el mecanismo de reintento controlado que corresponda.

### FE04. Enlace expirado, inválido o usado

El sistema rechaza la verificación e informa que debe solicitarse un nuevo enlace. Un mecanismo usado no puede volver a activar una cuenta ni verificar otro correo.

### FE05. Error al guardar la cuenta o la evidencia de autorización

El sistema no confirma el registro como exitoso si no puede guardar de forma consistente la cuenta y las evidencias que correspondan. Los errores deben gestionarse sin dejar estados parciales utilizables.

## 10. Reglas de negocio

- **RN-CU01-01.** El correo electrónico debe ser único por cuenta.
- **RN-CU01-02.** La cuenta debe permanecer pendiente hasta que el correo sea verificado.
- **RN-CU01-03.** Cada cuenta creada por el flujo público tendrá el rol predeterminado de usuario.
- **RN-CU01-04.** El registro no debe permitir que el visitante asigne o eleve su propio rol.
- **RN-CU01-05.** La contraseña no puede almacenarse en texto plano.
- **RN-CU01-06.** La contraseña debe almacenarse mediante bcrypt con factor de trabajo 12, conforme a la decisión técnica vigente del proyecto.
- **RN-CU01-07.** Los mecanismos de verificación deben ser de un solo uso, contar con vigencia limitada y almacenarse de forma segura.
- **RN-CU01-08.** No se permitirá iniciar sesión con una cuenta pendiente de verificación.
- **RN-CU01-09.** La aceptación de términos y la información de privacidad deben distinguirse de la autorización de tratamiento de datos sensibles.
- **RN-CU01-10.** La autorización de datos sensibles debe ser explícita, separada y demostrable.
- **RN-CU01-11.** La autorización no se debe marcar como otorgada si el usuario no realizó una acción afirmativa.
- **RN-CU01-12.** Las funciones que requieren datos sensibles no deben procesarlos mientras no exista autorización válida.
- **RN-CU01-13.** La finalidad informada de los datos de glucosa se limita a la gestión de mediciones propias, su consulta histórica, sus estadísticas descriptivas y su visualización.
- **RN-CU01-14.** La finalidad de tratamiento no incluye diagnóstico, prescripción, elaboración de dietas ni predicción individual de la respuesta a alimentos.
- **RN-CU01-15.** Las consultas al catálogo nutricional no se vincularán con mediciones de glucosa ni se utilizarán para inferir consumo.
- **RN-CU01-16.** El sistema no debe solicitar datos clínicos o alimenticios que no sean necesarios para el registro.
- **RN-CU01-17.** Las contraseñas, los mecanismos de verificación y los datos sensibles no deben escribirse en logs de aplicación.
- **RN-CU01-18.** Los mensajes de error deben evitar revelar si una cuenta existe cuando esto facilite la enumeración de usuarios.
- **RN-CU01-19.** Las evidencias de aceptación y autorización deben conservar las versiones de los documentos aplicables.
- **RN-CU01-20.** Los textos finales de autorización y privacidad deben someterse a la revisión legal correspondiente antes de su publicación.

## 11. Requisitos funcionales

- **RF-CU01-01.** El sistema debe mostrar el formulario de registro.
- **RF-CU01-02.** Debe validar nombres, apellidos, correo y contraseña.
- **RF-CU01-03.** Debe verificar la unicidad del correo.
- **RF-CU01-04.** Debe solicitar la confirmación de contraseña.
- **RF-CU01-05.** Debe permitir la aceptación de términos y la constancia de información sobre privacidad.
- **RF-CU01-06.** Debe presentar la autorización de tratamiento de datos sensibles como opción separada.
- **RF-CU01-07.** Debe conservar evidencia de las aceptaciones y autorizaciones registradas.
- **RF-CU01-08.** Debe crear las cuentas nuevas en estado pendiente de verificación.
- **RF-CU01-09.** Debe generar y enviar el mecanismo de verificación de correo.
- **RF-CU01-10.** Debe validar la integridad, vigencia y uso único del mecanismo de verificación.
- **RF-CU01-11.** Debe activar la cuenta únicamente después de una verificación correcta.
- **RF-CU01-12.** Debe permitir solicitar el reenvío del enlace conforme a los límites establecidos.
- **RF-CU01-13.** Debe impedir que una cuenta sin autorización válida de datos sensibles utilice las funciones que requieren ese tratamiento.
- **RF-CU01-14.** Debe impedir la asignación de roles privilegiados a través del formulario público.
- **RF-CU01-15.** Debe presentar mensajes de validación comprensibles.
- **RF-CU01-16.** Debe evitar la exposición de datos internos en los mensajes de error.
- **RF-CU01-17.** Debe proteger los datos de registro durante la transmisión y el almacenamiento.
- **RF-CU01-18.** Debe evitar recopilar información de glucosa o alimentación en el formulario de registro.

## 12. Seguridad y privacidad

- Toda comunicación de registro y verificación debe utilizar HTTPS.
- Las contraseñas deben almacenarse mediante el hash establecido en las reglas del proyecto.
- Los mecanismos de verificación no deben aparecer en logs ni ser reutilizables.
- Deben aplicarse límites de solicitudes para prevenir abuso del registro y del reenvío de correos.
- La información de autorización debe protegerse frente a alteración o acceso no autorizado.
- Los datos de perfil no deben incluir por defecto información clínica.
- El registro debe informar al usuario sobre las finalidades reales del tratamiento.
- El diseño de privacidad y los textos finales deben revisarse antes de publicar la aplicación.

## 13. Criterios de aceptación

- **CA-CU01-01.** Un visitante puede abrir el formulario.
- **CA-CU01-02.** Los campos obligatorios se validan antes de crear la cuenta.
- **CA-CU01-03.** No se permiten cuentas duplicadas para un mismo correo.
- **CA-CU01-04.** Una cuenta creada queda pendiente hasta verificar el correo.
- **CA-CU01-05.** El mecanismo de verificación expira y solo puede usarse una vez.
- **CA-CU01-06.** El usuario recibe confirmación después de una verificación correcta.
- **CA-CU01-07.** El rol predeterminado es usuario.
- **CA-CU01-08.** La contraseña no se almacena en texto plano.
- **CA-CU01-09.** La aceptación general y la autorización para datos sensibles aparecen separadas.
- **CA-CU01-10.** Una autorización no concedida no queda registrada como otorgada.
- **CA-CU01-11.** Las funciones que requieren datos sensibles no procesan esos datos sin autorización válida.
- **CA-CU01-12.** El formulario no recopila mediciones de glucosa ni hábitos alimenticios.
- **CA-CU01-13.** La finalidad informada no incluye planes alimenticios ni correlaciones entre alimentos y mediciones.
- **CA-CU01-14.** Los errores de registro no exponen datos técnicos sensibles.
- **CA-CU01-15.** La evidencia de autorización conserva la versión del texto aceptado.

## 14. Fuera del alcance

- Inicio de sesión, gestionado por CU02.
- Gestión de perfil, gestionada por CU03.
- Registro de mediciones de glucosa.
- Registro de alimentos consumidos.
- Recomendaciones de alimentación.
- Diagnóstico o prescripción.
- Correlación entre consultas al catálogo y mediciones personales.
