# ZapRead - Bionic Reading Web App

ZapRead is a web application that enhances reading efficiency by applying bionic reading formatting to uploaded documents. It supports various file formats and integrates with Supabase for authentication and Stripe for subscription payments.

## Features

- **User Authentication**: Secure user registration and login with Supabase
- **File Upload**: Support for TXT, PDF, and DOCX files
- **Bionic Reading Processing**: Highlights the first few letters of each word to improve reading speed
- **Subscription Plans**: Integration with Stripe for premium subscription management
- **Document History**: Track and manage previously processed documents

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication & Database**: Supabase
- **Payments**: Stripe

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/zapread.git
   cd zapread
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your configuration:
   ```
   # Flask configuration
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key

   # Supabase configuration
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key

   # Stripe configuration
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
   STRIPE_PRICE_ID=your-stripe-price-id
   ```

## Supabase Setup

1. Create a new project on [Supabase](https://supabase.io/).
2. Set up the authentication service and enable email/password sign-in.
3. Create the following tables in your Supabase database:

   **users**
   ```sql
   CREATE TABLE users (
     id UUID REFERENCES auth.users PRIMARY KEY,
     email TEXT UNIQUE,
     subscription_id TEXT,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

   **file_history**
   ```sql
   CREATE TABLE file_history (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     user_id UUID REFERENCES users NOT NULL,
     original_filename TEXT NOT NULL,
     file_type TEXT NOT NULL,
     processed_filename TEXT NOT NULL,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

## Stripe Setup

1. Create a [Stripe](https://stripe.com/) account and get your API keys.
2. Create a subscription product and pricing plan.
3. Set up webhook endpoints to receive events from Stripe.

## Running the Application

1. Start the Flask development server:
   ```
   flask run
   ```

2. Open your browser and navigate to `http://127.0.0.1:5000/`.

## Running in Production

For production deployment, consider using Gunicorn as the WSGI server:

```
gunicorn app:app
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 