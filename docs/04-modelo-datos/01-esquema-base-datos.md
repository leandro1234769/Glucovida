# GlucoVida | Diseño físico de la base de datos PostgreSQL

**Documento:** Especificación técnica del modelo físico de datos.  
**Módulo:** Base de datos y autenticación.  
**Versión:** 1.0  
**Estado:** Propuesta técnica para revisión y posterior implementación.  
**Motor:** PostgreSQL 18.  
**Backend:** Python + FastAPI.  
**ORM:** SQLAlchemy 2.x.  
**Migraciones:** Alembic.

---

# 1. ESQUEMA TÉCNICO DE TABLAS

## 1.1. Criterios generales del diseño

El modelo se construye con los siguientes principios:

1. **Integridad referencial:** las relaciones entre usuarios, sesiones y tokens estarán protegidas mediante claves foráneas.
2. **Consistencia:** las restricciones `NOT NULL`, `UNIQUE` y `CHECK` impedirán registrar estados inválidos.
3. **Trazabilidad:** los eventos de autenticación y seguridad quedarán registrados sin almacenar credenciales ni secretos.
4. **Revocación efectiva:** el servidor podrá comprobar el estado de una sesión utilizando su identificador y la versión de autenticación vigente.
5. **Minimización de datos:** únicamente se almacenará la información necesaria para cada proceso.
6. **Separación de responsabilidades:** los contadores temporales de Rate Limiting se mantendrán en Redis, mientras PostgreSQL conservará los datos persistentes.
7. **Eliminación controlada:** las relaciones entre entidades aplicarán políticas de eliminación adecuadas para preservar la integridad y la trazabilidad.

Se utilizarán identificadores `UUID` y marcas temporales `TIMESTAMP WITH TIME ZONE` (`TIMESTAMPTZ`).

PostgreSQL almacena los valores `TIMESTAMPTZ` internamente como instantes UTC y los presenta según la zona horaria configurada para la conexión. No conserva por sí mismo la zona horaria original enviada por el cliente. Por eso, las fechas del backend deberán manejarse en UTC y convertirse a la zona local al presentarse en la aplicación.

## 1.2. Entidades principales

| Tabla | Responsabilidad |
|---|---|
| `users` | Identidad, credenciales, estado de cuenta y versión de autenticación. |
| `auth_sessions` | Sesiones autenticadas, actividad, expiración y revocación. |
| `auth_refresh_tokens` | Hashes de Refresh Tokens, rotación, consumo y revocación. |
| `password_recovery_tokens` | Solicitudes y tokens de recuperación de contraseña. |
| `email_verification_tokens` | Tokens de verificación y activación de cuentas. |
| `audit_events` | Registro de eventos de seguridad y autenticación. |

## 1.3. Relaciones entre tablas

La estructura relacional principal será:

```text
                         USERS
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
       AUTH_SESSIONS  PASSWORD_      EMAIL_
             |        RECOVERY_     VERIFICATION_
             |        TOKENS        TOKENS
             |
             v
      AUTH_REFRESH_TOKENS


      AUDIT_EVENTS
        |       |
        +-------+
        Referencias opcionales a USERS
        y AUTH_SESSIONS
```

Cardinalidades:

- Un usuario puede tener muchas sesiones.
- Una sesión pertenece a un único usuario.
- Una sesión puede tener múltiples Refresh Tokens históricos debido a la rotación.
- Un usuario puede tener múltiples tokens históricos de recuperación.
- Un usuario puede tener múltiples tokens históricos de verificación.
- Un evento de auditoría puede estar relacionado con un usuario, una sesión o ambos. También puede existir sin usuario identificado, por ejemplo, ante un intento de inicio de sesión con un correo no registrado.

## 1.4. Tabla `users`

### Propósito

Almacena la identidad y la información necesaria para autenticar y administrar las cuentas de GlucoVida.

Contiene la versión global de autenticación `auth_version`, que permite invalidar todos los tokens anteriores después de un cambio o recuperación de contraseña.

También mantiene el estado de los intentos fallidos consecutivos de inicio de sesión, de forma persistente.

### SQL de referencia

```sql
CREATE TABLE glucovida.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    names VARCHAR(80) NOT NULL,
    surnames VARCHAR(100) NOT NULL,

    email VARCHAR(254) NOT NULL,

    password_hash VARCHAR(255) NOT NULL,

    account_status VARCHAR(24) NOT NULL
        DEFAULT 'pending_verification',

    email_verified_at TIMESTAMPTZ,

    auth_version INTEGER NOT NULL DEFAULT 1,

    password_changed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    failed_login_attempts SMALLINT NOT NULL DEFAULT 0,

    login_locked_until TIMESTAMPTZ,

    last_login_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_users_names
        CHECK (length(btrim(names)) > 0),

    CONSTRAINT ck_users_surnames
        CHECK (length(btrim(surnames)) > 0),

    CONSTRAINT ck_users_email
        CHECK (
            email = lower(email)
            AND email = btrim(email)
            AND length(email) > 0
        ),

    CONSTRAINT ck_users_password_hash
        CHECK (length(password_hash) > 0),

    CONSTRAINT ck_users_account_status
        CHECK (
            account_status IN (
                'pending_verification',
                'active',
                'suspended',
                'disabled'
            )
        ),

    CONSTRAINT ck_users_active_verified
        CHECK (
            account_status <> 'active'
            OR email_verified_at IS NOT NULL
        ),

    CONSTRAINT ck_users_auth_version
        CHECK (auth_version >= 1),

    CONSTRAINT ck_users_failed_attempts
        CHECK (failed_login_attempts BETWEEN 0 AND 5),

    CONSTRAINT ck_users_login_lock
        CHECK (
            login_locked_until IS NULL
            OR failed_login_attempts = 5
        )
);
```

### Consideraciones

- El correo se almacenará normalizado en minúsculas. La restricción única se aplicará sobre el valor normalizado.
- `password_hash` almacenará el hash bcrypt con costo 12, conforme a la decisión funcional existente. Se conservará longitud suficiente para facilitar una eventual migración a otro algoritmo de hash.
- `auth_version` comenzará en 1 y aumentará en los eventos que requieran invalidación global.
- `failed_login_attempts` representa los fallos consecutivos de autenticación.
- `login_locked_until` determina hasta cuándo se mantiene el bloqueo de 15 minutos.
- El estado `pending_verification` impide autenticar una cuenta que todavía no ha verificado su correo.
- Una cuenta suspendida o deshabilitada no podrá iniciar sesión, aunque la contraseña sea correcta.

El backend deberá actualizar `failed_login_attempts` y `login_locked_until` de forma atómica para evitar inconsistencias cuando lleguen intentos concurrentes.

## 1.5. Tabla `auth_sessions`

### Propósito

Representa cada sesión autenticada de un usuario.

Cada sesión tiene un identificador propio (`id`), que se incorpora como `sid` en el Access Token JWT.

La tabla permite validar si una sesión continúa vigente, si fue revocada, si ha superado el tiempo de inactividad o si alcanzó su expiración absoluta.

### SQL de referencia

```sql
CREATE TABLE glucovida.auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    auth_version_at_creation INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    absolute_expires_at TIMESTAMPTZ
        GENERATED ALWAYS AS (
            created_at + INTERVAL '24 hours'
        ) STORED,

    ip_address INET,

    user_agent VARCHAR(512),

    revoked_at TIMESTAMPTZ,

    revoke_reason VARCHAR(32),

    CONSTRAINT fk_auth_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_auth_sessions_version
        CHECK (auth_version_at_creation >= 1),

    CONSTRAINT ck_auth_sessions_activity
        CHECK (
            last_activity_at >= created_at
            AND last_activity_at <= absolute_expires_at
        ),

    CONSTRAINT ck_auth_sessions_revoked
        CHECK (
            (
                revoked_at IS NULL
                AND revoke_reason IS NULL
            )
            OR
            (
                revoked_at IS NOT NULL
                AND revoke_reason IS NOT NULL
            )
        ),

    CONSTRAINT ck_auth_sessions_revoke_reason
        CHECK (
            revoke_reason IS NULL
            OR revoke_reason IN (
                'logout',
                'password_change',
                'password_recovery',
                'refresh_reuse',
                'admin_action',
                'security_policy',
                'account_disabled'
            )
        ),

    CONSTRAINT ck_auth_sessions_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= created_at
        )
);
```

