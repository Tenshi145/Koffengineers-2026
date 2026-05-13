-- ============================================================
--  schema.sql — On My Way · MariaDB
--  Ejecutar: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS onmyway_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE onmyway_db;

-- ─── Usuarios ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)        NOT NULL,
    email       VARCHAR(150)        NOT NULL UNIQUE,
    password    VARCHAR(255)        NOT NULL,       -- bcrypt hash
    role        ENUM('admin','user') NOT NULL DEFAULT 'user',
    phone       VARCHAR(20),
    created_at  TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ─── Categorías ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(80)  NOT NULL UNIQUE,
    slug        VARCHAR(80)  NOT NULL UNIQUE,
    description TEXT,
    image_url   VARCHAR(500),
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ─── Productos ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id  INT UNSIGNED        NOT NULL,
    name         VARCHAR(200)        NOT NULL,
    slug         VARCHAR(200)        NOT NULL UNIQUE,
    description  TEXT,
    price        DECIMAL(10,2)       NOT NULL,
    stock        INT UNSIGNED        NOT NULL DEFAULT 0,
    image_url    VARCHAR(500),
    is_active    BOOLEAN             NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_category (category_id),
    INDEX idx_slug (slug),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- ─── Métodos de Envío ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS shipping_methods (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    description  VARCHAR(255),
    price        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    estimated_days_min INT UNSIGNED DEFAULT 1,
    estimated_days_max INT UNSIGNED DEFAULT 5,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- ─── Carritos ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS carts (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL UNIQUE,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cart_items (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cart_id     INT UNSIGNED NOT NULL,
    product_id  INT UNSIGNED NOT NULL,
    quantity    INT UNSIGNED NOT NULL DEFAULT 1,
    added_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id)    REFERENCES carts(id)    ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_cart_product (cart_id, product_id)
) ENGINE=InnoDB;

-- ─── Órdenes ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id                 INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id            INT UNSIGNED    NOT NULL,
    shipping_method_id INT UNSIGNED    NOT NULL,
    status             ENUM('pending','processing','shipped','delivered','cancelled')
                                       NOT NULL DEFAULT 'pending',
    -- Dirección de entrega (snapshot al momento de la compra)
    shipping_name      VARCHAR(150)    NOT NULL,
    shipping_address   VARCHAR(300)    NOT NULL,
    shipping_city      VARCHAR(100)    NOT NULL,
    shipping_zip       VARCHAR(20),
    shipping_phone     VARCHAR(20),
    -- Totales
    subtotal           DECIMAL(10,2)   NOT NULL,
    shipping_cost      DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    total              DECIMAL(10,2)   NOT NULL,
    notes              TEXT,
    created_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)            REFERENCES users(id)            ON DELETE RESTRICT,
    FOREIGN KEY (shipping_method_id) REFERENCES shipping_methods(id) ON DELETE RESTRICT,
    INDEX idx_user   (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
    id          INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    order_id    INT UNSIGNED   NOT NULL,
    product_id  INT UNSIGNED   NOT NULL,
    quantity    INT UNSIGNED   NOT NULL,
    unit_price  DECIMAL(10,2)  NOT NULL,   -- precio al momento de la compra
    subtotal    DECIMAL(10,2)  NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ============================================================
--  DATOS SEMILLA
-- ============================================================

-- Categorías
INSERT INTO categories (name, slug, description) VALUES
('Electrónica',  'electronica',  'Gadgets, accesorios y dispositivos'),
('Ropa',         'ropa',         'Moda para hombre y mujer'),
('Hogar',        'hogar',        'Todo para tu casa'),
('Deportes',     'deportes',     'Equipamiento y ropa deportiva'),
('Libros',       'libros',       'Ficción, técnicos y más');

-- Métodos de envío
INSERT INTO shipping_methods (name, description, price, estimated_days_min, estimated_days_max) VALUES
('Estándar',  'Envío regular',          49.00, 5, 7),
('Express',   'Entrega en 1-2 días',   149.00, 1, 2),
('Recolectar','Recoger en tienda',        0.00, 0, 0);

-- Admin inicial  (password: Admin123! — cambiar en producción)
-- Hash bcrypt generado con: python -c "import bcrypt; print(bcrypt.hashpw(b'Admin123!', bcrypt.gensalt()).decode())"
INSERT INTO users (name, email, password, role) VALUES
('Admin', 'admin@onmyway.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGfOfmOKSGm8vQmRFZvxdh7IWEi', 'admin');

-- Productos de muestra
INSERT INTO products (category_id, name, slug, description, price, stock, image_url) VALUES
(1, 'Auriculares Bluetooth Pro', 'auriculares-bluetooth-pro', 'Sonido envolvente, batería 30h', 899.00, 50, 'https://picsum.photos/seed/p1/400/400'),
(1, 'Cargador USB-C 65W',        'cargador-usb-c-65w',        'Carga rápida para laptop y móvil', 299.00, 100,'https://picsum.photos/seed/p2/400/400'),
(2, 'Playera Algodón Orgánico',  'playera-algodon-organico',  '100% algodón sustentable',         199.00, 80, 'https://picsum.photos/seed/p3/400/400'),
(2, 'Sudadera Hoodie Premium',   'sudadera-hoodie-premium',   'Fleece suave, bolsa canguro',       549.00, 40, 'https://picsum.photos/seed/p4/400/400'),
(3, 'Lámpara LED Escritorio',    'lampara-led-escritorio',    'Ajuste de brillo y temperatura',    349.00, 30, 'https://picsum.photos/seed/p5/400/400'),
(4, 'Botella Térmica 1L',        'botella-termica-1l',        'Mantiene frío 24h / calor 12h',     229.00, 60, 'https://picsum.photos/seed/p6/400/400'),
(5, 'Python Crash Course',       'python-crash-course',       'Aprende Python desde cero',         350.00, 25, 'https://picsum.photos/seed/p7/400/400');
