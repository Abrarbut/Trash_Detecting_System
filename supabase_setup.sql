-- Create detections table for TrashWatch
CREATE TABLE IF NOT EXISTS detections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    label TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    camera_source TEXT NOT NULL,
    image_url TEXT
);

-- Create index on timestamp for faster queries
CREATE INDEX IF NOT EXISTS detections_timestamp_idx ON detections(timestamp DESC);

-- Test query
SELECT 'Setup complete!' AS message;