### Consideraciones

**Expiración absoluta de 24 horas**

`absolute_expires_at` es una columna generada por PostgreSQL. Su valor se calcula a partir de `created_at`, por lo que no podrá extenderse accidentalmente durante una renovación de tokens.

**Inactividad de 30 minutos**

No se necesita almacenar una columna `idle_timeout` en cada sesión, porque el límite es una política global aprobada para GlucoVida.

La validación se efectuará utilizando:

```sql
last_activity_at > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
```

Si no se cumple la condición, la sesión se considera inactiva y no debe autorizar nuevas solicitudes.

**Información del dispositivo**

- `ip_address` utilizará el tipo nativo `INET`, compatible con IPv4 e IPv6.
- `user_agent` almacenará una descripción limitada del navegador o cliente, con un máximo de 512 caracteres.

Estos datos son auxiliares para auditoría y detección de actividad sospechosa. No se utilizarán como prueba de identidad. Su acceso y retención deberán limitarse por razones de privacidad.

**Motivos de revocación**

Se conservarán códigos controlados para identificar por qué una sesión dejó de estar activa.

La revocación ordinaria afectará únicamente a la sesión actual. El cambio y la recuperación de contraseña revocarán todas las sesiones activas del usuario.

## 1.6. Tabla `auth_refresh_tokens`

### Propósito

Almacena los registros históricos de los Refresh Tokens emitidos durante el ciclo de vida de una sesión.

Por seguridad, no se guardará el valor original del token, sino su hash SHA-256.

Cada renovación consume el token anterior y genera un sucesor. El historial permite identificar reutilizaciones y revocar las credenciales de una sesión comprometida.

### SQL de referencia

```sql
CREATE TABLE glucovida.auth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    session_id UUID NOT NULL,

    token_hash BYTEA NOT NULL,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ NOT NULL,

    consumed_at TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    revoke_reason VARCHAR(32),

    replaced_by_token_id UUID,

    CONSTRAINT fk_refresh_tokens_session
        FOREIGN KEY (session_id)
        REFERENCES glucovida.auth_sessions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_refresh_tokens_successor
        FOREIGN KEY (replaced_by_token_id)
        REFERENCES glucovida.auth_refresh_tokens(id)
        ON DELETE SET NULL,

    CONSTRAINT ck_refresh_token_hash_length
        CHECK (octet_length(token_hash) = 32),

    CONSTRAINT ck_refresh_token_expiration
        CHECK (expires_at > issued_at),

    CONSTRAINT ck_refresh_token_state
        CHECK (
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
        ),

    CONSTRAINT ck_refresh_token_consumed_at
        CHECK (
            consumed_at IS NULL
            OR consumed_at >= issued_at
        ),

    CONSTRAINT ck_refresh_token_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= issued_at
        ),

    CONSTRAINT ck_refresh_token_revocation_reason
        CHECK (
            (
                revoked_at IS NULL
                AND revoke_reason IS NULL
            )
            OR
            (
                revoked_at IS NOT NULL
                AND revoke_reason IS NOT NULL
            )
        ),

    CONSTRAINT ck_refresh_token_replacement
        CHECK (
            replaced_by_token_id IS NULL
            OR (
                replaced_by_token_id <> id
                AND consumed_at IS NOT NULL
                AND revoked_at IS NULL
            )
        )
);
```

### Consideraciones

**Almacenamiento seguro**

El Refresh Token se generará con un generador criptográfico seguro y contendrá al menos 256 bits de aleatoriedad.

Su valor original se enviará al navegador mediante la cookie protegida. El backend calculará SHA-256 y almacenará únicamente los 32 bytes del resultado.

No se utilizará bcrypt para estos tokens, porque no son contraseñas elegidas por usuarios y cuentan con alta entropía aleatoria.

**Estados del token**

| Estado | `consumed_at` | `revoked_at` | Uso |
|---|---|---|---|
| Disponible | NULL | NULL | Puede intentar una renovación si no expiró y su sesión sigue activa. |
| Consumido | Fecha | NULL | Ya fue utilizado durante una renovación. |
| Revocado | NULL | Fecha | Se invalidó anticipadamente. |

Un token expirado también debe rechazarse aunque sus dos campos de estado estén en `NULL`.

Los tokens consumidos se conservarán durante el periodo de retención definido para detectar intentos de reutilización.

**Rotación**

La relación `replaced_by_token_id` apunta al token sucesor.

Durante la renovación:

1. Se bloquea la sesión y el registro del token anterior.
2. Se verifica su estado.
3. Se marca el token anterior como consumido.
4. Se crea su sucesor.
5. Se registra la relación de reemplazo.
6. Se confirma la transacción.

Se impondrá una restricción única parcial para que no exista más de un Refresh Token disponible por sesión.

## 1.7. Tabla `password_recovery_tokens`

### Propósito

Almacena los tokens utilizados para recuperar la contraseña de un usuario.

Los tokens serán aleatorios, de un solo uso y almacenados mediante SHA-256.

La vigencia de 30 minutos se aplicará desde la fecha de emisión.

### SQL de referencia

```sql
CREATE TABLE glucovida.password_recovery_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    token_hash BYTEA NOT NULL,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ
        GENERATED ALWAYS AS (
            issued_at + INTERVAL '30 minutes'
        ) STORED,

    consumed_at TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    CONSTRAINT fk_recovery_tokens_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_recovery_token_hash_length
        CHECK (octet_length(token_hash) = 32),

    CONSTRAINT ck_recovery_token_state
        CHECK (
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
        ),

    CONSTRAINT ck_recovery_token_consumed_at
        CHECK (
            consumed_at IS NULL
            OR consumed_at >= issued_at
        ),

    CONSTRAINT ck_recovery_token_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= issued_at
        )
);
```

### Consideraciones

- La vigencia se calcula automáticamente a partir de `issued_at`.
- No es posible extender la vigencia a más de 30 minutos modificando `expires_at`.
- Un token utilizado debe marcarse con `consumed_at`.
- Los demás tokens de recuperación pendientes se invalidarán al completar una recuperación exitosa.
- La actualización de la contraseña, el incremento de `auth_version`, la revocación de sesiones y el consumo del token deben ejecutarse de forma transaccional.

El límite de tres solicitudes por hora y los límites adicionales por IP no se calcularán mediante consultas permanentes a esta tabla. Se aplicarán mediante los contadores temporales de Redis establecidos en el componente de Rate Limiting.

## 1.8. Tabla `email_verification_tokens`

### Propósito

Almacena los tokens enviados por correo para verificar la dirección electrónica del usuario y completar el proceso de activación de cuenta.

### SQL de referencia

```sql
CREATE TABLE glucovida.email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    token_hash BYTEA NOT NULL,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ NOT NULL,

    consumed_at TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    CONSTRAINT fk_email_verification_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_email_verification_hash_length
        CHECK (octet_length(token_hash) = 32),

    CONSTRAINT ck_email_verification_expiration
        CHECK (expires_at > issued_at),

    CONSTRAINT ck_email_verification_state
        CHECK (
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
        ),

    CONSTRAINT ck_email_verification_consumed_at
        CHECK (
            consumed_at IS NULL
            OR consumed_at >= issued_at
        ),

    CONSTRAINT ck_email_verification_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= issued_at
        )
);
```

### Consideraciones

El plazo exacto de verificación del correo no se encuentra fijado en los acuerdos funcionales disponibles.

Por esta razón, `expires_at` será calculado por la aplicación al crear el token, según una política que deberá aprobarse antes de implementar CU01. No se debe inventar una duración y presentarla como decisión ya confirmada.

El sistema permitirá conservar el historial de tokens anteriores y mantener únicamente uno disponible por usuario.

