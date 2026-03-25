CREATE DATABASE IF NOT EXISTS airbnb_expert;
USE airbnb_expert;

CREATE TABLE IF NOT EXISTS properties (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255),
    region      VARCHAR(100),
    price       FLOAT,
    scraped_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);