-- Create website_content table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.website_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section VARCHAR NOT NULL,
    key VARCHAR NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(section, key)
);

-- Add proper indexes
CREATE INDEX IF NOT EXISTS idx_website_content_section ON public.website_content(section);
CREATE INDEX IF NOT EXISTS idx_website_content_key ON public.website_content(key);
CREATE INDEX IF NOT EXISTS idx_website_content_section_key ON public.website_content(section, key);

-- Add comment to the table
COMMENT ON TABLE public.website_content IS 'Table for storing dynamic website content'; 