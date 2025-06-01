-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create newsletter_subscribers table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.newsletter_subscribers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR NOT NULL UNIQUE,
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for newsletter_subscribers
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_email ON public.newsletter_subscribers(email);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_is_active ON public.newsletter_subscribers(is_active);

-- Create feedback table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    feedback_type VARCHAR NOT NULL,
    message TEXT NOT NULL,
    email VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for feedback
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_feedback_type ON public.feedback(feedback_type);

-- Create page_views table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.page_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page VARCHAR NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for page_views
CREATE INDEX IF NOT EXISTS idx_page_views_page ON public.page_views(page);
CREATE INDEX IF NOT EXISTS idx_page_views_user_id ON public.page_views(user_id);
CREATE INDEX IF NOT EXISTS idx_page_views_timestamp ON public.page_views(timestamp);

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

-- Add indexes for website_content
CREATE INDEX IF NOT EXISTS idx_website_content_section ON public.website_content(section);
CREATE INDEX IF NOT EXISTS idx_website_content_key ON public.website_content(key);
CREATE INDEX IF NOT EXISTS idx_website_content_section_key ON public.website_content(section, key);

-- Add comments to tables
COMMENT ON TABLE public.newsletter_subscribers IS 'Table for storing newsletter subscribers';
COMMENT ON TABLE public.feedback IS 'Table for storing user feedback submissions';
COMMENT ON TABLE public.page_views IS 'Table for tracking page views and analytics';
COMMENT ON TABLE public.website_content IS 'Table for storing dynamic website content';

-- Insert default testimonials
INSERT INTO public.website_content (section, key, content)
VALUES 
    ('testimonials', 'testimonial_1', '{"text": "ZapRead has completely transformed how I consume research papers. I can get through them 30% faster with better comprehension. It''s a game-changer for academics.", "author_name": "Sarah Johnson", "author_title": "PhD Student", "author_image": "https://randomuser.me/api/portraits/women/32.jpg"}'),
    ('testimonials', 'testimonial_2', '{"text": "As someone with ADHD, focusing on text has always been a struggle. ZapRead has made reading so much easier by guiding my eye through the text. I''m finally enjoying books again!", "author_name": "Michael Torres", "author_title": "Software Engineer", "author_image": "https://randomuser.me/api/portraits/men/54.jpg"}'),
    ('testimonials', 'testimonial_3', '{"text": "I have to read hundreds of pages of legal documents weekly. Since using ZapRead, I''ve cut my review time by 20% while maintaining accuracy. Worth every penny!", "author_name": "Jennifer Miller", "author_title": "Corporate Lawyer", "author_image": "https://randomuser.me/api/portraits/women/68.jpg"}')
ON CONFLICT (section, key) DO NOTHING; 