Cuando se emita un nuevo token de verificación, la aplicación deberá revocar los tokens anteriores que todavía estén pendientes.

## 1.9. Tabla `audit_events`

### Propósito

Almacena los eventos relevantes para la seguridad y trazabilidad del sistema.

Debe permitir investigar operaciones como:

- Inicio de sesión exitoso.
- Intentos fallidos de autenticación.
- Bloqueos temporales.
- Cierre de sesión.
- Revocación de una sesión.
- Revocación global.
- Cambio y recuperación de contraseña.
- Renovación de tokens.
- Detección de reutilización de Refresh Tokens.
- Verificación del correo electrónico.

### SQL de referencia

```sql
CREATE TABLE glucovida.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID,

    session_id UUID,

    event_type VARCHAR(64) NOT NULL,

    outcome VARCHAR(20) NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    ip_address INET,

    user_agent VARCHAR(512),

    request_id UUID,

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_audit_session
        FOREIGN KEY (session_id)
        REFERENCES glucovida.auth_sessions(id)
        ON DELETE SET NULL,

    CONSTRAINT ck_audit_event_type
        CHECK (
            event_type IN (
                'account_registered',
                'email_verification_completed',
                'login_succeeded',
                'login_failed',
                'login_locked',
                'session_created',
                'logout',
                'session_revoked',
                'sessions_revoked_all',
                'refresh_rotated',
                'refresh_reuse_detected',
                'password_changed',
                'password_recovery_requested',
                'password_recovery_completed',
                'account_suspended',
                'account_disabled'
            )
        ),

    CONSTRAINT ck_audit_outcome
        CHECK (
            outcome IN (
                'success',
                'failure',
                'blocked',
                'security_event'
            )
        ),

    CONSTRAINT ck_audit_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);
```

### Consideraciones

**No se almacenarán datos secretos.**

Queda prohibido incluir en `metadata`:

- Contraseñas.
- Hashes de contraseñas.
- Access Tokens.
- Refresh Tokens.
- Tokens de recuperación.
- Tokens de verificación completos.
- Cookies de autenticación.
- Claves privadas o secretos criptográficos.

El campo `metadata` se utilizará exclusivamente para información contextual permitida y validada por la aplicación. No debe convertirse en un repositorio arbitrario de solicitudes HTTP.

**Relaciones opcionales**

`user_id` y `session_id` pueden ser nulos. Esto es necesario para registrar intentos de autenticación de cuentas inexistentes y para conservar eventos históricos cuando se eliminen las referencias a usuarios o sesiones.

**Inmutabilidad**

La tabla deberá tratarse como un registro de solo adición. El rol de ejecución de la aplicación no deberá tener permisos ordinarios de `UPDATE` o `DELETE` sobre sus registros.

La retención de logs y eventos deberá definirse de acuerdo con la política de privacidad, seguridad y conservación de información de GlucoVida.

---

# 2. ÍNDICES Y OPTIMIZACIÓN DE CONSULTAS

## 2.1. Objetivo

Los índices se diseñan para acelerar las consultas que se ejecutarán con mayor frecuencia:

- Búsqueda de usuarios por correo electrónico.
- Validación de una sesión a partir de `sid`.
- Verificación de la versión de autenticación `av`.
- Búsqueda del Refresh Token por su hash.
- Invalidación de tokens asociados a una sesión.
- Búsqueda de tokens de recuperación y verificación.
- Revocación de sesiones de un usuario.
- Consulta de auditoría por usuario, sesión o tipo de evento.

No se recomienda crear índices indiscriminadamente. Cada índice consume almacenamiento y genera trabajo adicional durante las operaciones de inserción, actualización y eliminación.

## 2.2. Índices propuestos

### Tabla `users`

```sql
-- Identificador único por correo normalizado.
-- La restricción UNIQUE de email también crea un índice.

CREATE INDEX idx_users_login_locked_until
ON glucovida.users (login_locked_until)
WHERE login_locked_until IS NOT NULL;

CREATE INDEX idx_users_account_status
ON glucovida.users (account_status);
```

Justificación:

- La restricción `UNIQUE(email)` permite localizar rápidamente una cuenta durante el login.
- `login_locked_until` puede utilizarse para consultas de administración y supervisión de bloqueos.
- `account_status` facilita la consulta de cuentas activas, suspendidas o pendientes cuando se requiera.

### Tabla `auth_sessions`

```sql
-- Consultar y revocar sesiones de un usuario.
CREATE INDEX idx_auth_sessions_user_revoked
ON glucovida.auth_sessions (user_id, revoked_at);

-- Encontrar sesiones que han superado su expiración absoluta.
CREATE INDEX idx_auth_sessions_active_absolute_expiry
ON glucovida.auth_sessions (absolute_expires_at)
WHERE revoked_at IS NULL;

-- Localizar sesiones inactivas durante procesos de mantenimiento.
CREATE INDEX idx_auth_sessions_active_last_activity
ON glucovida.auth_sessions (last_activity_at)
WHERE revoked_at IS NULL;
```

Justificación:

- La clave primaria `id` permite resolver las consultas de sesión por `sid`.
- El índice compuesto por `user_id` y `revoked_at` ayuda a buscar y revocar las sesiones activas de un usuario.
- Los índices parciales ayudan a localizar sesiones pendientes de expiración o limpieza.

### Tabla `auth_refresh_tokens`

```sql
-- Búsqueda exacta del hash del token.
CREATE UNIQUE INDEX uq_auth_refresh_tokens_hash
ON glucovida.auth_refresh_tokens (token_hash);

-- Consultar el historial de tokens de una sesión.
CREATE INDEX idx_auth_refresh_tokens_session_issued
ON glucovida.auth_refresh_tokens (session_id, issued_at DESC);

-- Garantizar un único Refresh Token disponible por sesión.
CREATE UNIQUE INDEX uq_auth_refresh_one_active_per_session
ON glucovida.auth_refresh_tokens (session_id)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;

-- Consultas de mantenimiento de tokens todavía disponibles.
CREATE INDEX idx_auth_refresh_tokens_active_expiry
ON glucovida.auth_refresh_tokens (expires_at)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;

-- Evitar que dos registros apunten al mismo sucesor.
CREATE UNIQUE INDEX uq_auth_refresh_replaced_by
ON glucovida.auth_refresh_tokens (replaced_by_token_id)
WHERE replaced_by_token_id IS NOT NULL;
```

Justificación:

El índice único sobre `token_hash` permite obtener el registro exacto a partir del hash recibido desde la cookie.

El índice parcial garantiza que una sesión no tenga dos Refresh Tokens disponibles simultáneamente. Esta restricción complementa el bloqueo transaccional aplicado durante la rotación.

### Tabla `password_recovery_tokens`

```sql
CREATE UNIQUE INDEX uq_password_recovery_token_hash
ON glucovida.password_recovery_tokens (token_hash);

CREATE INDEX idx_password_recovery_user_issued
ON glucovida.password_recovery_tokens (user_id, issued_at DESC);

CREATE UNIQUE INDEX uq_password_recovery_one_active_per_user
ON glucovida.password_recovery_tokens (user_id)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;
```

Justificación:

- El índice único busca el token por su hash.
- El índice por usuario permite consultar el historial e invalidar tokens anteriores.
- El índice parcial evita mantener más de un token de recuperación pendiente por usuario.

Un token expirado pero todavía no marcado como consumido o revocado seguirá perteneciendo al conjunto parcial. Antes de crear uno nuevo, la aplicación deberá revocar los registros anteriores que ya no deban estar disponibles.

### Tabla `email_verification_tokens`

```sql
CREATE UNIQUE INDEX uq_email_verification_token_hash
ON glucovida.email_verification_tokens (token_hash);

CREATE INDEX idx_email_verification_user_issued
ON glucovida.email_verification_tokens (user_id, issued_at DESC);

CREATE UNIQUE INDEX uq_email_verification_one_active_per_user
ON glucovida.email_verification_tokens (user_id)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;
```

### Tabla `audit_events`

