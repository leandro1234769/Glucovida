# CU03. Gestionar perfil

## 1. Identificación

| Campo | Descripción |
|---|---|
| **ID** | CU03 |
| **Nombre** | Gestionar perfil |
| **Actor principal** | Usuario |
| **Actores secundarios** | Sistema de GlucoVida, servicio de correo electrónico |
| **Objetivo** | Permitir que el usuario consulte y actualice la información básica de su perfil y gestione determinados datos relacionados con su cuenta. |
| **Prioridad** | Alta |
| **Tipo** | Caso de uso principal |

## 2. Descripción

El usuario autenticado puede acceder a su perfil para consultar la información registrada, modificar sus datos personales permitidos y gestionar información relacionada con su cuenta.

El sistema valida cualquier modificación antes de almacenarla y aplica mecanismos adicionales de seguridad cuando el usuario intenta modificar información sensible, como el correo electrónico o la contraseña.

## 3. Precondiciones

- El usuario debe haber iniciado sesión.
- La sesión debe encontrarse vigente.
- La cuenta debe estar activa.
- El sistema debe encontrarse disponible.

## 4. Disparador

El usuario selecciona la opción **«Mi perfil»** desde el panel principal de GlucoVida.

## 5. Información administrable

### Datos personales

| Campo | ¿Puede modificarlo? |
|---|---|
| Nombres | Sí |
| Apellidos | Sí |

### Datos de acceso

| Campo | ¿Puede modificarlo? | Condición |
|---|---|---|
| Correo electrónico | Sí | Requiere nueva verificación |
| Contraseña | Sí | Requiere contraseña actual y validaciones de seguridad |

### Información de salud

Los datos de salud no serán administrados mediante CU03. Las mediciones de glucosa, registros alimentarios y demás información relacionada con la salud tendrán casos de uso independientes.

Esto permite separar los datos personales de los datos clínicos y facilita posteriormente el diseño de la base de datos y los controles de privacidad.

## 6. Flujo principal: consultar perfil

| Paso | Actor | Acción |
|---|---|---|
| 1 | Usuario | Selecciona «Mi perfil». |
| 2 | Sistema | Verifica que la sesión sea válida. |
| 3 | Sistema | Consulta la información básica asociada a la cuenta. |
| 4 | Sistema | Muestra los datos personales y de acceso permitidos. |
| 5 | Usuario | Consulta su información. |

## 7. Flujo principal: actualizar datos personales

| Paso | Actor | Acción |
|---|---|---|
| 1 | Usuario | Selecciona la opción para editar su perfil. |
| 2 | Sistema | Muestra los campos que pueden modificarse. |
| 3 | Usuario | Modifica sus nombres o apellidos. |
| 4 | Usuario | Envía los cambios. |
| 5 | Sistema | Valida los datos ingresados. |
| 6 | Sistema | Guarda los cambios. |
| 7 | Sistema | Confirma que la información fue actualizada correctamente. |

## 8. Flujo alternativo: cambiar correo electrónico

### FA01. Solicitud de cambio de correo

- El usuario selecciona la opción para modificar su correo.
- El sistema solicita el nuevo correo electrónico.
- El usuario ingresa el nuevo correo.
- El sistema verifica que tenga un formato válido.
- El sistema verifica que el nuevo correo no esté asociado a otra cuenta.
- El sistema solicita una confirmación adicional de seguridad.
- El sistema registra el nuevo correo como pendiente de verificación.
- El sistema envía un mensaje de verificación a la nueva dirección.
- El correo anterior continúa siendo el medio de acceso hasta completar la nueva verificación, según la política de seguridad definida.
- Una vez verificado el nuevo correo, el sistema actualiza el correo principal de la cuenta.

## 9. Flujo alternativo: cambiar contraseña

### FA02. Cambio de contraseña

- El usuario selecciona «Cambiar contraseña».
- El sistema solicita la contraseña actual.
- El usuario ingresa la contraseña actual.
- El sistema valida la contraseña mediante `bcrypt`.
- El usuario introduce la nueva contraseña y su confirmación.
- El sistema valida la política de seguridad.
- El sistema genera un nuevo hash utilizando `bcrypt`.
- El sistema actualiza la contraseña.
- El sistema confirma el cambio.
- El sistema puede invalidar las sesiones activas anteriores como medida de seguridad.

