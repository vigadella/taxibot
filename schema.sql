-- schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  telegram_id BIGINT NOT NULL UNIQUE,
  phone VARCHAR(32),
  yandex_uid VARCHAR(128),
  registered_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  rent_amount_cents BIGINT DEFAULT 2219000, -- 22 190.00 ₸ -> хранится в тиинах (сенты)
  hour_limit INT DEFAULT 12,
  settings JSONB DEFAULT '{}' 
);

CREATE TABLE tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  oauth_token_enc TEXT NOT NULL,
  refresh_token_enc TEXT,
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE shifts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  start_ts TIMESTAMP WITH TIME ZONE,
  end_ts TIMESTAMP WITH TIME ZONE,
  total_online_seconds BIGINT DEFAULT 0,
  earnings_cents BIGINT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  shift_id UUID REFERENCES shifts(id) ON DELETE SET NULL,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  order_external_id VARCHAR(128),
  amount_cents BIGINT DEFAULT 0,
  commission_cents BIGINT DEFAULT 0,
  start_ts TIMESTAMP WITH TIME ZONE,
  end_ts TIMESTAMP WITH TIME ZONE,
  raw_json JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(64),
  sent_ts TIMESTAMP WITH TIME ZONE DEFAULT now(),
  payload JSONB
);

CREATE INDEX idx_users_telegram ON users(telegram_id);
CREATE INDEX idx_tokens_user ON tokens(user_id);
CREATE INDEX idx_shifts_user ON shifts(user_id);
CREATE INDEX idx_orders_user ON orders(user_id);