```sql
CREATE INDEX idx_audit_events_user_time
ON glucovida.audit_events (user_id, occurred_at DESC)
WHERE user_id IS NOT NULL;

CREATE INDEX idx_audit_events_session_time
ON glucovida.audit_events (session_id, occurred_at DESC)
WHERE session_id IS NOT NULL;

CREATE INDEX idx_audit_events_type_time
ON glucovida.audit_events (event_type, occurred_at DESC);

CREATE INDEX idx_audit_events_occurred_at
ON glucovida.audit_events (occurred_at DESC);
```

Justificación:

Estos índices permiten consultar eventos recientes de un usuario, los eventos de una sesión específica, los eventos de seguridad de un tipo determinado y los registros que deben revisarse por antigüedad.

## 2.3. Consulta crítica: validación de sesión por `sid` y `av`

Este es uno de los procesos más importantes de la arquitectura.

El backend deberá verificar:

1. Que el `sid` del JWT identifique una sesión existente.
2. Que la sesión pertenezca al `sub` del token.
3. Que `av` coincida con la versión almacenada en la sesión.
4. Que `av` coincida con `users.auth_version`.
5. Que el usuario esté activo.
6. Que la sesión no haya sido revocada.
7. Que no hayan transcurrido 30 minutos de inactividad.
8. Que no se hayan cumplido las 24 horas de duración absoluta.

Consulta SQL propuesta:

```sql
SELECT
    s.id,
    s.user_id,
    s.auth_version_at_creation,
    s.created_at,
    s.last_activity_at,
    s.absolute_expires_at
FROM glucovida.auth_sessions AS s
INNER JOIN glucovida.users AS u
    ON u.id = s.user_id
WHERE
    s.id = :sid
    AND s.user_id = :sub
    AND s.auth_version_at_creation = :av
    AND u.auth_version = :av
    AND u.account_status = 'active'
    AND s.revoked_at IS NULL
    AND s.absolute_expires_at > CURRENT_TIMESTAMP
    AND s.last_activity_at >
        CURRENT_TIMESTAMP - INTERVAL '30 minutes';
```

Si la consulta no devuelve un registro, la solicitud protegida deberá rechazarse con `401 Unauthorized`.

### ¿Necesitamos crear un índice `(id, auth_version_at_creation)`?

No. La columna `id` ya es clave primaria y tiene un índice único B-tree.

La consulta localiza una sola fila mediante `sid`, y luego comprueba el valor de `auth_version_at_creation`. Crear otro índice compuesto con `id` y `auth_version_at_creation` sería redundante en este patrón de acceso.

La búsqueda de `users` también utiliza su clave primaria. Esta decisión evita mantener índices adicionales que no aportan una mejora significativa.

La actualización de `auth_version` y la revocación de todas las sesiones deben ejecutarse en la misma transacción. Así, el backend no debe depender exclusivamente de que el proceso de revocación masiva haya alcanzado cada sesión para rechazar tokens anteriores.

## 2.4. Consulta crítica: búsqueda del Refresh Token

El backend calculará el SHA-256 del valor recibido desde la cookie y consultará:

```sql
SELECT
    id,
    session_id,
    issued_at,
    expires_at,
    consumed_at,
    revoked_at,
    replaced_by_token_id
FROM glucovida.auth_refresh_tokens
WHERE token_hash = :token_hash
  AND consumed_at IS NULL
  AND revoked_at IS NULL
  AND expires_at > CURRENT_TIMESTAMP;
```

El índice único `uq_auth_refresh_tokens_hash` permite localizar el registro mediante una búsqueda exacta.

La consulta deberá continuar con la validación del estado de la sesión y del usuario.

**No se debe confiar únicamente en que el Refresh Token aparezca en la tabla.** También debe verificarse que pertenezca a una sesión válida.

## 2.5. Índices y consultas: consideraciones de rendimiento

- Se utilizarán índices B-tree para identificadores, hashes y fechas de consulta habitual.
- Se utilizarán índices parciales para limitar los índices a registros activos cuando resulte conveniente.
- Los índices únicos garantizarán la unicidad del correo y de los hashes.
- Se evitarán índices individuales sobre campos de baja selectividad que no tengan un patrón de consulta justificado.
- Se evaluarán las consultas reales con `EXPLAIN (ANALYZE, BUFFERS)` en el entorno de pruebas.
- Se supervisará el tamaño de las tablas y el crecimiento del historial de tokens y auditoría.

Los índices propuestos son una base para el MVP. Su necesidad y efectividad deberán confirmarse mediante mediciones con datos representativos, no únicamente por su definición en el DDL.

---

# 3. DICCIONARIO DE DATOS

Los siguientes diccionarios describen cada campo, su tipo, restricciones y propósito funcional.

## 3.1. Diccionario de `users`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Identificador único del usuario. |
| `names` | VARCHAR(80) | NOT NULL | Nombres del usuario. |
| `surnames` | VARCHAR(100) | NOT NULL | Apellidos del usuario. |
| `email` | VARCHAR(254) | NOT NULL, UNIQUE | Correo normalizado en minúsculas. |
| `password_hash` | VARCHAR(255) | NOT NULL | Hash de contraseña. Implementación bcrypt costo 12. |
| `account_status` | VARCHAR(24) | NOT NULL, DEFAULT, CHECK | Estado de la cuenta. |
| `email_verified_at` | TIMESTAMPTZ | NULL | Momento de verificación del correo. |
| `auth_version` | INTEGER | NOT NULL, DEFAULT 1, CHECK | Versión global que invalida tokens anteriores. |
| `password_changed_at` | TIMESTAMPTZ | NOT NULL | Fecha del último cambio de contraseña. |
| `failed_login_attempts` | SMALLINT | NOT NULL, DEFAULT 0, CHECK | Cantidad de intentos consecutivos fallidos. |
| `login_locked_until` | TIMESTAMPTZ | NULL | Finalización del bloqueo temporal. |
| `last_login_at` | TIMESTAMPTZ | NULL | Fecha del último login exitoso. |
| `created_at` | TIMESTAMPTZ | NOT NULL | Fecha de creación de la cuenta. |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Última actualización de los datos de cuenta. |

**Valores admitidos para `account_status`:**

- `pending_verification`
- `active`
- `suspended`
- `disabled`

El bloqueo por intentos fallidos no se tratará como un estado permanente de cuenta. Se manejará mediante `failed_login_attempts` y `login_locked_until`.

## 3.2. Diccionario de `auth_sessions`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Identificador de la sesión y valor utilizado como `sid`. |
| `user_id` | UUID | FK, NOT NULL, ON DELETE CASCADE | Usuario propietario. |
| `auth_version_at_creation` | INTEGER | NOT NULL, CHECK | Versión global al crear la sesión. |
| `created_at` | TIMESTAMPTZ | NOT NULL | Fecha de inicio de sesión. |
| `last_activity_at` | TIMESTAMPTZ | NOT NULL | Última actividad autenticada válida. |
| `absolute_expires_at` | TIMESTAMPTZ | GENERATED | Expiración absoluta, 24 horas después de la creación. |
| `ip_address` | INET | NULL | Dirección IP observada por el backend. |
| `user_agent` | VARCHAR(512) | NULL | Identificación limitada del navegador o cliente. |
| `revoked_at` | TIMESTAMPTZ | NULL | Momento de revocación de la sesión. |
| `revoke_reason` | VARCHAR(32) | NULL, CHECK | Motivo por el cual se revocó la sesión. |

**Motivos admitidos:**

- `logout`
- `password_change`
- `password_recovery`
- `refresh_reuse`
- `admin_action`
- `security_policy`
- `account_disabled`

La expiración por inactividad se determina mediante la diferencia entre el tiempo actual y `last_activity_at`.

