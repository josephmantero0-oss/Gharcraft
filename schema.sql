-- BuildSync Database Schema DDL
-- PropTech & Renovation Marketplace Database Architecture

CREATE DATABASE IF NOT EXISTS buildsync_db;
USE buildsync_db;

-- 1. Users Table (Clients, Contractors, Admins)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('client', 'contractor', 'admin') NOT NULL DEFAULT 'client',
    avatar_url VARCHAR(255) DEFAULT 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Contractor Profiles Table (KYC & Skills)
CREATE TABLE IF NOT EXISTS contractor_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    trade_category ENUM('Carpentry', 'Masonry', 'Interiors', 'Electrical', 'Plumbing', 'General') NOT NULL,
    experience_years INT DEFAULT 5,
    service_zipcodes VARCHAR(255) DEFAULT '400001, 400050, 400080',
    aadhaar_pan_redacted VARCHAR(50) DEFAULT 'XXXX-XXXX-9842 / ABCDE****F',
    kyc_status ENUM('pending', 'verified', 'rejected') DEFAULT 'verified',
    rating DECIMAL(3,2) DEFAULT 4.9,
    completed_projects_count INT DEFAULT 12,
    hourly_rate DECIMAL(10,2) DEFAULT 850.00,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    client_id INT NOT NULL,
    contractor_id INT,
    project_type VARCHAR(100) NOT NULL, -- e.g., 'Custom Wardrobe', 'Full Home Renovation', 'Structural Masonry'
    property_address TEXT NOT NULL,
    square_footage INT NOT NULL,
    estimated_total_cost DECIMAL(12,2) NOT NULL,
    escrow_deposited DECIMAL(12,2) DEFAULT 0.00,
    status ENUM('bidding', 'in_progress', 'completed', 'disputed') DEFAULT 'in_progress',
    price_locked BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(id),
    FOREIGN KEY (contractor_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Milestones Table
CREATE TABLE IF NOT EXISTS milestones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    phase_number INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    amount DECIMAL(12,2) NOT NULL,
    status ENUM('locked', 'funded', 'in_review', 'approved', 'released') DEFAULT 'locked',
    approved_at DATETIME NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Daily Progress Logs Table (Field Worker Uploads)
CREATE TABLE IF NOT EXISTS daily_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    contractor_id INT NOT NULL,
    log_date DATE NOT NULL,
    summary_text TEXT NOT NULL,
    voice_note_url VARCHAR(255) NULL,
    photo_1_url VARCHAR(255) NOT NULL,
    photo_2_url VARCHAR(255) NOT NULL,
    photo_3_url VARCHAR(255) NOT NULL,
    attendance_count INT DEFAULT 4,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (contractor_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Escrow Transactions Ledger
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    milestone_id INT NULL,
    payer_id INT NOT NULL,
    payee_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    platform_fee DECIMAL(12,2) NOT NULL,
    net_payout DECIMAL(12,2) NOT NULL,
    transaction_type ENUM('escrow_deposit', 'milestone_release', 'dispute_refund') NOT NULL,
    reference_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (payer_id) REFERENCES users(id),
    FOREIGN KEY (payee_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Materials Catalog & Ledger (Price-Lock Tracking)
CREATE TABLE IF NOT EXISTS raw_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    wholesale_unit_price DECIMAL(10,2) NOT NULL,
    retail_unit_price DECIMAL(10,2) NOT NULL,
    unit_measure VARCHAR(30) NOT NULL, -- e.g., 'sq.ft', 'bag', 'sheet'
    locked_price_guarantee DECIMAL(10,2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed Materials Data
INSERT INTO raw_materials (material_name, category, wholesale_unit_price, retail_unit_price, unit_measure, locked_price_guarantee) VALUES
('BWP Marine Plywood (18mm)', 'Carpentry', 115.00, 145.00, 'sq.ft', 115.00),
('Teak Veneer (4mm Grade A)', 'Interiors', 180.00, 230.00, 'sq.ft', 180.00),
('UltraTech Super Cement', 'Masonry', 370.00, 420.00, 'bag (50kg)', 370.00),
('TMT Steel Bars (12mm FE500D)', 'Structural', 62.00, 74.00, 'kg', 62.00),
('Soft-Close Hydraulic Hinges (Blum)', 'Hardware', 450.00, 580.00, 'pair', 450.00),
('Asian Paints Royal Emulsion', 'Finishing', 420.00, 510.00, 'liter', 420.00);
