# Supabase External Database Management Guide

This guide explains how to manage your Supabase database from external tools like pgAdmin, DBeaver, or directly from your IDE.

## 🔧 Database Connection Information

### Getting Your Connection Details

1. **Go to your Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project: `ZapRead`

2. **Navigate to Settings → Database**
   - Find the "Connection info" section
   - You'll need these details:
     - Host
     - Database name
     - Port (usually 5432)
     - User
     - Password (use your database password, not project password)

### Connection String Format
```postgresql://[username]:[password]@[host]:[port]/[database]?sslmode=require
```

Example:
```
postgresql://postgres:your_password@db.abc123xyz.supabase.co:5432/postgres?sslmode=require
```

## 🛠️ External Database Management Tools

### Option 1: pgAdmin (Recommended for PostgreSQL)

**Installation:**
```bash
# macOS with Homebrew
brew install --cask pgadmin4

# Or download from: https://www.pgadmin.org/download/
```

**Setup:**
1. Open pgAdmin
2. Right-click "Servers" → "Create" → "Server"
3. **General Tab:**
   - Name: `ZapRead Supabase`
4. **Connection Tab:**
   - Host: `db.your-project-ref.supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - Username: `postgres`
   - Password: `[your-database-password]`
5. **SSL Tab:**
   - SSL Mode: `Require`

### Option 2: DBeaver (Universal Database Tool)

**Installation:**
```bash
# macOS with Homebrew
brew install --cask dbeaver-community

# Or download from: https://dbeaver.io/download/
```

**Setup:**
1. Open DBeaver
2. Click "New Database Connection" (plug icon)
3. Select "PostgreSQL"
4. Fill in connection details:
   - Server Host: `db.your-project-ref.supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - Username: `postgres`
   - Password: `[your-database-password]`
5. **SSL Tab:**
   - Use SSL: `Yes`
   - SSL Mode: `require`

### Option 3: TablePlus (macOS/iOS)

**Installation:**
```bash
# macOS with Homebrew
brew install --cask tableplus

# Or download from: https://tableplus.com/
```

**Setup:**
1. Open TablePlus
2. Click "+" to create new connection
3. Select "PostgreSQL"
4. Fill in connection details
5. Enable SSL

### Option 4: VS Code Extensions

**Installation:**
1. Install "PostgreSQL" extension by Chris Kolkman
2. Or install "SQLTools" extension

**Setup with SQLTools:**
1. Install "SQLTools PostgreSQL/Cockroach Driver"
2. Open Command Palette (`Cmd+Shift+P`)
3. Run "SQLTools: Add New Connection"
4. Select "PostgreSQL"
5. Fill in connection details

## 📝 Database Schema Setup

### Step 1: Apply the Schema

1. **Using pgAdmin/DBeaver:**
   - Open the query editor
   - Copy the contents of `supabase_admin_schema.sql`
   - Execute the script

2. **Using Command Line:**
   ```bash
   # Install PostgreSQL client tools
   brew install postgresql
   
   # Apply schema
   psql "postgresql://postgres:your_password@db.abc123xyz.supabase.co:5432/postgres?sslmode=require" -f supabase_admin_schema.sql
   ```

3. **Using Supabase SQL Editor:**
   - Go to Supabase Dashboard → SQL Editor
   - Paste the schema and run

### Step 2: Verify Schema

Run this query to verify your tables exist:
```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

Expected tables:
- `users`
- `feedback`
- `newsletter_subscribers`
- `website_content`
- `page_views`
- `user_files`

## 🔐 Setting Up Admin User

### Method 1: Using the make_admin.py Script

```bash
# Make sure you're in the project directory
cd /Users/JosephAyleshaa/Desktop/ZapRead

# Activate virtual environment
source .venv/bin/activate

# Check current admin users
python make_admin.py --list

# Make a user admin (replace with actual email)
python make_admin.py your-email@example.com
```

### Method 2: Direct SQL (if you have registered user)

```sql
-- First, find your user ID from auth.users
SELECT id, email FROM auth.users WHERE email = 'your-email@example.com';

