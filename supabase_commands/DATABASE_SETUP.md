# ZapRead Database Setup Guide

This document provides instructions for setting up the necessary database tables in Supabase for the ZapRead application.

## Required Tables

The ZapRead application requires the following database tables:

1. `newsletter_subscribers` - For storing newsletter subscribers
2. `feedback` - For storing user feedback submissions
3. `page_views` - For tracking page views and analytics
4. `website_content` - For storing dynamic website content
5. `users` - Automatically created by Supabase Auth
6. `file_history` - For storing user document processing history

## Setup Instructions

### Option 1: Using the SQL Editor in Supabase Dashboard

1. Log in to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy the contents of the `database_setup.sql` file
4. Paste the SQL into the editor
5. Click "Run" to execute the SQL and create all tables

### Option 2: Using Individual SQL Files

If you prefer to create tables one by one:

1. Execute `newsletter_subscribers_table.sql`
2. Execute `feedback_table.sql`
3. Execute `page_views_table.sql`
4. Execute `website_content_table.sql`

## Verifying Setup

After running the SQL scripts, you should be able to:

1. View all tables in the Supabase Table Editor
2. Access the ZapRead admin dashboard without errors
3. See default testimonials on the home page

## Troubleshooting

If you encounter errors:

- Ensure the UUID extension is enabled
- Check that the auth.users table exists (created by Supabase Auth)
- Verify all tables have been created with the correct structure

For additional help, please refer to the Supabase documentation or contact support. 