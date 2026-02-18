-- Migration: Add STOCK strategy support to option_trades
-- Run against the MySQL database before deploying the new code.

-- Widen strategy_type from VARCHAR(5) to VARCHAR(10) for "STOCK"
ALTER TABLE option_trades MODIFY COLUMN strategy_type VARCHAR(10) NOT NULL;

-- Change contracts from INT to FLOAT for fractional shares
ALTER TABLE option_trades MODIFY COLUMN contracts FLOAT NOT NULL DEFAULT 1;

-- Make strike nullable (stock sales store sell price here, but it's optional)
ALTER TABLE option_trades MODIFY COLUMN strike FLOAT NULL;

-- Make expiry nullable (stock sales don't have expiry)
ALTER TABLE option_trades MODIFY COLUMN expiry VARCHAR(10) NULL;
