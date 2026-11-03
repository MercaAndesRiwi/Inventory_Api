# MercaAndes - API Inventory (F3)

Microservicio de inventario determinista y catálogo de vendedores para la plataforma MercaAndes.

---

## Que hace esta API

Esta API simula el sistema de inventario y stock para la arquitectura de microservicios de MercaAndes con dos funciones principales:

1. **Calculo de Stock Determinista**:
   - Calcula unidades disponibles para cualquier tupla `(SKU, tienda)` mediante un algoritmo basado en SHA-256.
   - Es totalmente determinista: los mismos valores de entrada siempre generan exactamente la misma disponibilidad sin depender de una base de datos.
2. **Catalogo e Inventario de Vendedores (F3)**:
   - **Catalogo de vendedores**: Mas de 3,000 vendedores (`SEL-001`, `SEL-002`, etc.) persistidos en PostgreSQL.
   - **Pool de 50,000 SKUs**: Catalogo de productos desde `SKU-00001` hasta `SKU-50000`.
   - **Snapshots cada 10 minutos**: Las existencias y marcas de tiempo se actualizan automaticamente de forma determinista cada 10 minutos.
   - **Seguridad**: Endpoints de inventario protegidos mediante tokens Bearer.
   - **Inyeccion de fallas**: Simula condiciones reales de red (limites de tasa `429` y caidas de servicio `503` en ~3% de las peticiones).

> **Nota sobre auto-inicializacion:** La API cuenta con inicializacion automatica en su ciclo de vida: al iniciar, verifica y crea la tabla `sellers` en PostgreSQL con los 3,000 registros si aun no existen.

---

## Inicio Rapido con Docker Compose (Recomendado)

La forma mas rapida de ejecutar la base de datos PostgreSQL y la API es mediante Docker Compose:

### 1. Preparar variables de entorno

Copia el archivo de configuracion base:

```powershell
# En PowerShell:
Copy-Item .env.example .env

# En Linux / macOS / Bash:
cp .env.example .env
```

### 2. Levantar los contenedores

```bash
docker compose up --build -d
```

Esto ejecutara:

- **`db`**: Contenedor PostgreSQL 16 expuesto en el puerto `5432`.
- **`api`**: Contenedor FastAPI expuesto en el puerto `8000`, el cual sembrara la tabla de sellers automaticamente al arrancar.

### 3. Verificar estado

Revisa que los contenedores esten corriendo y la base de datos este lista:

```bash
docker compose logs -f api
```

Deberas ver: `Application startup complete` y `Database already initialized with 3000 sellers`.

---

## Ejecucion Local (Alternativa sin Docker)

Si prefieres ejecutar el proyecto localmente con Python y `uv`:

```powershell
# 1. Instalar dependencias
uv sync

# 2. Poblar la base de datos de PostgreSQL local
uv run python -m inventory.infrastructure.persistence.seed_sellers

# 3. Iniciar el servidor
uv run python -m inventory.presentation.main
```

---

## Como probar en Swagger UI

Abre en tu navegador: **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Paso 1: Autenticacion (Para endpoints de inventario)

Los endpoints de inventario requieren autorizacion previa:

1. Haz clic en el boton **Authorize** (arriba a la derecha en Swagger).
2. En el campo `Value`, ingresa uno de los tokens validos configurados:
   ```text
   token-seller-123
   ```

   *(Swagger anade `Bearer ` automaticamente, no es necesario escribirlo).*
3. Presiona **Authorize** y luego **Close**.

---

### Paso 2: Valores exactos para probar los endpoints

| Endpoint                                                      | Descripcion                                          | Requiere Auth | Parametros de ejemplo para copiar                  |
| :------------------------------------------------------------ | :--------------------------------------------------- | :-----------: | :------------------------------------------------- |
| **`GET /`**                                           | Health Check del servicio                            |      No      | *(Ninguno, solo Execute)*                        |
| **`GET /api/v1/inventory/stock`**                     | Stock determinista (SKU / Tienda)                    |      No      | `sku`: `SKU-00001store_id`: `STORE-1`        |
| **`GET /api/v1/sellers`**                             | Listar todos los vendedores de la BD                 |      No      | *(Ninguno, solo Execute)*                        |
| **`GET /api/v1/sellers/{seller_id}`**                 | Consultar vendedor por ID                            |      No      | `seller_id`: `SEL-001`                         |
| **`GET /api/v1/sellers/{seller_id}/score`**           | Consultar el puntaje ya calculado y guardado en Gold |      No      | `seller_id`: `SEL-001`                         |
| **`GET /api/v1/sellers/{seller_id}/inventory`**       | Inventario paginado de un vendedor                   | **Si** | `seller_id`: `SEL-001page`: `1limit`: `10` |
| **`GET /api/v1/sellers/{seller_id}/inventory/{sku}`** | Stock de un SKU especifico del vendedor              | **Si** | `seller_id`: `SEL-001sku`: `SKU-23229`       |

> **Nota sobre los SKUs:**
> Cada vendedor tiene asignado un subconjunto de los 50,000 SKUs disponibles. Para consultar un SKU especifico, puedes usar `SKU-23229` (pertenece a `SEL-001`) o tomar cualquier `sku` devuelto por el endpoint paginado del vendedor.

El endpoint de puntaje consulta la fila existente en `gold_seller_score` y devuelve el puntaje, sus componentes y la fecha de cálculo. La API no vuelve a calcular esos valores. Acepta el ID del catálogo (`SEL-*`) y resuelve su UUID mediante `dim_seller_source_key`; también acepta directamente el UUID de `dim_seller`. En esta demo, varios IDs se agrupan por país y tipo, por lo que pueden compartir puntaje. Si todavía no hay puntaje, responde `404`; si Gold no está disponible, responde `503`. La API debe conectarse a la misma base PostgreSQL donde el job Spark escribe los resultados.

---

## Variables de Entorno Principales (`.env`)

| Variable                       | Descripcion                                           | Valor por defecto                                 |
| :----------------------------- | :---------------------------------------------------- | :------------------------------------------------ |
| `API_HOST` / `API_PORT`    | Host y puerto de la API                               | `0.0.0.0` / `8000`                            |
| `MASTER_SEED`                | Semilla para calculo determinista                     | `42`                                            |
| `MAX_STOCK`                  | Limite superior de existencias por SKU                | `450`                                           |
| `ERROR_RATE`                 | Tasa de simulacion de errores 429/503                 | `0.0` (o `0.03` para 3%)                      |
| `VALID_TOKENS`               | Tokens Bearer autorizados (separados por coma)        | `token-seller-123,bearer-token-mercaandes-2026` |
| `POS_DB_HOST`                | Host de PostgreSQL (`localhost` o `db` en docker) | `localhost`                                     |
| `POS_DB_PORT`                | Puerto de PostgreSQL                                  | `5432`                                          |
| `POS_DB_NAME`                | Nombre de la base de datos                            | `MercaAndes`                                    |
| `POS_DB_USER` / `PASSWORD` | Credenciales de base de datos                         | *(Configuradas en `.env`)*                    |

---

## Comandos de Desarrollo y Pruebas

```powershell
# Ejecutar los 17 tests unitarios
uv run pytest

# Ejecutar el linter y analisis de codigo
uv run ruff check

# Detener los contenedores de Docker
docker compose down
```
