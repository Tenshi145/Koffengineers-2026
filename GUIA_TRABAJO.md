# 🚀 ON MY WAY — Hackathon Blink Galaxy 2026
## Manual de Operaciones · Equipo Koffengineers

> **Regla de Oro:** Si no está en Git, no existe. Commitea frecuente, pushea antes de pausas.

---

## 👥 Roles y Responsabilidades

| # | Rol | Responsable | Stack Principal | Rama Base |
|---|-----|-------------|-----------------|-----------|
| 1 | **DevOps / DB Lead** | — | MariaDB, Raspberry Pi, Docker | `dev-infra` |
| 2 | **Backend Lead** | — | Python, Flask, JWT, API REST | `dev-back` |
| 3 | **Frontend Lead** | — | React, Vite, Tailwind CSS | `dev-front` |
| 4 | **Integrador / UI** | — | React, Axios, UX, Testing | `dev-front` |

---

## ⏰ Hitos — Bloques de 4 Horas

### 🟢 HORA 0–4 · "Cimientos" (CRÍTICO)
**Objetivo: Todo el equipo puede levantar el proyecto localmente.**

| Rol | Tarea | Entregable |
|-----|-------|------------|
| DevOps/DB | Instalar MariaDB en RasPi, ejecutar `schema.sql`, configurar `.env` | DB corriendo, usuario de app creado |
| DevOps/DB | Crear `docker-compose.yml` (opcional), documentar IP de la RasPi | `README.md` con IP del evento |
| Backend | Levantar `app.py`, probar conexión a DB, endpoint `/api/health` respondiendo | `GET /api/health → 200 OK` |
| Backend | Implementar auth: `POST /api/auth/register` y `POST /api/auth/login` con JWT | Tokens funcionando en Postman |
| Frontend | `npm create vite`, configurar Tailwind, instalar Axios, configurar proxy a backend | App corriendo en `localhost:5173` |
| Integrador | Crear layout base: Navbar, Footer, Router con React Router DOM | Rutas `/`, `/login`, `/catalog` navegables |

**✅ Gate de salida:** `curl http://<IP_RASPI>:5000/api/health` devuelve `{"status": "ok"}`

---

### 🟡 HORA 4–8 · "Core Features"
**Objetivo: Catálogo funcional + Login real.**

| Rol | Tarea | Entregable |
|-----|-------|------------|
| DevOps/DB | Poblar DB con 15+ productos seed en `seed.sql`, configurar nginx como proxy | Productos en DB, puerto 80 redirige |
| Backend | Endpoints: `GET /api/products`, `GET /api/products/:id`, `GET /api/categories` | JSON con productos y paginación |
| Backend | Endpoint carrito: `POST/GET/DELETE /api/cart` (persistente en DB) | Carrito vinculado a usuario |
| Frontend | Componente `ProductCard`, página `Catalog` con grid responsivo, filtros | Grid de productos renderizando datos reales |
| Integrador | Página `Login` + `Register` funcionales, contexto de Auth con JWT en localStorage | Usuario puede registrarse y loguear |

**✅ Gate de salida:** Un usuario puede registrarse, ver el catálogo y agregar un producto al carrito.

---

### 🟠 HORA 8–12 · "Checkout & Admin"
**Objetivo: Flujo completo de compra + Panel de administración.**

| Rol | Tarea | Entregable |
|-----|-------|------------|
| DevOps/DB | Monitorear RasPi (temperatura, memoria), backups de DB cada hora | Sistema estable, script de backup |
| Backend | Endpoints: `POST /api/orders`, `GET /api/orders/:id`, métodos de envío | Orden creada en DB con status |
| Backend | Endpoints admin: `POST/PUT/DELETE /api/admin/products`, `GET /api/admin/orders` | CRUD protegido por rol admin |
| Frontend | Página `Cart` con resumen, `Checkout` con form de dirección y método de envío | UI completa de checkout |
| Integrador | Panel Admin: lista de productos (editar/eliminar), lista de órdenes con status | Admin puede gestionar inventario |

**✅ Gate de salida:** Flujo completo: Login → Catálogo → Carrito → Checkout → Orden creada → Admin la ve.

---

### 🔴 HORA 12–16 · "Polish & Seguridad"
**Objetivo: UX pulida, validaciones, manejo de errores.**

| Rol | Tarea | Entregable |
|-----|-------|------------|
| DevOps/DB | Optimizar consultas lentas, configurar CORS definitivo, SSL si es posible | Tiempos de respuesta < 200ms |
| Backend | Validaciones con `marshmallow` o `pydantic`, manejo de errores global, logging | API devuelve errores claros |
| Backend | Endpoint de búsqueda: `GET /api/products?search=&category=&sort=` | Búsqueda y filtros funcionando |
| Frontend | Buscador en tiempo real, filtros por categoría, ordenamiento, loading states | UX fluida con skeletons |
| Integrador | Toasts de notificación, página de confirmación de orden, página 404 | Experiencia de usuario completa |

---

### 🏁 HORA 16–20 · "Integración Final"
**Objetivo: Todo integrado, probado en RasPi, listo para demo.**

| Rol | Tarea | Entregable |
|-----|-------|------------|
| DevOps/DB | Build de producción (`npm run build`), servir estáticos desde Flask o nginx | App accesible por IP en red local |
| Backend | Revisar todos los endpoints con datos reales, documentar en `API.md` | Documentación de la API |
| Frontend | Fix de bugs visuales, responsividad móvil, favicon, título de pestaña | App visualmente impecable |
| Integrador | Testing end-to-end del flujo completo, preparar demo script (2 min) | Demo ensayada y funcionando |

**✅ Gate de salida:** Jurado puede acceder a `http://<IP>` y completar una compra sin ayuda.

---

### 🎯 HORA 20–24 · "Demo & Buffer"
**Objetivo: Preparar presentación, pulir pitch, corregir bugs críticos.**

- [ ] Actualizar `README.md` con instrucciones de instalación
- [ ] Grabar video demo de 2 minutos (por si falla la red)
- [ ] Preparar 3 slides: Problema → Solución → Tech Stack
- [ ] Merge final a `main`, tag de release `v1.0.0-hackathon`
- [ ] **DORMIR AL MENOS 2 HORAS** 😴

---

## 🔄 Protocolo de Merges

```bash
# Antes de mergear a main (solo DevOps/DB y Backend Lead lo hacen):
git checkout main
git pull origin main
git merge --no-ff dev-back   # Merge con commit de merge explícito
git push origin main

# En RasPi (Deploy):
git pull origin main
sudo systemctl restart onmyway-api
```

---

## 🚨 Reglas de Emergencia

1. **Bug crítico en producción:** Crea rama `hotfix/<descripción>` desde `main`, arregla, mergea.
2. **Conflicto de merge:** El Integrador es el árbitro. Se resuelve en voz alta, no en silencio.
3. **RasPi se cae:** El DevOps tiene el backup. No entrar en pánico.
4. **Alguien se bloquea > 30 min:** Pedir ayuda inmediatamente. Ego = tiempo perdido.

---

## 📡 Acceso al Entorno

```
RasPi IP: _______________  (llenar al inicio del hackathon)
DB Host: localhost:3306
DB Name: onmyway_db
API URL: http://<IP>:5000
Frontend: http://<IP>:80  (o :5173 en dev)
```
