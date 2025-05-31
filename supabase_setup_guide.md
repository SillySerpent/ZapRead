# Supabase Setup Guide for ZapRead

This guide will help you set up the required database tables and configurations in your Supabase project.

## Prerequisites

- A Supabase account
- A Supabase project created for ZapRead
- Your Supabase URL and API key in your `.env` file

## Creating the Database Tables

Follow these steps to create the required tables:

1. **Log in to your Supabase Dashboard**: Go to [https://app.supabase.io/](https://app.supabase.io/) and sign in.

2. **Select your project**: Choose the project you're using for ZapRead.

3. **Open the SQL Editor**: In the left sidebar, click on "SQL Editor".

4. **Create a New Query**: Click "New Query" to create a new SQL query.

5. **Copy and Paste the SQL Script**: Copy the entire contents of the `supabase_tables.sql` file and paste it into the query editor.

6. **Run the Query**: Click the "Run" button to execute the script and create all the tables.

## Setting Up Authentication

1. **Configure Authentication**: In the Supabase dashboard, go to "Authentication" > "Settings".

2. **Enable Email Authentication**: Make sure email authentication is enabled.

3. **Disable Email Confirmation (Optional)**: If you're just testing, you might want to disable email confirmation by turning off "Enable email confirmations" in the Email Auth settings.

4. **Set Up Redirect URLs**: Add your application URL to the "Redirect URLs" list. For local development, add `http://localhost:5000`.

## Test Your Setup

After completing the setup, you can run the test script to verify everything is working:

```
python3 test/test_connections.py
```

If all tests pass, your Supabase configuration is correct!

## Database Schema Explanation

### `users` Table

This table extends the built-in `auth.users` table in Supabase and stores additional user information:

- `id`: UUID that references the auth.users table
- `email`: User's email address
- `created_at`: When the user record was created
- `updated_at`: When the user record was last updated
- `subscription_id`: Stripe subscription ID
- `subscription_status`: Current subscription status

### `file_history` Table

This table stores the history of files processed by each user:

- `id`: Unique identifier for the history record
- `user_id`: References the user who processed the file
- `original_filename`: Name of the original uploaded file
- `file_type`: Type of the file (TXT, PDF, DOCX)
- `processed_filename`: Name of the processed file
- `created_at`: When the record was created
- `updated_at`: When the record was last updated

## Row Level Security (RLS)

The SQL script sets up Row Level Security policies to ensure users can only access their own data:

- Users can only select and update their own user record
- Users can only select and insert their own file history records

## Automatic User Creation

A trigger is set up to automatically create a record in the `users` table whenever a new user signs up through Supabase authentication. 