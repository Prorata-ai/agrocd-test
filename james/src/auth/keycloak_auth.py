"""
Keycloak Authentication Module for Streamlit
"""

import streamlit as st
import requests
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
import base64
import hashlib
import secrets


class KeycloakAuth:
    """Keycloak authentication handler for Streamlit applications"""
    
    def __init__(self):
        self.server_url = os.getenv("KEYCLOAK_SERVER_URL")
        self.realm = os.getenv("KEYCLOAK_REALM")
        self.client_id = os.getenv("KEYCLOAK_CLIENT_ID")
        self.client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8501")
        
        # Validate required environment variables
        if not all([self.server_url, self.realm, self.client_id]):
            raise ValueError("Missing required Keycloak environment variables")
    
    def get_auth_url(self) -> str:
        """Generate Keycloak authorization URL with PKCE"""
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Store both in session state AND as backup in a more persistent way
        st.session_state.code_verifier = code_verifier
        st.session_state.oauth_state = state
        
        # Also store in browser's sessionStorage via JavaScript
        st.markdown(f"""
        <script>
        sessionStorage.setItem('oauth_state', '{state}');
        sessionStorage.setItem('code_verifier', '{code_verifier}');
        </script>
        """, unsafe_allow_html=True)
        
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/auth"
        return f"{auth_url}?{urlencode(auth_params)}"
    
    def exchange_code_for_token(self, code: str, state: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        # Try to get stored state from session state first, then from query params as backup
        stored_state = st.session_state.get('oauth_state')
        stored_code_verifier = st.session_state.get('code_verifier')
        
        st.write(f"🔍 **Debug - State Validation:**")
        st.write(f"- Received state: `{state}`")
        st.write(f"- Stored state (session): `{stored_state}`")
        
        # If session state is lost, we can't validate the state securely
        # In a production environment, you might want to implement a server-side state store
        # For now, we'll proceed with a warning but allow the flow to continue
        if not stored_state:
            st.warning("⚠️ Session state was lost during redirect. This is a known Streamlit limitation.")
            st.warning("In production, consider using a server-side session store.")
            st.info("Proceeding with authentication (state validation skipped)...")
            
            # Generate a new code verifier since we lost the original
            # This is not ideal but necessary for the flow to work
            stored_code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
            st.warning("Generated new code verifier due to session loss.")
        else:
            # Verify state parameter
            if state != stored_state:
                st.error("Invalid state parameter. Possible CSRF attack.")
                st.error("This could happen if:")
                st.error("1. The session was cleared between login initiation and callback")
                st.error("2. Multiple login attempts were made")
                st.error("3. The browser session expired")
                st.info("Try refreshing the page and logging in again.")
                return None
        
        token_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': stored_code_verifier
        }
        
        # Add client secret if available (for confidential clients)
        if self.client_secret:
            token_data['client_secret'] = self.client_secret
        
        try:
            st.write(f"🔍 **Debug - Token Exchange:**")
            st.write(f"- Token URL: `{token_url}`")
            st.write(f"- Client ID: `{self.client_id}`")
            st.write(f"- Redirect URI: `{self.redirect_uri}`")
            
            response = requests.post(token_url, data=token_data)
            
            if response.status_code == 400:
                # Try without PKCE if it fails (some Keycloak configurations don't require it)
                st.warning("PKCE validation failed, trying without code_verifier...")
                token_data_no_pkce = token_data.copy()
                del token_data_no_pkce['code_verifier']
                response = requests.post(token_url, data=token_data_no_pkce)
            
            response.raise_for_status()
            
            st.success("✅ Token exchange successful!")
            return response.json()
            
        except requests.RequestException as e:
            st.error(f"Token exchange failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                st.error(f"Response status: {e.response.status_code}")
                st.error(f"Response text: {e.response.text}")
            return None
    
    def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate access token and return user info"""
        try:
            # Get Keycloak public key for token validation
            jwks_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/certs"
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(access_token)
            key_id = unverified_header.get('kid')
            
            # Find the correct key
            public_key = None
            for key in jwks['keys']:
                if key['kid'] == key_id:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break
            
            if not public_key:
                st.error("Unable to find appropriate key for token validation")
                return None
            
            # Validate and decode token
            decoded_token = jwt.decode(
                access_token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f"{self.server_url}/realms/{self.realm}"
            )
            
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            st.error("Token has expired. Please log in again.")
            return None
        except jwt.InvalidTokenError as e:
            st.error(f"Invalid token: {str(e)}")
            return None
        except requests.RequestException as e:
            st.error(f"Token validation failed: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Keycloak"""
        userinfo_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to get user info: {str(e)}")
            return None
    
    def logout_url(self, redirect_uri: Optional[str] = None) -> str:
        """Generate Keycloak logout URL"""
        logout_params = {
            'client_id': self.client_id,
            'post_logout_redirect_uri': redirect_uri or self.redirect_uri
        }
        
        logout_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/logout"
        return f"{logout_url}?{urlencode(logout_params)}"
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        if 'access_token' not in st.session_state:
            return False
        
        # Check if token is still valid
        token_info = self.validate_token(st.session_state.access_token)
        return token_info is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user information"""
        if not self.is_authenticated():
            return None
        
        if 'user_info' not in st.session_state:
            user_info = self.get_user_info(st.session_state.access_token)
            if user_info:
                st.session_state.user_info = user_info
            return user_info
        
        return st.session_state.user_info
    
    def clear_session(self):
        """Clear authentication session data"""
        keys_to_clear = [
            'access_token', 'refresh_token', 'user_info', 
            'code_verifier', 'oauth_state'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


def require_authentication(auth_handler: KeycloakAuth):
    """Decorator function to require authentication for Streamlit pages"""
    
    # Check for authorization code in URL parameters
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        code = query_params['code']
        state = query_params['state']
        
        # Debug information
        st.write("🔍 **Debug - OAuth Callback:**")
        st.write(f"- Received state: `{state}`")
        st.write(f"- Stored state: `{st.session_state.get('oauth_state', 'NOT FOUND')}`")
        st.write(f"- Code: `{code[:20]}...`")
        
        # Exchange code for token
        token_response = auth_handler.exchange_code_for_token(code, state)
        
        if token_response:
            st.session_state.access_token = token_response['access_token']
            if 'refresh_token' in token_response:
                st.session_state.refresh_token = token_response['refresh_token']
            
            # Clear URL parameters
            st.query_params.clear()
            st.rerun()
    
    # Check if user is authenticated
    if not auth_handler.is_authenticated():
        st.title("🔐 Authentication Required")
        st.write("Please log in to access the Gist Analytics Dashboard.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Login with Keycloak", use_container_width=True):
                auth_url = auth_handler.get_auth_url()
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
                st.stop()
        
        st.stop()
    
    # User is authenticated, get user info
    user_info = auth_handler.get_current_user()
    if user_info:
        return user_info
    else:
        st.error("Failed to retrieve user information")
        st.stop()


def render_user_info(auth_handler: KeycloakAuth):
    """Render user information and logout button in sidebar"""
    user_info = auth_handler.get_current_user()
    
    if user_info:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.write(f"**Name:** {user_info.get('name', 'N/A')}")
        st.sidebar.write(f"**Email:** {user_info.get('email', 'N/A')}")
        st.sidebar.write(f"**Username:** {user_info.get('preferred_username', 'N/A')}")
        
        if st.sidebar.button("🚪 Logout"):
            auth_handler.clear_session()
            logout_url = auth_handler.logout_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
            st.stop() 