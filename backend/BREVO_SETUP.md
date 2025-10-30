# Brevo Email Setup for Production

This guide explains how to set up Brevo (formerly Sendinblue) Transactional API for sending emails in production on Railway.

## Overview

The application uses a factory pattern to automatically select the appropriate email sender:
- **Development**: `ConsoleEmailSender` - prints emails to console
- **Production**: `BrevoEmailSender` - sends real emails via Brevo API

## Prerequisites

1. A Brevo account (free tier available at https://www.brevo.com)
2. A verified sender email address in Brevo
3. Railway account with your project deployed

## Step 1: Set Up Brevo Account

1. **Create Account**
   - Go to https://www.brevo.com
   - Sign up for a free account
   - Verify your email address

2. **Get API Key**
   - Log in to your Brevo dashboard
   - Go to **Settings** → **SMTP & API** → **API Keys**
   - Click **Generate a new API key**
   - Give it a name (e.g., "polito-log-production")
   - Copy the API key (you won't be able to see it again!)

3. **Verify Sender Email**
   - Go to **Senders** → **Add a new sender**
   - Add your sender email (e.g., noreply@polito-log.com)
   - Complete the verification process
   - Note: For custom domains, you'll need to verify DNS records

## Step 2: Configure Railway Secrets

Railway provides a secure way to store sensitive environment variables:

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Navigate to your polito-log project
   - Select your backend service

2. **Add Environment Variables**
   - Go to the **Variables** tab
   - Add the following variables:

   ```
   ENVIRONMENT=production
   BREVO_API_KEY=your-brevo-api-key-here
   BREVO_SENDER_EMAIL=noreply@polito-log.com
   BREVO_SENDER_NAME=Polito-Log
   ```

   Replace the values with your actual configuration.

3. **Deploy**
   - Railway will automatically redeploy with the new environment variables
   - The application will now use BrevoEmailSender for all emails

## Step 3: Verify Setup

1. **Check Logs**
   - After deployment, check Railway logs
   - You should see: `"Using BrevoEmailSender for production email delivery"`
   - If you see console sender, check that ENVIRONMENT=production and BREVO_API_KEY is set

2. **Test Magic Link**
   - Try logging in through your frontend
   - Check your email inbox for the magic link
   - Check Brevo dashboard → Statistics → Email to see delivery status

## Email Template

The magic link emails include:
- Professional HTML template with styling
- Plain text fallback for email clients that don't support HTML
- 15-minute expiration notice
- Security notice about ignoring unsolicited emails

## Troubleshooting

### Emails Not Sending

1. **Check API Key**
   - Verify BREVO_API_KEY is set in Railway
   - Verify the API key is correct in Brevo dashboard
   - Ensure the key has "Send transactional emails" permission

2. **Check Sender Email**
   - Verify the sender email in Brevo dashboard
   - For custom domains, verify DNS records are configured

3. **Check Logs**
   ```bash
   # In Railway dashboard, view logs for error messages
   # Look for Brevo API errors or exceptions
   ```

4. **Check Brevo Dashboard**
   - Go to **Statistics** → **Email**
   - Check for bounces or blocked emails
   - View detailed delivery reports

### Rate Limits

Brevo free tier limits:
- 300 emails per day
- 9,000 emails per month

For higher limits, upgrade to a paid plan.

## Development vs Production

The application automatically detects the environment:

| Environment | Email Sender | Requires API Key |
|-------------|-------------|------------------|
| development | ConsoleEmailSender | No |
| production (with BREVO_API_KEY) | BrevoEmailSender | Yes |
| production (without BREVO_API_KEY) | ConsoleEmailSender | No |

## Security Best Practices

1. **Never commit API keys** - Always use environment variables
2. **Use Railway secrets** - Store sensitive data in Railway's secure variable storage
3. **Rotate API keys** - Periodically generate new API keys in Brevo
4. **Monitor usage** - Check Brevo dashboard for unusual activity
5. **Verify sender domain** - Use proper DNS configuration for custom domains

## Additional Resources

- [Brevo API Documentation](https://developers.brevo.com/)
- [Brevo Python SDK](https://github.com/sendinblue/APIv3-python-library)
- [Railway Environment Variables](https://docs.railway.app/guides/variables)

## Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify Brevo dashboard for delivery status
3. Review this setup guide
4. Check Brevo API status page