## 3.3. Diccionario de `auth_refresh_tokens`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Identificador interno del registro. |
| `session_id` | UUID | FK, NOT NULL, ON DELETE CASCADE | Sesión propietaria del token. |
| `token_hash` | BYTEA | NOT NULL, UNIQUE, CHECK | Hash SHA-256 de 32 bytes. |
| `issued_at` | TIMESTAMPTZ | NOT NULL | Fecha de emisión. |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiración, nunca superior al límite absoluto de sesión. |
| `consumed_at` | TIMESTAMPTZ | NULL | Fecha en que el token fue utilizado durante una renovación. |
| `revoked_at` | TIMESTAMPTZ | NULL | Fecha de revocación anticipada. |
| `revoke_reason` | VARCHAR(32) | NULL, CHECK | Motivo de revocación. |
| `replaced_by_token_id` | UUID | FK, UNIQUE parcial, NULL | Identificador del Refresh Token sucesor. |

La tabla conserva el historial necesario para detectar reutilizaciones. No guarda el valor original de la cookie.

## 3.4. Diccionario de `password_recovery_tokens`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Identificador del registro. |
| `user_id` | UUID | FK, NOT NULL, ON DELETE CASCADE | Usuario que solicita recuperación. |
| `token_hash` | BYTEA | NOT NULL, UNIQUE, CHECK | Hash SHA-256 del token de recuperación. |
| `issued_at` | TIMESTAMPTZ | NOT NULL | Fecha de emisión. |
| `expires_at` | TIMESTAMPTZ | GENERATED | Expira exactamente 30 minutos después de `issued_at`. |
| `consumed_at` | TIMESTAMPTZ | NULL | Momento de uso del token. |
| `revoked_at` | TIMESTAMPTZ | NULL | Momento de invalidación anticipada. |

La limitación de solicitudes por cuenta e IP se administra externamente mediante Redis.

## 3.5. Diccionario de `email_verification_tokens`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Identificador del registro. |
| `user_id` | UUID | FK, NOT NULL, ON DELETE CASCADE | Cuenta que debe verificar el correo. |
| `token_hash` | BYTEA | NOT NULL, UNIQUE, CHECK | Hash SHA-256 del token. |
| `issued_at` | TIMESTAMPTZ | NOT NULL | Fecha de emisión. |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Fecha de expiración establecida por la política de verificación. |
| `consumed_at` | TIMESTAMPTZ | NULL | Fecha en que se verificó el correo. |
| `revoked_at` | TIMESTAMPTZ | NULL | Fecha de invalidación anticipada. |

La vigencia exacta de los enlaces de verificación todavía debe definirse antes de implementar CU01.

## 3.6. Diccionario de `audit_events`

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Identificador del evento. |
| `user_id` | UUID | FK, NULL, ON DELETE SET NULL | Usuario asociado al evento, cuando se conoce. |
| `session_id` | UUID | FK, NULL, ON DELETE SET NULL | Sesión asociada al evento. |
| `event_type` | VARCHAR(64) | NOT NULL, CHECK | Tipo de evento de seguridad. |
| `outcome` | VARCHAR(20) | NOT NULL, CHECK | Resultado del evento. |
| `occurred_at` | TIMESTAMPTZ | NOT NULL | Fecha del evento. |
| `ip_address` | INET | NULL | IP asociada al evento. |
| `user_agent` | VARCHAR(512) | NULL | Identificación limitada del cliente. |
| `request_id` | UUID | NULL | Identificador de trazabilidad HTTP. |
| `metadata` | JSONB | NOT NULL, DEFAULT, CHECK | Información contextual no secreta. |

`metadata` deberá utilizar una lista permitida de propiedades definida por el backend, no un volcado completo de la solicitud o respuesta HTTP.

---

# 4. SCRIPT DDL COMPLETO PARA POSTGRESQL

El siguiente script crea el esquema y las seis tablas principales, sus restricciones, claves foráneas, índices y el mecanismo de validación de expiración de Refresh Tokens.

Está diseñado para PostgreSQL 18 y puede servir como base para una migración inicial de Alembic.

**Importante:** debe ejecutarse en una base de datos de desarrollo o pruebas antes de integrarlo en producción. La gestión posterior del esquema deberá realizarse mediante migraciones versionadas.

