-- ============================================================================
-- ZapRead Admin Dashboard Database Schema
-- ============================================================================
-- This file contains all the SQL commands needed to set up the database
-- tables and permissions for the admin dashboard functionality.

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Users table (extends auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    subscription_status TEXT DEFAULT 'none',
    subscription_id TEXT,
    upload_count INTEGER DEFAULT 0,
    daily_upload_count INTEGER DEFAULT 0,
    last_upload_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    PRIMARY KEY (id)
);

-- Enable RLS on users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy for users to read their own data
CREATE POLICY "Users can view own data" ON public.users
    FOR SELECT USING (auth.uid() = id);

-- Policy for users to update their own data
CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Policy for admins to view all users
CREATE POLICY "Admins can view all users" ON public.users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Policy for admins to update all users
CREATE POLICY "Admins can update all users" ON public.users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================================================
-- Feedback table
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on feedback table
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

-- Policy for authenticated users to create feedback
CREATE POLICY "Anyone can create feedback" ON public.feedback
    FOR INSERT WITH CHECK (true);

-- Policy for users to view their own feedback
CREATE POLICY "Users can view own feedback" ON public.feedback
    FOR SELECT USING (user_id = auth.uid());

-- Policy for admins to view all feedback
CREATE POLICY "Admins can view all feedback" ON public.feedback
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================================================
-- Newsletter subscribers table
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.newsletter_subscribers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on newsletter_subscribers table
ALTER TABLE public.newsletter_subscribers ENABLE ROW LEVEL SECURITY;

-- Policy for anyone to subscribe to newsletter
CREATE POLICY "Anyone can subscribe to newsletter" ON public.newsletter_subscribers
    FOR INSERT WITH CHECK (true);

-- Policy for users to manage their own subscription
CREATE POLICY "Users can manage own subscription" ON public.newsletter_subscribers
    FOR ALL USING (email = (SELECT email FROM auth.users WHERE id = auth.uid()));

-- Policy for admins to view all subscribers
CREATE POLICY "Admins can view all subscribers" ON public.newsletter_subscribers
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================================================
-- Website content table (for testimonials and other content)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.website_content (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    type TEXT NOT NULL, -- 'testimonial', 'about', 'privacy', etc.
    title TEXT,
    content TEXT NOT NULL,
    author_name TEXT,
    author_email TEXT,
    author_title TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on website_content table
ALTER TABLE public.website_content ENABLE ROW LEVEL SECURITY;

-- Policy for anyone to view active content
CREATE POLICY "Anyone can view active content" ON public.website_content
    FOR SELECT USING (is_active = true);

-- Policy for admins to manage all content
CREATE POLICY "Admins can manage all content" ON public.website_content
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================================================
-- Page views table (for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.page_views (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    page_url TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on page_views table
ALTER TABLE public.page_views ENABLE ROW LEVEL SECURITY;

-- Policy for system to insert page views
CREATE POLICY "System can insert page views" ON public.page_views
    FOR INSERT WITH CHECK (true);

-- Policy for admins to view all page views
CREATE POLICY "Admins can view all page views" ON public.page_views
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================================================
-- User files table (for tracking uploads)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_files (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT,
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    file_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS on user_files table
ALTER TABLE public.user_files ENABLE ROW LEVEL SECURITY;

-- Policy for users to view their own files
CREATE POLICY "Users can view own files" ON public.user_files
    FOR SELECT USING (user_id = auth.uid());

-- Policy for users to insert their own files
CREATE POLICY "Users can insert own files" ON public.user_files
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Policy for admins to view all files
CREATE POLICY "Admins can view all files" ON public.user_files
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================================================
-- Indexes for better performance
-- ============================================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON public.users(is_admin);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON public.users(subscription_status);

-- Feedback table indexes
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_is_read ON public.feedback(is_read);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback(created_at);

-- Newsletter subscribers indexes
CREATE INDEX IF NOT EXISTS idx_newsletter_email ON public.newsletter_subscribers(email);
CREATE INDEX IF NOT EXISTS idx_newsletter_is_active ON public.newsletter_subscribers(is_active);

-- Website content indexes
CREATE INDEX IF NOT EXISTS idx_website_content_type ON public.website_content(type);
CREATE INDEX IF NOT EXISTS idx_website_content_is_active ON public.website_content(is_active);
CREATE INDEX IF NOT EXISTS idx_website_content_is_featured ON public.website_content(is_featured);

-- Page views indexes
CREATE INDEX IF NOT EXISTS idx_page_views_user_id ON public.page_views(user_id);
CREATE INDEX IF NOT EXISTS idx_page_views_created_at ON public.page_views(created_at);
CREATE INDEX IF NOT EXISTS idx_page_views_page_url ON public.page_views(page_url);

-- User files indexes
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON public.user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_processing_status ON public.user_files(processing_status);
CREATE INDEX IF NOT EXISTS idx_user_files_created_at ON public.user_files(created_at);

-- ============================================================================
-- Functions for automatic timestamp updates
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_updated_at 
    BEFORE UPDATE ON public.feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_newsletter_subscribers_updated_at 
    BEFORE UPDATE ON public.newsletter_subscribers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_website_content_updated_at 
    BEFORE UPDATE ON public.website_content 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_files_updated_at 
    BEFORE UPDATE ON public.user_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample data for testing (optional)
-- ============================================================================

-- Insert sample testimonials
INSERT INTO public.website_content (type, title, content, author_name, author_email, author_title, is_featured, display_order)
VALUES 
    ('testimonial', 'Amazing PDF Processing', 'ZapRead has transformed how I handle PDF documents. The text extraction is incredibly accurate and fast!', 'John Smith', 'john@example.com', 'Product Manager', true, 1),
    ('testimonial', 'Great User Experience', 'The interface is intuitive and the results are always reliable. Highly recommend for anyone working with PDFs.', 'Sarah Johnson', 'sarah@example.com', 'Designer', true, 2),
    ('testimonial', 'Efficient and Reliable', 'I process dozens of PDFs daily and ZapRead makes it effortless. The OCR capabilities are top-notch.', 'Michael Brown', 'michael@example.com', 'Data Analyst', false, 3)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Admin dashboard views (for easier querying)
-- ============================================================================

-- View for user statistics
CREATE OR REPLACE VIEW admin_user_stats AS
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN is_admin = true THEN 1 END) as admin_users,
    COUNT(CASE WHEN subscription_status != 'none' THEN 1 END) as paid_users,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as new_users_30_days,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_users_7_days
FROM public.users;

-- View for feedback statistics
CREATE OR REPLACE VIEW admin_feedback_stats AS
SELECT 
    COUNT(*) as total_feedback,
    COUNT(CASE WHEN is_read = false THEN 1 END) as unread_feedback,
    AVG(rating) as average_rating,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as feedback_30_days
FROM public.feedback;

-- View for newsletter statistics
CREATE OR REPLACE VIEW admin_newsletter_stats AS
SELECT 
    COUNT(*) as total_subscribers,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_subscribers,
    COUNT(CASE WHEN subscribed_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as new_subscribers_30_days
FROM public.newsletter_subscribers;

-- ============================================================================
-- Grant permissions to service role (for server-side operations)
-- ============================================================================

-- Note: These grants should be applied carefully in production
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
-- GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- ============================================================================
-- End of schema
-- ============================================================================ 