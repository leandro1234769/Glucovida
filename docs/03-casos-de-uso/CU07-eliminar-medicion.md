# CU07. Eliminar medición de glucosa

## 1. Información general

- **Código:** CU07
- **Nombre:** Eliminar medición de glucosa
- **Actor principal:** Usuario registrado y autenticado.
- **Objetivo:** Permitir que el usuario retire una medición propia de su historial, evitando eliminaciones accidentales, accesos no autorizados y alteraciones inconsistentes de la información.
- **Prioridad:** Alta.
- **Tipo:** Caso de uso funcional.
- **Relaciones:** CU04. Registrar medición de glucosa; CU05. Consultar mediciones; CU06. Editar medición de glucosa.

## 2. Descripción

El usuario consulta su historial, selecciona una medición y solicita eliminarla. El sistema verifica la propiedad del registro y presenta una ventana de confirmación con la fecha y hora de la medición, junto con las opciones «Cancelar» y «Eliminar».

Una vez confirmada la operación, el sistema realiza una **eliminación lógica**. El registro deja de estar disponible en las consultas ordinarias, pero permanece marcado como eliminado durante 30 días. Cumplido ese plazo, se programa su depuración definitiva, sujeta a la política de conservación y a las obligaciones aplicables.

El usuario no dispone de una opción para recuperar mediciones eliminadas desde la interfaz ordinaria.

## 3. Precondiciones

1. El usuario debe tener una cuenta activa.
2. El usuario debe contar con una sesión válida.
3. Debe existir la medición que desea eliminar.
4. La medición debe pertenecer al usuario autenticado.
5. La medición no debe estar ya eliminada.
6. El usuario debe tener permiso para ejecutar la operación.

## 4. Postcondiciones

**Éxito:**

- La medición queda marcada como eliminada.
- La medición deja de aparecer en el historial ordinario.
- La medición deja de incluirse en las estadísticas y gráficas actuales.
- El sistema registra la fecha de eliminación y los metadatos mínimos de auditoría necesarios.
- Se establece el vencimiento del periodo de retención de 30 días.
- El sistema confirma que la operación se completó.

**Fallo:**

- La medición conserva su estado anterior.
- No se confirma una eliminación que no se haya guardado.
- El sistema informa que la operación no pudo completarse.

## 5. Flujo principal

1. El usuario ingresa a la sección de historial de mediciones.
2. El sistema presenta sus registros conforme a los criterios de consulta definidos en CU05.
3. El usuario selecciona la medición que desea retirar.
4. El sistema verifica que el registro exista, se encuentre disponible y pertenezca al usuario autenticado.
5. El usuario selecciona la opción **Eliminar**.
6. El sistema presenta una ventana de confirmación con la fecha y hora de la medición y las opciones «Cancelar» y «Eliminar».
7. El usuario confirma la eliminación.
8. El sistema vuelve a validar la autorización y el estado del registro.
9. El sistema marca la medición como eliminada y registra la fecha de eliminación.
10. El sistema establece el vencimiento de la retención de 30 días.
11. El sistema registra los metadatos de auditoría correspondientes.
12. El sistema excluye la medición de las consultas ordinarias, estadísticas y gráficas actuales.
13. El sistema informa que la operación se completó correctamente.

## 6. Flujos alternativos

### A1. El usuario cancela la eliminación

1. El usuario selecciona «Cancelar» en la ventana de confirmación.
2. El sistema cierra la ventana.
3. La medición permanece disponible y sin modificaciones.

### A2. El registro ya fue eliminado

1. El sistema detecta que la medición ya se encuentra marcada como eliminada o no está disponible.
2. El sistema informa que el registro no se encuentra disponible para esa operación.
3. No realiza una segunda eliminación ni modifica otros registros.

### A3. El usuario intenta eliminar una medición de otra persona

1. El sistema comprueba que la medición no pertenece al usuario autenticado.
2. El sistema rechaza la operación.
3. No revela información del propietario ni detalles innecesarios del registro.

### A4. La medición cambia durante la solicitud

1. El sistema detecta que el estado del registro cambió antes de confirmar la eliminación.
2. El sistema vuelve a verificar el estado y los permisos.
3. Si el registro ya no se encuentra disponible, rechaza la operación e informa el resultado.

## 7. Excepciones

- **E1. Sesión expirada:** el sistema solicita autenticarse nuevamente.
- **E2. Acceso no autorizado:** la operación es rechazada.
- **E3. Error de base de datos:** el sistema informa que no pudo completar la operación y mantiene el estado anterior.
- **E4. Error de conexión:** el sistema no confirma la eliminación hasta verificar el resultado.
- **E5. Conflicto de estado:** el sistema verifica nuevamente el registro para evitar operaciones inconsistentes.
- **E6. Error de auditoría:** la eliminación no debe confirmarse si no es posible registrar los metadatos obligatorios de forma consistente.
- **E7. Error del proceso de depuración:** el sistema registra el fallo técnico, permite reintentar la tarea y evita afirmar que la eliminación definitiva se completó sin comprobarlo.

## 8. Política de eliminación y conservación

La política funcional inicial queda definida de la siguiente manera:

- **Tipo de eliminación:** lógica.
- **Disponibilidad ordinaria:** el registro se excluye de las consultas del usuario después de la eliminación.
- **Recuperación por parte del usuario:** no disponible desde la interfaz ordinaria.
- **Periodo de retención:** 30 días contados desde la fecha de eliminación.
- **Después de la retención:** el sistema programa la depuración definitiva de la medición, de acuerdo con la política de conservación aplicable.
- **Auditoría:** se conservan los metadatos mínimos necesarios para acreditar la operación durante el periodo establecido en la política correspondiente.
- **Copias de seguridad:** su tratamiento debe documentarse para evitar que la información eliminada reaparezca en el sistema después de una restauración.