```sql
BEGIN;

-- =========================================================
-- 1. ESQUEMA
-- =========================================================

CREATE SCHEMA IF NOT EXISTS glucovida;

SET LOCAL search_path TO glucovida, public;


-- =========================================================
-- 2. USERS
-- =========================================================

CREATE TABLE glucovida.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    names VARCHAR(80) NOT NULL,
    surnames VARCHAR(100) NOT NULL,

    email VARCHAR(254) NOT NULL,

    password_hash VARCHAR(255) NOT NULL,

    account_status VARCHAR(24) NOT NULL
        DEFAULT 'pending_verification',

    email_verified_at TIMESTAMPTZ,

    auth_version INTEGER NOT NULL DEFAULT 1,

    password_changed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    failed_login_attempts SMALLINT NOT NULL DEFAULT 0,

    login_locked_until TIMESTAMPTZ,

    last_login_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_users_names
        CHECK (length(btrim(names)) > 0),

    CONSTRAINT ck_users_surnames
        CHECK (length(btrim(surnames)) > 0),

    CONSTRAINT ck_users_email
        CHECK (
            email = lower(email)
            AND email = btrim(email)
            AND length(email) > 0
        ),

    CONSTRAINT ck_users_password_hash
        CHECK (length(password_hash) > 0),

    CONSTRAINT ck_users_account_status
        CHECK (
            account_status IN (
                'pending_verification',
                'active',
                'suspended',
                'disabled'
            )
        ),

    CONSTRAINT ck_users_active_verified
        CHECK (
            account_status <> 'active'
            OR email_verified_at IS NOT NULL
        ),

    CONSTRAINT ck_users_auth_version
        CHECK (auth_version >= 1),

    CONSTRAINT ck_users_failed_attempts
        CHECK (failed_login_attempts BETWEEN 0 AND 5),

    CONSTRAINT ck_users_login_lock
        CHECK (
            login_locked_until IS NULL
            OR failed_login_attempts = 5
        )
);


-- =========================================================
-- 3. AUTH_SESSIONS
-- =========================================================

CREATE TABLE glucovida.auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    auth_version_at_creation INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    absolute_expires_at TIMESTAMPTZ
        GENERATED ALWAYS AS (
            created_at + INTERVAL '24 hours'
        ) STORED,

    ip_address INET,

    user_agent VARCHAR(512),

    revoked_at TIMESTAMPTZ,

    revoke_reason VARCHAR(32),

    CONSTRAINT fk_auth_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_auth_sessions_version
        CHECK (auth_version_at_creation >= 1),

    CONSTRAINT ck_auth_sessions_activity
        CHECK (
            last_activity_at >= created_at
            AND last_activity_at <= absolute_expires_at
        ),

    CONSTRAINT ck_auth_sessions_revoked
        CHECK (
            (
                revoked_at IS NULL
                AND revoke_reason IS NULL
            )
            OR
            (
                revoked_at IS NOT NULL
                AND revoke_reason IS NOT NULL
            )
        ),

    CONSTRAINT ck_auth_sessions_revoke_reason
        CHECK (
            revoke_reason IS NULL
            OR revoke_reason IN (
                'logout',
                'password_change',
                'password_recovery',
                'refresh_reuse',
                'admin_action',
                'security_policy',
                'account_disabled'
            )
        ),

    CONSTRAINT ck_auth_sessions_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= created_at
        )
);


-- =========================================================
-- 4. AUTH_REFRESH_TOKENS
-- =========================================================

CREATE TABLE glucovida.auth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    session_id UUID NOT NULL,

    token_hash BYTEA NOT NULL,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ NOT NULL,

    consumed_at TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    revoke_reason VARCHAR(32),

    replaced_by_token_id UUID,

    CONSTRAINT fk_refresh_tokens_session
        FOREIGN KEY (session_id)
        REFERENCES glucovida.auth_sessions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_refresh_tokens_successor
        FOREIGN KEY (replaced_by_token_id)
        REFERENCES glucovida.auth_refresh_tokens(id)
        ON DELETE SET NULL,

    CONSTRAINT ck_refresh_token_hash_length
        CHECK (octet_length(token_hash) = 32),

    CONSTRAINT ck_refresh_token_expiration
        CHECK (expires_at > issued_at),

    CONSTRAINT ck_refresh_token_state
        CHECK (
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
        ),

    CONSTRAINT ck_refresh_token_consumed_at
        CHECK (
            consumed_at IS NULL
            OR consumed_at >= issued_at
        ),

    CONSTRAINT ck_refresh_token_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= issued_at
        ),

    CONSTRAINT ck_refresh_token_revocation_reason
        CHECK (
            (
                revoked_at IS NULL
                AND revoke_reason IS NULL
            )
            OR
            (
                revoked_at IS NOT NULL
                AND revoke_reason IS NOT NULL
            )
        ),

    CONSTRAINT ck_refresh_token_replacement
        CHECK (
            replaced_by_token_id IS NULL
            OR (
                replaced_by_token_id <> id
                AND consumed_at IS NOT NULL
                AND revoked_at IS NULL
            )
        )
);


-- =========================================================
-- 5. PASSWORD_RECOVERY_TOKENS
-- =========================================================

CREATE TABLE glucovida.password_recovery_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    token_hash BYTEA NOT NULL,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ
        GENERATED ALWAYS AS (
            issued_at + INTERVAL '30 minutes'
        ) STORED,

    consumed_at TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    CONSTRAINT fk_recovery_tokens_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_recovery_token_hash_length
        CHECK (octet_length(token_hash) = 32),

    CONSTRAINT ck_recovery_token_state
        CHECK (
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
        ),

    CONSTRAINT ck_recovery_token_consumed_at
        CHECK (
            consumed_at IS NULL
            OR consumed_at >= issued_at
        ),

    CONSTRAINT ck_recovery_token_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= issued_at
        )
);


-- =========================================================
-- 6. EMAIL_VERIFICATION_TOKENS
-- =========================================================

CREATE TABLE glucovida.email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    token_hash BYTEA NOT NULL,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMPTZ NOT NULL,

    consumed_at TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    CONSTRAINT fk_email_verification_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE CASCADE,

    CONSTRAINT ck_email_verification_hash_length
        CHECK (octet_length(token_hash) = 32),

    CONSTRAINT ck_email_verification_expiration
        CHECK (expires_at > issued_at),

    CONSTRAINT ck_email_verification_state
        CHECK (
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
        ),

    CONSTRAINT ck_email_verification_consumed_at
        CHECK (
            consumed_at IS NULL
            OR consumed_at >= issued_at
        ),

    CONSTRAINT ck_email_verification_revoked_at
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= issued_at
        )
);


-- =========================================================
-- 7. AUDIT_EVENTS
-- =========================================================

CREATE TABLE glucovida.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID,

    session_id UUID,

    event_type VARCHAR(64) NOT NULL,

    outcome VARCHAR(20) NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    ip_address INET,

    user_agent VARCHAR(512),

    request_id UUID,

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id)
        REFERENCES glucovida.users(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_audit_session
        FOREIGN KEY (session_id)
        REFERENCES glucovida.auth_sessions(id)
        ON DELETE SET NULL,

    CONSTRAINT ck_audit_event_type
        CHECK (
            event_type IN (
                'account_registered',
                'email_verification_completed',
                'login_succeeded',
                'login_failed',
                'login_locked',
                'session_created',
                'logout',
                'session_revoked',
                'sessions_revoked_all',
                'refresh_rotated',
                'refresh_reuse_detected',
                'password_changed',
                'password_recovery_requested',
                'password_recovery_completed',
                'account_suspended',
                'account_disabled'
            )
        ),

    CONSTRAINT ck_audit_outcome
        CHECK (
            outcome IN (
                'success',
                'failure',
                'blocked',
                'security_event'
            )
        ),

    CONSTRAINT ck_audit_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);


-- =========================================================
-- 8. ÍNDICES USERS
-- =========================================================

CREATE UNIQUE INDEX uq_users_email
ON glucovida.users (email);

CREATE INDEX idx_users_login_locked_until
ON glucovida.users (login_locked_until)
WHERE login_locked_until IS NOT NULL;

CREATE INDEX idx_users_account_status
ON glucovida.users (account_status);


-- =========================================================
-- 9. ÍNDICES AUTH_SESSIONS
-- =========================================================

CREATE INDEX idx_auth_sessions_user_revoked
ON glucovida.auth_sessions (user_id, revoked_at);

CREATE INDEX idx_auth_sessions_active_absolute_expiry
ON glucovida.auth_sessions (absolute_expires_at)
WHERE revoked_at IS NULL;

CREATE INDEX idx_auth_sessions_active_last_activity
ON glucovida.auth_sessions (last_activity_at)
WHERE revoked_at IS NULL;


-- =========================================================
-- 10. ÍNDICES AUTH_REFRESH_TOKENS
-- =========================================================

CREATE UNIQUE INDEX uq_auth_refresh_tokens_hash
ON glucovida.auth_refresh_tokens (token_hash);

CREATE INDEX idx_auth_refresh_tokens_session_issued
ON glucovida.auth_refresh_tokens (session_id, issued_at DESC);

CREATE UNIQUE INDEX uq_auth_refresh_one_active_per_session
ON glucovida.auth_refresh_tokens (session_id)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;

CREATE INDEX idx_auth_refresh_tokens_active_expiry
ON glucovida.auth_refresh_tokens (expires_at)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;

CREATE UNIQUE INDEX uq_auth_refresh_replaced_by
ON glucovida.auth_refresh_tokens (replaced_by_token_id)
WHERE replaced_by_token_id IS NOT NULL;


-- =========================================================
-- 11. ÍNDICES PASSWORD_RECOVERY_TOKENS
-- =========================================================

CREATE UNIQUE INDEX uq_password_recovery_token_hash
ON glucovida.password_recovery_tokens (token_hash);

CREATE INDEX idx_password_recovery_user_issued
ON glucovida.password_recovery_tokens (user_id, issued_at DESC);

CREATE UNIQUE INDEX uq_password_recovery_one_active_per_user
ON glucovida.password_recovery_tokens (user_id)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;


-- =========================================================
-- 12. ÍNDICES EMAIL_VERIFICATION_TOKENS
-- =========================================================

CREATE UNIQUE INDEX uq_email_verification_token_hash
ON glucovida.email_verification_tokens (token_hash);

CREATE INDEX idx_email_verification_user_issued
ON glucovida.email_verification_tokens (user_id, issued_at DESC);

CREATE UNIQUE INDEX uq_email_verification_one_active_per_user
ON glucovida.email_verification_tokens (user_id)
WHERE consumed_at IS NULL
  AND revoked_at IS NULL;


-- =========================================================
-- 13. ÍNDICES AUDIT_EVENTS
-- =========================================================

CREATE INDEX idx_audit_events_user_time
ON glucovida.audit_events (user_id, occurred_at DESC)
WHERE user_id IS NOT NULL;

CREATE INDEX idx_audit_events_session_time
ON glucovida.audit_events (session_id, occurred_at DESC)
WHERE session_id IS NOT NULL;

CREATE INDEX idx_audit_events_type_time
ON glucovida.audit_events (event_type, occurred_at DESC);

CREATE INDEX idx_audit_events_occurred_at
ON glucovida.audit_events (occurred_at DESC);


-- =========================================================
-- 14. VALIDACIÓN ENTRE AUTH_REFRESH_TOKENS Y AUTH_SESSIONS
-- =========================================================

CREATE OR REPLACE FUNCTION glucovida.validate_refresh_token_session()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_created_at TIMESTAMPTZ;
    v_absolute_expires_at TIMESTAMPTZ;
    v_last_activity_at TIMESTAMPTZ;
    v_revoked_at TIMESTAMPTZ;
    v_successor_session_id UUID;
BEGIN

    SELECT
        created_at,
        absolute_expires_at,
        last_activity_at,
        revoked_at
    INTO
        v_created_at,
        v_absolute_expires_at,
        v_last_activity_at,
        v_revoked_at
    FROM glucovida.auth_sessions
    WHERE id = NEW.session_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'La sesión asociada al Refresh Token no existe'
            USING ERRCODE = '23503';
    END IF;

    IF NEW.issued_at < v_created_at THEN
        RAISE EXCEPTION
            'El Refresh Token no puede emitirse antes de crear la sesión'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.issued_at >= v_absolute_expires_at THEN
        RAISE EXCEPTION
            'No se puede emitir un Refresh Token después de la expiración absoluta'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.expires_at > v_absolute_expires_at THEN
        RAISE EXCEPTION
            'El Refresh Token supera la expiración absoluta de la sesión'
            USING ERRCODE = '23514';
    END IF;

    IF v_revoked_at IS NOT NULL THEN
        RAISE EXCEPTION
            'No se puede emitir un Refresh Token para una sesión revocada'
            USING ERRCODE = '23514';
    END IF;

    IF v_last_activity_at <=
        CURRENT_TIMESTAMP - INTERVAL '30 minutes' THEN
        RAISE EXCEPTION
            'No se puede renovar una sesión inactiva'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.replaced_by_token_id IS NOT NULL THEN

        SELECT session_id
        INTO v_successor_session_id
        FROM glucovida.auth_refresh_tokens
        WHERE id = NEW.replaced_by_token_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION
                'El Refresh Token sucesor no existe'
                USING ERRCODE = '23503';
        END IF;

        IF v_successor_session_id <> NEW.session_id THEN
            RAISE EXCEPTION
                'El Refresh Token sucesor debe pertenecer a la misma sesión'
                USING ERRCODE = '23514';
        END IF;

    END IF;

    RETURN NEW;

END;
$$;


CREATE TRIGGER trg_validate_refresh_token_session
BEFORE INSERT OR UPDATE OF
    session_id,
    issued_at,
    expires_at,
    replaced_by_token_id
ON glucovida.auth_refresh_tokens
FOR EACH ROW
EXECUTE FUNCTION glucovida.validate_refresh_token_session();


-- =========================================================
-- 15. COMENTARIOS DE DOCUMENTACIÓN
-- =========================================================

COMMENT ON TABLE glucovida.users IS
'Identidad, credenciales y estado de autenticación de usuarios de GlucoVida.';

COMMENT ON TABLE glucovida.auth_sessions IS
'Registro persistente de sesiones autenticadas, expiración y revocación.';

COMMENT ON TABLE glucovida.auth_refresh_tokens IS
'Hashes y trazabilidad de Refresh Tokens opacos emitidos por sesión.';

COMMENT ON TABLE glucovida.password_recovery_tokens IS
'Tokens de recuperación de contraseña de un solo uso con vigencia de 30 minutos.';

COMMENT ON TABLE glucovida.email_verification_tokens IS
'Tokens de verificación de correo electrónico.';

COMMENT ON TABLE glucovida.audit_events IS
'Registro histórico de eventos de autenticación y seguridad sin credenciales ni secretos.';

COMMENT ON COLUMN glucovida.users.auth_version IS
'Versión global de autenticación. Su incremento invalida credenciales de sesiones anteriores.';

COMMENT ON COLUMN glucovida.auth_sessions.auth_version_at_creation IS
'Versión de autenticación del usuario al crear la sesión. Debe coincidir con JWT av y users.auth_version.';

COMMENT ON COLUMN glucovida.auth_refresh_tokens.token_hash IS
'Hash SHA-256 de 32 bytes del Refresh Token. Nunca almacena el token original.';

COMMENT ON COLUMN glucovida.password_recovery_tokens.expires_at IS
'Columna generada: la recuperación expira 30 minutos después de issued_at.';

COMMENT ON COLUMN glucovida.audit_events.metadata IS
'Datos contextuales permitidos. No almacenar contraseñas, hashes ni tokens completos.';


COMMIT;
```