-- Insert/update in users table
INSERT INTO public.users (id, email, is_admin, subscription_status)
VALUES ('user-id-from-above', 'your-email@example.com', true, 'none')
ON CONFLICT (id) DO UPDATE SET is_admin = true;
```

## 📊 Useful Admin Queries

### User Statistics
```sql
-- Get overview stats
SELECT * FROM admin_user_stats;

-- Detailed user list
SELECT 
    u.email,
    u.is_admin,
    u.subscription_status,
    u.created_at,
    COUNT(f.id) as total_files
FROM users u
LEFT JOIN user_files f ON u.id = f.user_id
GROUP BY u.id, u.email, u.is_admin, u.subscription_status, u.created_at
ORDER BY u.created_at DESC;
```

### Feedback Management
```sql
-- Get unread feedback
SELECT * FROM feedback WHERE is_read = false ORDER BY created_at DESC;

-- Mark feedback as read
UPDATE feedback SET is_read = true WHERE id = 'feedback-id';
```

### Newsletter Management
```sql
-- Get active subscribers
SELECT * FROM newsletter_subscribers WHERE is_active = true;

-- Get subscriber count
SELECT COUNT(*) as total_subscribers FROM newsletter_subscribers WHERE is_active = true;
```

### Content Management
```sql
-- Get all testimonials
SELECT * FROM website_content WHERE type = 'testimonial' ORDER BY display_order;

-- Add new testimonial
INSERT INTO website_content (type, title, content, author_name, author_email, author_title, is_featured)
VALUES ('testimonial', 'Great Service', 'Amazing experience!', 'John Doe', 'john@example.com', 'Customer', false);
```

## 🔍 Monitoring and Analytics

### Page Views Analytics
```sql
-- Most popular pages
SELECT 
    page_url, 
    COUNT(*) as views,
    COUNT(DISTINCT user_id) as unique_users
FROM page_views 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY page_url 
ORDER BY views DESC;
```

### User Activity
```sql
-- Recent user activity
SELECT 
    u.email,
    COUNT(pv.id) as page_views,
    COUNT(uf.id) as file_uploads,
    MAX(pv.created_at) as last_activity
FROM users u
LEFT JOIN page_views pv ON u.id = pv.user_id
LEFT JOIN user_files uf ON u.id = uf.user_id
WHERE u.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.id, u.email
ORDER BY last_activity DESC;
```

## 🚨 Security Best Practices

### 1. Row Level Security (RLS)
- All tables have RLS enabled
- Policies ensure users can only access their own data
- Admins can access all data when authenticated

### 2. Connection Security
- Always use SSL connections (`sslmode=require`)
- Use strong database passwords
- Consider IP allowlisting in production

### 3. Backup Strategy
```sql
-- Create backup (run locally)
pg_dump "postgresql://postgres:password@host:5432/postgres?sslmode=require" > backup.sql

-- Restore backup
psql "postgresql://postgres:password@host:5432/postgres?sslmode=require" < backup.sql
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused:**
   - Check if database is paused (Supabase dashboard)
   - Verify connection string
   - Check SSL settings

2. **Permission Denied:**
   - Verify user has correct permissions
   - Check RLS policies
   - Ensure admin status is set correctly

3. **Table Not Found:**
   - Run the schema script
   - Check table exists in correct schema (public)

### Debug Queries

```sql
-- Check if user is admin
SELECT id, email, is_admin FROM users WHERE email = 'your-email@example.com';

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'users';

-- Check table permissions
SELECT * FROM information_schema.table_privileges WHERE table_name = 'users';
```

## 📚 Additional Resources

- [Supabase Database Documentation](https://supabase.com/docs/guides/database)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
- [DBeaver Documentation](https://dbeaver.io/docs/)

## 🔄 Regular Maintenance Tasks

### Weekly
- Review new user registrations
- Check unread feedback
- Monitor page view analytics

### Monthly
- Review testimonials and website content
- Analyze user engagement metrics
- Check for inactive newsletter subscribers

### As Needed
- Add new admin users
- Update testimonials
- Send newsletters
- Respond to feedback 