La eliminación lógica no equivale a la eliminación física inmediata. El sistema debe distinguir entre el estado de eliminación, el vencimiento del plazo de retención y la depuración definitiva.

## 9. Reglas de negocio

- **RN-CU07-01. Propiedad del registro:** solo el usuario propietario puede eliminar la medición.
- **RN-CU07-02. Confirmación explícita:** el sistema solicita confirmación antes de ejecutar la eliminación.
- **RN-CU07-03. Autorización en el servidor:** los permisos se verifican en el backend en cada solicitud.
- **RN-CU07-04. Alcance individual:** eliminar una medición no afecta las demás mediciones del usuario.
- **RN-CU07-05. Eliminación lógica:** la operación marca el registro como eliminado, sin borrarlo físicamente de inmediato.
- **RN-CU07-06. Exclusión del historial:** las mediciones eliminadas no aparecen en las consultas ordinarias.
- **RN-CU07-07. Consistencia de estadísticas:** las mediciones eliminadas no se incluyen en las estadísticas ni en las gráficas actuales.
- **RN-CU07-08. Sin recuperación ordinaria:** el usuario no dispone de una función para restaurar la medición eliminada.
- **RN-CU07-09. Retención definida:** el periodo inicial de retención es de 30 días desde la eliminación.
- **RN-CU07-10. Depuración definitiva:** al finalizar el periodo, el sistema debe ejecutar o programar la eliminación definitiva, respetando la política de conservación aplicable.
- **RN-CU07-11. Auditoría:** el sistema registra los metadatos mínimos necesarios para identificar la operación y su resultado.
- **RN-CU07-12. Protección de auditoría:** la información de auditoría no debe quedar disponible en las consultas ordinarias del usuario.
- **RN-CU07-13. Consistencia de la operación:** el cambio de estado, la auditoría y la exclusión del registro deben gestionarse de manera consistente.
- **RN-CU07-14. Sin efectos clínicos automáticos:** eliminar una medición no genera diagnósticos ni recomendaciones médicas.

## 10. Requisitos funcionales relacionados

- **RF-CU07-01:** el sistema debe permitir seleccionar una medición propia para eliminarla.
- **RF-CU07-02:** el sistema debe solicitar confirmación mediante una ventana con las opciones «Cancelar» y «Eliminar».
- **RF-CU07-03:** el sistema debe impedir la eliminación de mediciones pertenecientes a otros usuarios.
- **RF-CU07-04:** el sistema debe marcar el registro como eliminado sin borrarlo físicamente de inmediato.
- **RF-CU07-05:** el sistema debe retirar la medición de las consultas ordinarias.
- **RF-CU07-06:** el sistema debe excluir la medición de las estadísticas y gráficas actuales.
- **RF-CU07-07:** el sistema debe registrar la fecha de eliminación y los metadatos de auditoría definidos.
- **RF-CU07-08:** el sistema debe aplicar un periodo de retención de 30 días.
- **RF-CU07-09:** el sistema debe ejecutar o programar la depuración definitiva al vencimiento del periodo, conforme a la política aplicable.
- **RF-CU07-10:** el sistema debe informar si la operación se completó o falló.
- **RF-CU07-11:** el sistema debe impedir la recuperación desde la interfaz ordinaria del usuario.
- **RF-CU07-12:** el sistema debe contemplar el tratamiento de las copias de seguridad y de los procesos de restauración.

## 11. Seguridad y protección de datos

- Utilizar HTTPS para las comunicaciones.
- Verificar en el backend que el usuario sea propietario del registro.
- No confiar exclusivamente en que el botón de eliminación esté oculto en la interfaz.
- Evitar revelar datos de otros usuarios durante los intentos no autorizados.
- Restringir el acceso a los registros eliminados y a sus metadatos de auditoría.
- Garantizar que los registros eliminados no se incluyan en las consultas ordinarias, exportaciones, estadísticas ni gráficas.
- Ejecutar las operaciones de manera consistente para evitar estados parciales.
- Proteger las tareas de depuración definitiva y registrar su resultado técnico.
- Definir el tratamiento de copias de seguridad para que la restauración no contradiga la política de eliminación.
- Aplicar las medidas de protección contra CSRF que correspondan al esquema de autenticación mediante cookies.

## 12. Criterios de aceptación

1. El usuario puede solicitar la eliminación de una medición propia.
2. El sistema muestra una ventana de confirmación con la fecha y hora de la medición.
3. Si el usuario cancela, la medición permanece disponible.
4. Un usuario no puede eliminar mediciones de terceros, aunque conozca su identificador.
5. Una eliminación exitosa marca el registro como eliminado y lo retira del historial ordinario.
6. Las estadísticas y gráficas actuales dejan de incluir la medición eliminada.
7. La eliminación no afecta otros registros del usuario.
8. La operación registra los metadatos de auditoría correspondientes.
9. El usuario no dispone de una función ordinaria para recuperar el registro.
10. El registro permanece sujeto al periodo de retención de 30 días.
11. Al finalizar la retención, el sistema programa o ejecuta la depuración definitiva conforme a la política establecida.
12. Un error no produce una confirmación falsa de eliminación.
13. Los registros eliminados no reaparecen en consultas ordinarias tras una actualización del historial.
14. El tratamiento de las copias de seguridad está contemplado en la política de eliminación.
15. La eliminación y conservación de los datos se ajustan a las reglas de protección de datos aplicables.