---

# 5. REGLAS DE INTEGRIDAD Y SEGURIDAD COMPLEMENTARIAS

El DDL establece las restricciones estructurales, pero algunas condiciones dependen de operaciones transaccionales y reglas de aplicación.

## 5.1. Política ON DELETE

| Relación | Acción | Justificación |
|---|---|---|
| `users` → `auth_sessions` | CASCADE | Una sesión no puede existir sin su usuario. |
| `auth_sessions` → `auth_refresh_tokens` | CASCADE | Los Refresh Tokens pertenecen exclusivamente a una sesión. |
| `users` → `password_recovery_tokens` | CASCADE | Los tokens de recuperación no tienen utilidad sin la cuenta. |
| `users` → `email_verification_tokens` | CASCADE | Los tokens de verificación dependen de la cuenta. |
| `users` → `audit_events` | SET NULL | Permite conservar el evento aunque se elimine la referencia al usuario. |
| `auth_sessions` → `audit_events` | SET NULL | Conserva la auditoría sin exigir que la sesión siga existiendo. |
| `auth_refresh_tokens` → su sucesor | SET NULL | Permite depurar registros sin dejar una referencia rota. |

**Regla operativa:** la desactivación ordinaria de una cuenta no debe eliminar físicamente al usuario. Se utilizará `account_status = 'disabled'` o `suspended`, según corresponda.

Las eliminaciones definitivas deberán realizarse mediante un proceso controlado que contemple las dependencias de los módulos clínicos y las obligaciones de retención que resulten aplicables.

## 5.2. Operación transaccional: cambio de contraseña

El backend deberá actualizar la contraseña, incrementar la versión y revocar las sesiones dentro de una misma transacción.

Ejemplo conceptual:

```sql
BEGIN;

UPDATE glucovida.users
SET
    password_hash = :new_password_hash,
    password_changed_at = CURRENT_TIMESTAMP,
    auth_version = auth_version + 1,
    failed_login_attempts = 0,
    login_locked_until = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :user_id;

UPDATE glucovida.auth_sessions
SET
    revoked_at = CURRENT_TIMESTAMP,
    revoke_reason = 'password_change'
WHERE user_id = :user_id
  AND revoked_at IS NULL;

UPDATE glucovida.auth_refresh_tokens AS rt
SET
    revoked_at = CURRENT_TIMESTAMP,
    revoke_reason = 'session_revoked'
FROM glucovida.auth_sessions AS s
WHERE rt.session_id = s.id
  AND s.user_id = :user_id
  AND rt.consumed_at IS NULL
  AND rt.revoked_at IS NULL;

INSERT INTO glucovida.audit_events (
    user_id,
    event_type,
    outcome,
    metadata
)
VALUES (
    :user_id,
    'password_changed',
    'success',
    '{}'::JSONB
);

COMMIT;
```

Este ejemplo ilustra las operaciones y su agrupación. La implementación debe comprobar que el usuario fue actualizado exactamente una vez y manejar cualquier error mediante rollback.

La lógica real debe ejecutarse con autorización válida y bloqueo transaccional apropiado para impedir operaciones concurrentes inconsistentes.

## 5.3. Operación transaccional: cierre de sesión

```sql
BEGIN;

UPDATE glucovida.auth_sessions
SET
    revoked_at = CURRENT_TIMESTAMP,
    revoke_reason = 'logout'
WHERE id = :session_id
  AND user_id = :user_id
  AND revoked_at IS NULL;

UPDATE glucovida.auth_refresh_tokens
SET
    revoked_at = CURRENT_TIMESTAMP,
    revoke_reason = 'session_revoked'
WHERE session_id = :session_id
  AND consumed_at IS NULL
  AND revoked_at IS NULL;

INSERT INTO glucovida.audit_events (
    user_id,
    session_id,
    event_type,
    outcome,
    metadata
)
VALUES (
    :user_id,
    :session_id,
    'logout',
    'success',
    '{}'::JSONB
);

COMMIT;
```

El cierre de sesión afecta únicamente al registro de sesión indicado. No revoca las sesiones de otros dispositivos.

## 5.4. Consistencia de rotación de Refresh Tokens

La renovación requiere que dos solicitudes simultáneas no puedan utilizar el mismo Refresh Token para obtener sucesores distintos.

La implementación debe:

