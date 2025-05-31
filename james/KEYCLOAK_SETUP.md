# Keycloak Authentication Setup Guide

## Overview
This guide explains how to set up Keycloak authentication for the PrtGist Analytics Dashboard.

## Prerequisites
1. A running Keycloak server
2. Admin access to Keycloak
3. Python packages installed (see requirements.txt)

## Environment Variables
Add these variables to your `.env` file:

```bash
# Keycloak Authentication Configuration
KEYCLOAK_SERVER_URL=https://your-keycloak-server.com
KEYCLOAK_REALM=your-realm-name
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_REDIRECT_URI=http://localhost:8501
```

## Keycloak Configuration Steps

### 1. Create a Realm
1. Log into Keycloak Admin Console
2. Create a new realm or use an existing one
3. Note the realm name for `KEYCLOAK_REALM`

### 2. Create a Client
1. Go to Clients → Create Client
2. Set Client ID (use this for `KEYCLOAK_CLIENT_ID`)
3. Set Client Type to "OpenID Connect"
4. Enable "Client authentication" if you want a confidential client
5. Set Valid Redirect URIs to your Streamlit app URL (e.g., `http://localhost:8501/*`)
6. Set Web Origins to `*` or your specific domain
7. Save the client

### 3. Configure Client Settings
1. In the client settings, go to the "Credentials" tab
2. Copy the Client Secret (use this for `KEYCLOAK_CLIENT_SECRET`)
3. In "Advanced Settings", ensure:
   - Proof Key for Code Exchange Code Challenge Method: S256
   - OAuth 2.0 Device Authorization Grant Enabled: OFF (unless needed)

### 4. Create Users (Optional)
1. Go to Users → Add User
2. Set username, email, first name, last name
3. Go to Credentials tab and set a password
4. Ensure "Temporary" is OFF if you want a permanent password

## Security Features Implemented

### 1. PKCE (Proof Key for Code Exchange)
- Protects against authorization code interception attacks
- Uses SHA256 code challenge method
- Automatically generates code verifier and challenge

### 2. State Parameter
- Prevents CSRF attacks
- Validates that the authorization response matches the request

### 3. Token Validation
- Validates JWT tokens using Keycloak's public keys
- Checks token expiration, audience, and issuer
- Automatic token refresh (if refresh tokens are enabled)

### 4. Secure Session Management
- Stores tokens securely in Streamlit session state
- Automatic session cleanup on logout
- Token validation on each request

## Usage in Your Application

### Basic Integration
```python
from src.auth.keycloak_auth import KeycloakAuth, require_authentication, render_user_info

# Initialize Keycloak auth
auth = KeycloakAuth()

# Require authentication for the entire app
user_info = require_authentication(auth)

# Render user info in sidebar
render_user_info(auth)
```

### Advanced Usage
```python
# Check if user is authenticated
if auth.is_authenticated():
    user_info = auth.get_current_user()
    st.write(f"Welcome, {user_info['name']}!")
else:
    st.write("Please log in")

# Manual logout
if st.button("Logout"):
    auth.clear_session()
    st.rerun()
```

## Troubleshooting

### Common Issues

1. **"Missing required Keycloak environment variables"**
   - Ensure all required environment variables are set in your `.env` file

2. **"Invalid redirect URI"**
   - Check that the redirect URI in Keycloak client matches `KEYCLOAK_REDIRECT_URI`
   - Ensure the URI includes the protocol (http/https)

3. **"Token validation failed"**
   - Verify the Keycloak server URL is correct and accessible
   - Check that the realm name is correct
   - Ensure the client ID matches the one in Keycloak

4. **"CORS errors"**
   - Set Web Origins in Keycloak client to `*` or your specific domain
   - Ensure the Keycloak server allows cross-origin requests

### Debug Mode
To enable debug logging, add this to your Streamlit app:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Client Secret**: Keep client secrets secure and rotate them regularly
3. **Token Expiration**: Configure appropriate token lifetimes in Keycloak
4. **User Roles**: Implement role-based access control if needed
5. **Monitoring**: Monitor authentication failures and token usage

## Example Keycloak Client Configuration

```json
{
  "clientId": "gist-analytics",
  "name": "Gist Analytics Dashboard",
  "description": "Analytics dashboard for Gist data",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "redirectUris": ["http://localhost:8501/*"],
  "webOrigins": ["*"],
  "protocol": "openid-connect",
  "attributes": {
    "pkce.code.challenge.method": "S256"
  }
}
``` 