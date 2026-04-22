# Guía de Seguridad — DATA_Dashboard

Manual de operación para el PM de DATA (sin conocimientos de desarrollo requeridos).

---

## Resumen del modelo de seguridad

Las credenciales de SQL Server **nunca** se guardan en texto plano. El flujo es:

```
secrets.key  +  credentials.enc  -->  CredentialStore (solo en RAM)
```

- `secrets.key`: clave de cifrado Fernet (32 bytes en base64). Solo existe en el servidor.
- `credentials.enc`: credenciales cifradas (servidor, base de datos, usuario, contraseña).
- Ninguno de los dos ficheros entra en el repositorio Git ni en el `.exe`.
- Las rutas se pasan al servicio de Windows como variables de entorno.

---

## 1. Primer despliegue — generar clave y cifrar credenciales

> Ejecutar **una sola vez** en el servidor Windows destino.

### 1.1. Abrir PowerShell en el directorio de instalación

```powershell
cd C:\DATA_Dashboard          # o la ruta elegida en el servidor
```

### 1.2. Generar la clave Fernet

```powershell
python scripts\generate_key.py --out C:\DATA_secrets\secrets.key
```

- Sustituye `C:\DATA_secrets\` por la ruta protegida que hayas elegido **fuera** del directorio de la aplicación.
- Si el fichero ya existe, el script pedirá confirmación antes de sobreescribir.

### 1.3. Cifrar las credenciales

```powershell
python scripts\encrypt_credentials.py `
    --key C:\DATA_secrets\secrets.key `
    --out C:\DATA_secrets\credentials.enc
```

El script pedirá de forma interactiva:

| Campo | Descripción |
|---|---|
| Servidor SQL Server | Hostname o IP, p. ej. `SQLSRV01` o `192.168.1.10` |
| Base de datos | Nombre de la BD, p. ej. `AqualiaMonitoring` |
| Usuario | Login de SQL Server |
| Contraseña | No se muestra en pantalla |

Tras introducir los datos, muestra un resumen (sin contraseña) y pide confirmación antes de escribir el fichero.

### 1.4. Verificar los ficheros generados

```powershell
Test-Path C:\DATA_secrets\secrets.key      # debe devolver True
Test-Path C:\DATA_secrets\credentials.enc  # debe devolver True
```

---

## 2. Configurar variables de entorno en el servicio de Windows

El servicio (registrado con NSSM) debe conocer la ruta de los dos ficheros.

### Con NSSM (recomendado)

```powershell
nssm set DATA_Dashboard AppEnvironmentExtra `
    "SECRETS_KEY_PATH=C:\DATA_secrets\secrets.key" `
    "CREDENTIALS_PATH=C:\DATA_secrets\credentials.enc" `
    "DATA_SOURCE=sqlserver"
```

Tras el cambio, reiniciar el servicio:

```powershell
nssm restart DATA_Dashboard
```

### Con sc.exe (alternativa sin NSSM)

Editar manualmente las variables de entorno del servicio en el registro:

```
HKLM\SYSTEM\CurrentControlSet\Services\DATA_Dashboard\Environment
```

Añadir (tipo REG_MULTI_SZ):

```
SECRETS_KEY_PATH=C:\DATA_secrets\secrets.key
CREDENTIALS_PATH=C:\DATA_secrets\credentials.enc
DATA_SOURCE=sqlserver
```

---

## 3. Permisos NTFS en la carpeta de secretos

Solo la cuenta de servicio de Windows debe poder leer los ficheros de secretos.

### 3.1. Crear la carpeta con permisos restringidos

```powershell
# Crear carpeta (si no existe)
New-Item -Path C:\DATA_secrets -ItemType Directory -Force

# Quitar herencia y asignar permisos explícitos
$acl = Get-Acl C:\DATA_secrets
$acl.SetAccessRuleProtection($true, $false)   # desactivar herencia
$acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) }

# Dar control total al administrador local
$adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$acl.AddAccessRule($adminRule)

# Dar lectura a la cuenta de servicio (sustituir por el nombre real)
$svcRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "DOMINIO\svc_datadashboard", "Read", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$acl.AddAccessRule($svcRule)

Set-Acl C:\DATA_secrets $acl
```

> Sustituye `DOMINIO\svc_datadashboard` por la cuenta real que ejecuta el servicio.

### 3.2. Verificar permisos

```powershell
Get-Acl C:\DATA_secrets | Format-List
```

La salida solo debe mostrar `Administrators` y la cuenta de servicio.

---

## 4. Rotación de credenciales (cambio de contraseña)

Si la contraseña de SQL Server cambia **pero la clave no**:

```powershell
python scripts\encrypt_credentials.py `
    --key C:\DATA_secrets\secrets.key `
    --out C:\DATA_secrets\credentials.enc
```

Introducir los nuevos datos cuando el script los pida. El fichero `credentials.enc` se sobreescribe.

Reiniciar el servicio para que cargue las nuevas credenciales:

```powershell
nssm restart DATA_Dashboard
```

---

## 5. Rotación completa de clave (brecha de seguridad)

Si `secrets.key` o `credentials.enc` han sido comprometidos:

1. **Generar una nueva clave** (sobreescribe la anterior):

```powershell
python scripts\generate_key.py --out C:\DATA_secrets\secrets.key
# Confirmar con "s" cuando pregunte
```

2. **Re-cifrar las credenciales** con la nueva clave:

```powershell
python scripts\encrypt_credentials.py `
    --key C:\DATA_secrets\secrets.key `
    --out C:\DATA_secrets\credentials.enc
```

3. **Eliminar cualquier copia** del `secrets.key` o `credentials.enc` antiguo que pueda existir en otras ubicaciones.

4. Reiniciar el servicio:

```powershell
nssm restart DATA_Dashboard
```

---

## 6. Copia de seguridad de la clave

> **Crítico**: si pierdes `secrets.key`, los `credentials.enc` existentes son **irrecuperables**.

Guarda una copia de `secrets.key` en:

- Un gestor de contraseñas corporativo (KeePass, Azure Key Vault, etc.)
- Un almacenamiento cifrado separado del servidor de aplicación

**Nunca** subas `secrets.key` al repositorio Git ni lo incluyas en el `.exe`.

---

## 7. Verificación de arranque

Para confirmar que el servicio arranca con las credenciales correctas, revisar el log de NSSM:

```powershell
# Ver log de stdout del servicio
Get-Content C:\DATA_Dashboard\logs\service_stdout.log -Tail 50

# Ver log de stderr
Get-Content C:\DATA_Dashboard\logs\service_stderr.log -Tail 50
```

Un arranque correcto no muestra ningún error de tipo `FileNotFoundError` ni `ValueError` relacionado con credenciales.

---

## 8. Referencia rápida de variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATA_SOURCE` | Fuente de datos activa | `sqlserver` |
| `SECRETS_KEY_PATH` | Ruta absoluta a `secrets.key` | `C:\DATA_secrets\secrets.key` |
| `CREDENTIALS_PATH` | Ruta absoluta a `credentials.enc` | `C:\DATA_secrets\credentials.enc` |
| `INACTIVITY_HOURS` | Umbral de inactividad en horas (default: 24) | `24` |
| `STREAMLIT_PORT` | Puerto HTTP del dashboard (default: 8501) | `8501` |
