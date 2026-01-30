-- OPS Database Initialization Script
-- Database: db_ops

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS `db_ops` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `db_ops`;

-- Grant privileges
GRANT ALL PRIVILEGES ON db_ops.* TO 'ops_user'@'%';
FLUSH PRIVILEGES;

SET FOREIGN_KEY_CHECKS = 1;
