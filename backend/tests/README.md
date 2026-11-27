# Pruebas de registro de GlucoVida

Desde `backend/`, instala las dependencias con `python -m pip install ".[test]"`
en el entorno virtual. Usa una instancia de Redis exclusiva de pruebas en
`127.0.0.1:16379`. El test abre un servidor SMTP real sobre TLS en un puerto
local efimero y captura el mensaje sin entregarlo fuera del equipo.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://gv_app@127.0.0.1:55432/glucovida_test'
$env:TEST_REDIS_URL = 'redis://127.0.0.1:16379/15'
$env:DATABASE_URL = $env:TEST_DATABASE_URL
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m pytest -q tests
```

La prueba con transportes fija `terms-test-v1`, `privacy-test-v1` y `health-data-test-v1`,
30 minutos de vigencia, 5 solicitudes por IP en 60 segundos y 2 por correo
en 15 minutos. Registro y reenvio comparten estos limites. Los identificadores
de prueba corresponden al entorno local.

Para cargar la configuracion fuera de pytest, `RegistrationSettings` lee las
variables siguientes con prefijo `GLUCOVIDA_`. Usa valores distintos para las
dos claves secretas, con al menos 32 bytes aleatorios cada una.

| Configuracion | Variables sin prefijo |
|---|---|
| Entorno y activacion | `ENVIRONMENT`, `PUBLIC_REGISTRATION_ENABLED`, `PRODUCTION_RELEASE_APPROVED` |
| Origenes de frontend, lista JSON | `ALLOWED_ORIGINS` |
| Clave de firma CSRF y clave HMAC del limite | `CSRF_KEY`, `RATE_LIMIT_KEY` |
| Redis | `REDIS_URL` |
| SMTP y pagina HTTPS de verificacion | `SMTP_HOST`, `SMTP_PORT` (465 por defecto), `SMTP_STARTTLS` (activalo para 587), `SMTP_SENDER`, `VERIFICATION_PAGE` |
| Credenciales SMTP y CA privada, opcionales | `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_CA_FILE` |
| Versiones y vigencia del enlace | `TERMS_VERSION`, `PRIVACY_VERSION`, `HEALTH_DATA_VERSION`, `VERIFICATION_TTL_MINUTES` |
| Limites de registro y reenvio | `REGISTRATION_IP_REQUESTS`, `REGISTRATION_IP_WINDOW_SECONDS`, `REGISTRATION_EMAIL_REQUESTS`, `REGISTRATION_EMAIL_WINDOW_SECONDS` |

## Desarrollo local

El perfil de `.env.example` usa `glucovida_local` y Redis DB 14. La suite
usa `glucovida_test` y Redis DB 15. Para levantar el buzon SMTP local
desde `backend/`:

```powershell
$state = Join-Path $env:LOCALAPPDATA 'GlucoVida-SMTP-Local'
.venv\Scripts\python.exe tests/local_smtp.py --state-dir $state
```

Configura `GLUCOVIDA_SMTP_CA_FILE` con la ruta a `smtp-ca.pem` de esa
carpeta. El buzon `inbox` contiene los mensajes de prueba en formato EML.
Usa solo datos sinteticos y borra los mensajes cuando termines de probarlos.

## Activacion del registro publico

Copia `.env.example` a `.env` para desarrollo local. El registro se activa por
defecto en development y test, con sus documentos respectivos.

Aplica las migraciones en la base de destino y suministra `DATABASE_URL` y
las variables de la tabla anterior mediante la configuracion del despliegue.
Usa las versiones aprobadas de los textos y el remitente autorizado por el
proveedor SMTP. Deja `GLUCOVIDA_PUBLIC_REGISTRATION_ENABLED=false` hasta validar
Redis, Brevo y HTTPS en ese entorno. Tras la aprobacion juridica y operativa,
activa `GLUCOVIDA_PRODUCTION_RELEASE_APPROVED` y el registro publico, y
reinicia con `python -m uvicorn app.main:create_app --factory`.

Usa HTTPS para la API y un frontend del mismo sitio para que el navegador
envie la cookie `__Host-gv_csrf` con `SameSite=Strict`. La aplicacion utiliza
la IP de la conexion resuelta por el servidor ASGI. Si hay un proxy inverso,
configura Uvicorn para confiar solo en las IP de los proxies controlados.

## Integracion de la interfaz

1. Antes de enviar el formulario, llama a `GET /api/v1/auth/csrf` con
   `credentials: "include"`. Guarda el `csrf_token` de la respuesta.
2. Envia `POST /api/v1/auth/register` con JSON, credenciales incluidas y
   `X-CSRF-Token`. En `consent` envia `terms_accepted`,
   `privacy_acknowledged`, `health_data_authorized`, `terms_version`,
   `privacy_version` y `health_data_version`, de acuerdo
   con los textos que se mostraron a la persona.
3. Tras el `202`, muestra **Reenviar enlace**. Envia el correo que se uso
   para registrar la cuenta a `POST /api/v1/auth/email-verification/resend`
   con el mismo mecanismo CSRF. Ante `429`, respeta `Retry-After`.
4. En la pagina de verificacion, lee el token de `#token=...`, elimina el
   fragmento del historial y envia `{"token":"..."}` a
   `POST /api/v1/auth/email-verification/confirm` con CSRF. Un `204` confirma
   la activacion. Un `401` permite ofrecer un nuevo enlace.

El registro y el reenvio emiten la misma respuesta generica. El correo se
envia despues de confirmar la transaccion, como tarea local de la respuesta.
Si el envio falla o el proceso se interrumpe, la persona puede solicitar
otro enlace.


## Inicio de sesion en desarrollo y pruebas

Configura `GLUCOVIDA_JWT_PRIVATE_KEY_FILE` con la ruta a una clave privada RSA
PEM de al menos 2048 bits almacenada fuera de Git, y define
`GLUCOVIDA_JWT_ISSUER` y `GLUCOVIDA_JWT_AUDIENCE` para tu API.
`POST /api/v1/auth/login` devuelve un JWT Bearer de 15 minutos y coloca
el token de renovacion en la cookie segura `__Host-gv_refresh`.
Guarda el nuevo encabezado `X-CSRF-Token` para solicitudes posteriores.

Las rutas protegidas pueden usar `Depends(require_access_session)`. Esa
dependencia valida el JWT y aplica tanto las 24 horas de vigencia absoluta
como los 30 minutos de inactividad contra la sesion persistida. La ruta de
login se habilita solo en development y test con clave configurada.