## 10. Flujos alternativos adicionales

### FA03. Datos inválidos

- El sistema identifica información incompleta o con formato incorrecto.
- El sistema indica los campos que deben corregirse.
- El usuario realiza las correcciones.
- El proceso continúa nuevamente con la validación.

### FA04. Correo electrónico ya utilizado

- El sistema determina que el nuevo correo pertenece a otra cuenta.
- El sistema rechaza el cambio.
- El usuario debe ingresar otra dirección.

### FA05. Contraseña actual incorrecta

- El sistema determina que la contraseña actual no coincide.
- El cambio de contraseña no se realiza.
- El sistema informa que las credenciales actuales no son válidas.

## 11. Flujos de excepción

### FE01. Error al actualizar el perfil

- Ocurre un error durante el almacenamiento.
- El sistema informa que no fue posible completar la actualización.
- Los datos anteriores permanecen sin modificaciones.

### FE02. Error al enviar verificación de correo

- El sistema no puede enviar el mensaje a la nueva dirección.
- El cambio permanece pendiente.
- El correo anterior continúa siendo válido hasta completar el proceso definido.

### FE03. Sesión expirada

- El usuario intenta actualizar información después de que su sesión haya expirado.
- El sistema rechaza la operación.
- El usuario es redirigido al inicio de sesión.
- No se realizan modificaciones.

## 12. Postcondiciones

### Si la actualización es exitosa:

- Los datos permitidos quedan actualizados.
- La información almacenada cumple las reglas de validación.
- Los cambios quedan asociados a la cuenta autenticada.

### Si se modifica el correo:

- El nuevo correo debe ser verificado antes de convertirse en el correo principal de la cuenta.

### Si se modifica la contraseña:

- La nueva contraseña queda almacenada mediante `bcrypt`.
- La contraseña anterior deja de ser válida.

### Si la operación falla:

- La información anterior permanece intacta.
- No se almacena información incompleta o inválida.

## 13. Reglas de negocio relacionadas

| Código | Regla |
|---|---|
| **RN18** | Solo un usuario autenticado puede gestionar su perfil. |
| **RN19** | Los nombres y apellidos pueden ser modificados por el usuario. |
| **RN20** | El correo electrónico debe ser único dentro del sistema. |
| **RN21** | Un correo electrónico nuevo debe verificarse antes de convertirse en el correo principal de la cuenta. |
| **RN22** | El cambio de contraseña requiere validar la contraseña actual. |
| **RN23** | Las nuevas contraseñas deben cumplir la política de seguridad definida para GlucoVida. |
| **RN24** | Las contraseñas nuevas deben almacenarse mediante `bcrypt`. |
| **RN25** | Los datos de salud no se modifican mediante el perfil básico, sino mediante los casos de uso correspondientes. |
| **RN26** | Una sesión expirada no puede utilizarse para modificar información del usuario. |

## 14. Requisitos funcionales relacionados

- **RF16:** El sistema debe permitir al usuario consultar su información de perfil.
- **RF17:** El sistema debe permitir modificar nombres y apellidos.
- **RF18:** El sistema debe permitir solicitar el cambio de correo electrónico.
- **RF19:** El sistema debe verificar el nuevo correo antes de establecerlo como correo principal.
- **RF20:** El sistema debe permitir cambiar la contraseña.
- **RF21:** El sistema debe solicitar la contraseña actual antes de permitir su modificación.
- **RF22:** El sistema debe validar toda información modificada antes de almacenarla.
- **RF23:** El sistema debe impedir modificaciones realizadas mediante sesiones expiradas.

## 15. Consideraciones de seguridad y privacidad

- El usuario solo puede modificar su propio perfil.
- El sistema no debe permitir que un usuario modifique su rol.
- El cambio de correo requiere una nueva verificación.
- El cambio de contraseña debe generar un nuevo hash.
- Las operaciones sensibles deben quedar registradas como eventos de seguridad cuando corresponda.
- La información de salud debe mantenerse separada conceptualmente de los datos básicos del perfil.
- El sistema debe aplicar controles de autorización en el backend y no confiar únicamente en las restricciones de la interfaz.