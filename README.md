# 🛍️ On My Way — Marketplace

> **Hackathon Blink Galaxy 2026 · Equipo Koffengineers**

E-commerce completo construido con Flask + MariaDB + React + Vite + Tailwind CSS,
desplegable en Raspberry Pi 4.

---

## 📁 Estructura del Repositorio

```
Koffengineers-2026/
├── .gitignore
├── GUIA_TRABAJO.md          # Manual de operaciones y roles
├── README.md                # Este archivo
│
├── server/                  # Backend Python/Flask
│   ├── app.py               # Aplicación principal + todos los endpoints
│   ├── requirements.txt     # Dependencias Python
│   ├── schema.sql           # Esquema de MariaDB + datos seed
│   ├── .env.example         # Variables de entorno (copiar a .env)
│   └── venv/                # (ignorado por git)
│
└── client/                  # Frontend React/Vite
    ├── vite.config.js       # Config de Vite con host expuesto
    ├── package.json
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── lib/
        │   └── api.js           # Axios + interceptores JWT
        ├── context/
        │   └── AuthContext.jsx  # Estado global de autenticación
        ├── components/
        │   ├── ProductCard.jsx  # Card de producto
        │   ├── Navbar.jsx
        │   └── CartDrawer.jsx
        └── pages/
            ├── Home.jsx
            ├── Catalog.jsx
            ├── ProductDetail.jsx
            ├── Cart.jsx
            ├── Checkout.jsx
            ├── Login.jsx
            ├── Register.jsx
            ├── Orders.jsx
            └── admin/
                ├── Dashboard.jsx
                ├── Products.jsx
                └── Orders.jsx
```

---

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone https://github.com/JenniferMC26/Koffengineers-2026.git
cd Koffengineers-2026
```

### 2. Base de datos (MariaDB)
```bash
# Instalar MariaDB en RasPi
sudo apt update && sudo apt install -y mariadb-server

# Configurar seguridad
sudo mysql_secure_installation

# Crear usuario y base de datos
sudo mysql -u root -p << 'EOF'
CREATE USER 'onmyway_user'@'localhost' IDENTIFIED BY 'CambiarEsto123!';
GRANT ALL PRIVILEGES ON onmyway_db.* TO 'onmyway_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Ejecutar schema
mysql -u root -p < server/schema.sql
```

### 3. Backend (Flask)
```bash
cd server

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env   # ← Editar DB_PASSWORD, SECRET_KEY, JWT_SECRET

# Levantar servidor
python app.py
# API disponible en: http://0.0.0.0:5000
```

### 4. Frontend (React)
```bash
cd client

# Instalar dependencias
npm install

# Desarrollo (con hot reload)
npm run dev
# App disponible en: http://0.0.0.0:5173

# Producción
npm run build
npm run preview   # o servir con nginx
```

---

## 🌐 Acceso en Red Local (Jurado)

```
# Descubrir IP de la Raspberry Pi
ip addr show | grep "inet " | grep -v 127.0.0.1

# El jurado accede a:
http://<IP_RASPI>:5173   # Desarrollo
http://<IP_RASPI>:80     # Producción (con nginx)
```

### Configurar nginx (producción)
```bash
sudo apt install -y nginx

# /etc/nginx/sites-available/onmyway
server {
    listen 80;
    root /home/pi/Koffengineers-2026/client/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/onmyway /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🔑 Credenciales de Prueba

| Rol   | Email                | Password  |
|-------|----------------------|-----------|
| Admin | admin@onmyway.com    | Admin123! |

---

## 🔀 Flujo de Git

```bash
# Ramas principales
main          ← producción (solo merges aprobados)
dev-infra     ← DevOps / Base de datos
dev-back      ← Backend Flask
dev-front     ← Frontend React

# Crear rama de feature
git checkout dev-back
git checkout -b feature/cart-endpoint

# Trabajar, commitear frecuente
git add .
git commit -m "feat(cart): add POST /api/cart endpoint"
git push origin feature/cart-endpoint

# Mergear a rama dev (sin fast-forward para historial claro)
git checkout dev-back
git merge --no-ff feature/cart-endpoint
git push origin dev-back

# Solo DevOps mergea a main (al final de cada hito)
git checkout main
git merge --no-ff dev-back
git push origin main
git tag -a v1.0.0 -m "Release final hackathon"
```

---

## 📡 API — Endpoints Principales

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/api/health` | — | Estado del servidor |
| POST | `/api/auth/register` | — | Registro de usuario |
| POST | `/api/auth/login` | — | Login, devuelve JWT |
| GET | `/api/products` | — | Catálogo con filtros |
| GET | `/api/products/:slug` | — | Detalle de producto |
| GET | `/api/categories` | — | Lista de categorías |
| GET | `/api/cart` | JWT | Ver carrito |
| POST | `/api/cart` | JWT | Agregar al carrito |
| DELETE | `/api/cart/:id` | JWT | Quitar item |
| GET | `/api/shipping` | — | Métodos de envío |
| POST | `/api/orders` | JWT | Crear orden |
| GET | `/api/orders` | JWT | Mis órdenes |
| GET | `/api/admin/orders` | Admin | Todas las órdenes |
| PATCH | `/api/admin/orders/:id/status` | Admin | Cambiar status |
| POST | `/api/admin/products` | Admin | Crear producto |
| PUT | `/api/admin/products/:id` | Admin | Actualizar producto |
| DELETE | `/api/admin/products/:id` | Admin | Desactivar producto |

---

## 🛡️ Seguridad

- **Contraseñas:** Hashing con `bcrypt` (salt rounds = 12)
- **Autenticación:** JWT con expiración de 24 horas
- **Roles:** Middleware `admin_required` protege endpoints del panel
- **SQL Injection:** Consultas con parámetros `%s` en PyMySQL (nunca f-strings con input del usuario)
- **CORS:** Configurable via `CORS_ORIGINS` en `.env`

---

*Built with ❤️ by Koffengineers — Hackathon Blink Galaxy 2026*
