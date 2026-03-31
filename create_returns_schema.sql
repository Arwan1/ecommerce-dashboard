CREATE TABLE IF NOT EXISTS returns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    reason VARCHAR(255) NOT NULL DEFAULT 'Unspecified',
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    refund_amount DECIMAL(10, 2) DEFAULT 0.00,
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_returns_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_returns_product FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_returns_order_id (order_id),
    INDEX idx_returns_product_id (product_id),
    INDEX idx_returns_status (status),
    INDEX idx_returns_created_at (created_at)
);