1. Localizar el token por `token_hash`.
2. Bloquear el registro del token.
3. Bloquear la sesión correspondiente.
4. Verificar la vigencia del token y de la sesión.
5. Marcar el token anterior como consumido.
6. Insertar el sucesor.
7. Vincular el token anterior con el sucesor.
8. Confirmar la transacción.

Se utilizará `SELECT ... FOR UPDATE` sobre los registros pertinentes, además de la restricción única parcial de un token disponible por sesión.

No se debe ejecutar el proceso como una secuencia de operaciones independientes sin transacción.

## 5.5. Persistencia de intentos fallidos

La tabla `users` conserva:

- Número de intentos consecutivos fallidos.
- Fecha hasta la cual se mantiene el bloqueo.

La aplicación debe actualizar ambos campos de manera atómica.

Para evitar condiciones de carrera en el inicio de sesión se recomienda bloquear la fila del usuario mediante `SELECT ... FOR UPDATE` antes de modificar los contadores.

Los límites por IP, sesión y ventanas temporales de otros endpoints se mantendrán en Redis, conforme al componente 2.

---

# 6. CONSIDERACIONES PARA SQLALCHEMY Y ALEMBIC

## 6.1. Correspondencia ORM

Cada tabla debe representarse mediante un modelo de SQLAlchemy.

Ejemplo conceptual para `User`:

```python
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "auth_version >= 1",
            name="ck_users_auth_version",
        ),
        {"schema": "glucovida"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    auth_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
```

Este fragmento muestra únicamente la correspondencia básica. El modelo completo deberá incorporar todos los campos, restricciones, relaciones, índices y columnas generadas definidos en el DDL.

## 6.2. Migraciones

Alembic administrará las modificaciones de la base de datos.

Flujo esperado:

1. Definir los modelos ORM.
2. Configurar `target_metadata` en Alembic.
3. Generar una migración inicial.
4. Revisar manualmente el DDL generado.
5. Verificar claves foráneas, índices parciales, restricciones y triggers.
6. Ejecutar la migración en una base de datos limpia.
7. Ejecutar pruebas de integración.
8. Aprobar y versionar la migración.

No se recomienda confiar exclusivamente en `--autogenerate` para generar triggers, funciones o reglas especiales. Estos elementos deberán incluirse y revisarse expresamente en las migraciones.

---

# 7. REGLAS DE SEGURIDAD Y OPERACIÓN DE LA BASE DE DATOS

## 7.1. Separación de permisos

Se recomienda trabajar con roles diferentes para:

- Propietario y administrador del esquema.
- Usuario de ejecución del backend.
- Usuario de migraciones.
- Usuario de lectura o monitoreo, cuando corresponda.

El usuario de ejecución del backend no deberá disponer de permisos generales para modificar el esquema ni administrar roles de PostgreSQL.

## 7.2. Auditoría de solo adición

El backend podrá insertar eventos de auditoría y consultar aquellos que necesite mostrar o investigar.

No deberá tener permisos ordinarios para modificar o eliminar eventos históricos.

La política de retención y depuración se administrará mediante un proceso separado y autorizado.

## 7.3. Protección de hashes y secretos

- Los hashes de contraseñas no se expondrán mediante la API.
- Los Refresh Tokens originales no se almacenarán.
- Los tokens de recuperación y verificación no se almacenarán en texto plano.
- Los secretos de conexión estarán fuera del código fuente.
- Los backups deberán protegerse mediante controles de acceso y cifrado apropiados.
- El acceso a las tablas de autenticación estará restringido al backend y personal técnico autorizado.

## 7.4. Privacidad de IP y User-Agent

Las direcciones IP y los identificadores de navegador pueden constituir datos personales o permitir identificar indirectamente a una persona.

Por ello:

- Solo se recopilarán para finalidades de seguridad y operación justificadas.
- Se restringirá su consulta.
- Se establecerá un periodo de conservación.
- No se utilizarán para publicidad ni perfiles comerciales.
- Se evitará copiar estos datos a logs o sistemas secundarios sin necesidad.

## 7.5. Independencia entre Redis y PostgreSQL

Redis conservará los contadores temporales de Rate Limiting.

PostgreSQL será responsable de la persistencia de cuentas, sesiones y tokens.

Una caída o reinicio de Redis no deberá provocar que las sesiones revocadas vuelvan a considerarse activas. Tampoco se podrá desactivar silenciosamente el Rate Limiting cuando Redis no esté disponible.

---

# 8. DECISIONES PENDIENTES ANTES DE CERRAR EL MODELO COMPLETO

El esquema de autenticación está definido como propuesta técnica, pero hay decisiones que todavía requieren tratamiento explícito:

| N.º | Asunto | Situación | Tratamiento |
|---|---|---|---|
| 1 | Vigencia exacta del token de verificación de correo | No definida | Establecer antes de implementar CU01. |
| 2 | Retención de auditoría y datos de IP/User-Agent | No definida | Acordar con la política de privacidad. |
| 3 | Modelo de roles y permisos | No incluido en estas seis tablas | Diseñar RBAC para usuarios, administradores y profesionales autorizados. |
| 4 | Procedimiento de eliminación definitiva de cuentas | Requiere revisar módulos dependientes | Definir borrado, anonimización y retención. |
| 5 | Política de conservación de Refresh Tokens consumidos | Pendiente de operación | Definir ventana de detección y depuración. |

Estas decisiones no cambian los tiempos aprobados para sesiones, Access Tokens ni recuperación de contraseñas.

También queda pendiente el diseño físico de las tablas funcionales de GlucoVida: mediciones de glucosa, catálogo nutricional, contenidos educativos y reportes.

---

# 9. CRITERIOS DE ACEPTACIÓN DEL MODELO FÍSICO

El modelo de autenticación se considerará preparado para iniciar implementación cuando se verifique:

1. Las seis tablas se crean correctamente en PostgreSQL.
2. Las claves primarias y foráneas se encuentran definidas.
3. Los correos normalizados no pueden duplicarse.
4. Los hashes de tokens tienen una longitud de 32 bytes.
5. Las sesiones no pueden superar las 24 horas.
6. Los tokens de recuperación expiran a los 30 minutos.
7. Un usuario no puede mantener más de un Refresh Token disponible por sesión.
8. No puede haber más de un token pendiente de recuperación por usuario.
9. No puede haber más de un token pendiente de verificación por usuario.
10. Los eventos de auditoría pueden conservarse sin referencias activas a usuarios o sesiones eliminados.
11. La consulta de autenticación por `sid` y `av` utiliza la clave primaria de la sesión y la clave primaria del usuario.
12. Las consultas de búsqueda de hashes aprovechan los índices únicos.
13. La rotación de Refresh Tokens se ejecuta de manera transaccional.
14. El backend utiliza conexiones y credenciales con privilegios mínimos.
15. Las pruebas de migración y restauración funcionan correctamente.

**Resultado esperado:** una estructura relacional consistente, segura y preparada para implementar la autenticación de GlucoVida mediante FastAPI, SQLAlchemy, PostgreSQL y Redis.

## 10. Referencias técnicas

- PostgreSQL Global Development Group. *PostgreSQL 18: Data Types*. https://www.postgresql.org/docs/18/datatype.html
- PostgreSQL Global Development Group. *PostgreSQL 18: UUID Functions*. https://www.postgresql.org/docs/18/functions-uuid.html
- PostgreSQL Global Development Group. *PostgreSQL 18: Constraints*. https://www.postgresql.org/docs/18/ddl-constraints.html
- PostgreSQL Global Development Group. *PostgreSQL 18: Multicolumn Indexes*. https://www.postgresql.org/docs/18/indexes-multicolumn.html
- PostgreSQL Global Development Group. *PostgreSQL 18: Explicit Locking*. https://www.postgresql.org/docs/18/explicit-locking.html
- OWASP Foundation. *Session Management Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- SQLAlchemy. *SQLAlchemy 2.x Documentation*. https://docs.sqlalchemy.org/
- Alembic. *Database Migration Tool for SQLAlchemy*. https://alembic.sqlalchemy.org/