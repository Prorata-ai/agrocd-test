"""
Simplified Keycloak Authentication Module for Streamlit (Development)
This version works around Streamlit's session state limitations during redirects.
"""

import streamlit as st
import requests
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import base64
import hashlib
import secrets


class SimpleKeycloakAuth:
    """Simplified Keycloak authentication handler for Streamlit applications"""
    
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
        """Generate Keycloak authorization URL (simplified, no PKCE)"""
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email'
        }
        
        auth_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/auth"
        return f"{auth_url}?{urlencode(auth_params)}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token (simplified)"""
        token_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        # Add client secret if available (for confidential clients)
        if self.client_secret:
            token_data['client_secret'] = self.client_secret
        
        try:
            st.write(f"🔍 **Debug - Token Exchange:**")
            st.write(f"- Token URL: `{token_url}`")
            st.write(f"- Client ID: `{self.client_id}`")
            st.write(f"- Redirect URI: `{self.redirect_uri}`")
            st.write(f"- Grant Type: `{token_data['grant_type']}`")
            st.write(f"- Using Client Secret: `{bool(self.client_secret)}`")
            
            response = requests.post(token_url, data=token_data, timeout=10)
            
            # Log response details
            st.write(f"- Response Status: `{response.status_code}`")
            
            if response.status_code == 200:
                st.success("✅ Token exchange successful!")
                return response.json()
            else:
                # Handle specific error cases
                try:
                    error_data = response.json()
                    error_type = error_data.get('error', 'unknown_error')
                    error_description = error_data.get('error_description', 'No description provided')
                    
                    st.error(f"❌ Token exchange failed: `{error_type}`")
                    st.error(f"📝 Description: `{error_description}`")
                    
                    # Provide specific guidance based on error type
                    if error_type == 'invalid_grant':
                        if 'code' in error_description.lower():
                            st.warning("🔄 **Authorization code expired or already used**")
                            st.info("This is normal - authorization codes can only be used once and expire quickly.")
                            st.info("Please click 'Try Again' to get a fresh authorization code.")
                        else:
                            st.warning("🔧 **Grant type issue**")
                            st.info("There might be a configuration mismatch between the client and server.")
                    elif error_type == 'invalid_client':
                        st.warning("🔧 **Client configuration issue**")
                        st.info("Check your KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET settings.")
                    elif error_type == 'invalid_request':
                        st.warning("🔧 **Request format issue**")
                        st.info("Check your KEYCLOAK_REDIRECT_URI setting.")
                    
                except ValueError:
                    # Response is not JSON
                    st.error(f"❌ Token exchange failed with status {response.status_code}")
                    st.error(f"📝 Response: `{response.text[:200]}...`")
                
                return None
            
        except requests.Timeout:
            st.error("⏱️ Token exchange timed out. Please try again.")
            return None
        except requests.ConnectionError:
            st.error("🌐 Connection error. Please check your network and Keycloak server URL.")
            return None
        except requests.RequestException as e:
            st.error(f"🔧 Token exchange failed: {str(e)}")
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
    
    def get_user_roles(self, access_token: str) -> Optional[list]:
        """Extract user roles from access token"""
        try:
            # Decode token without verification to get roles (we already validated it during exchange)
            decoded_token = jwt.decode(access_token, options={"verify_signature": False})
            
            # Keycloak stores roles in different places depending on configuration
            roles = []
            
            # Check realm roles
            if 'realm_access' in decoded_token and 'roles' in decoded_token['realm_access']:
                roles.extend(decoded_token['realm_access']['roles'])
            
            # Check client roles for our specific client
            if 'resource_access' in decoded_token and self.client_id in decoded_token['resource_access']:
                client_roles = decoded_token['resource_access'][self.client_id].get('roles', [])
                roles.extend(client_roles)
            
            # Also check for roles in the top level (some configurations put them there)
            if 'roles' in decoded_token:
                if isinstance(decoded_token['roles'], list):
                    roles.extend(decoded_token['roles'])
            
            return list(set(roles))  # Remove duplicates
            
        except Exception as e:
            st.error(f"Failed to extract roles from token: {str(e)}")
            return None
    
    def has_required_role(self, access_token: str, required_role: str = "gist-analyst") -> bool:
        """Check if user has the required role"""
        roles = self.get_user_roles(access_token)
        if roles is None:
            return False
        
        return required_role in roles
    
    def check_user_authorization(self, access_token: str, user_info: Dict[str, Any]) -> bool:
        """Check if user is authorized to access the dashboard"""
        # Get user roles
        roles = self.get_user_roles(access_token)
        
        if roles is None:
            st.error("❌ Unable to retrieve user roles")
            return False
        
        # Check for required role
        required_role = "gist-analyst"
        has_role = required_role in roles
        
        # Display role information
        st.write("🔍 **Authorization Check:**")
        st.write(f"- User: `{user_info.get('preferred_username', 'Unknown')}`")
        st.write(f"- Required Role: `{required_role}`")
        st.write(f"- User Roles: `{', '.join(roles) if roles else 'None'}`")
        st.write(f"- Access Granted: `{has_role}`")
        
        if not has_role:
            st.error(f"❌ **Access Denied**")
            st.error(f"You need the `{required_role}` role to access this dashboard.")
            st.info("**What to do:**")
            st.info("1. Contact your administrator to assign the required role")
            st.info("2. Make sure you're logged in with the correct account")
            st.info("3. Try logging out and back in if roles were recently updated")
            
            # Show logout button
            if st.button("🚪 Logout and Try Different Account"):
                self.clear_session()
                logout_url = self.logout_url()
                st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
                st.stop()
            
            return False
        
        st.success(f"✅ **Access Granted** - You have the required `{required_role}` role")
        return True
    
    def logout_url(self, redirect_uri: Optional[str] = None) -> str:
        """Generate Keycloak logout URL"""
        logout_params = {
            'client_id': self.client_id,
            'post_logout_redirect_uri': redirect_uri or self.redirect_uri
        }
        
        logout_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/logout"
        return f"{logout_url}?{urlencode(logout_params)}"
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated and authorized"""
        return (
            'access_token' in st.session_state and 
            'user_info' in st.session_state and
            'user_authorized' in st.session_state and
            st.session_state.user_authorized
        )
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user information"""
        return st.session_state.get('user_info')
    
    def clear_session(self):
        """Clear authentication session data"""
        keys_to_clear = ['access_token', 'refresh_token', 'user_info', 'user_authorized']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


def simple_require_authentication(auth_handler: SimpleKeycloakAuth):
    """Simplified authentication requirement function"""
    
    # Check for authorization code in URL parameters
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        
        # Check if we've already processed this code
        if st.session_state.get('processed_code') == code:
            st.info("🔄 Code already processed, redirecting...")
            st.query_params.clear()
            st.rerun()
            return
        
        st.write("🔍 **Debug - OAuth Callback:**")
        st.write(f"- Received code: `{code[:20]}...`")
        st.write(f"- Code length: `{len(code)}`")
        st.write(f"- Current time: `{datetime.now()}`")
        
        # Exchange code for token
        token_response = auth_handler.exchange_code_for_token(code)
        
        if token_response:
            # Mark this code as processed
            st.session_state.processed_code = code
            
            st.session_state.access_token = token_response['access_token']
            if 'refresh_token' in token_response:
                st.session_state.refresh_token = token_response['refresh_token']
            
            # Get user info
            user_info = auth_handler.get_user_info(token_response['access_token'])
            if user_info:
                st.session_state.user_info = user_info
                st.success(f"✅ Successfully authenticated as {user_info.get('name', user_info.get('preferred_username', 'User'))}")
                
                # Check user authorization
                if auth_handler.check_user_authorization(token_response['access_token'], user_info):
                    # User is authorized, store authorization status
                    st.session_state.user_authorized = True
                    # Clear URL parameters and redirect
                    st.query_params.clear()
                    st.rerun()
                else:
                    # User is not authorized, clear session and stop
                    auth_handler.clear_session()
                    st.stop()
            else:
                st.error("Failed to retrieve user information")
                st.stop()
        else:
            st.error("❌ Authentication failed. Please try again.")
            st.info("💡 **Troubleshooting tips:**")
            st.info("1. **Refresh the page** and try logging in again")
            st.info("2. **Clear your browser cache** and cookies")
            st.info("3. **Try in an incognito/private window**")
            st.info("4. **Wait a few seconds** before trying again")
            
            # Clear the failed code from URL
            if st.button("🔄 Try Again"):
                st.query_params.clear()
                st.rerun()
            
            st.stop()
    
    # Check if user is authenticated
    if not auth_handler.is_authenticated():
        st.title("🔐 Authentication Required")
        st.write("Please log in to access the Gist Analytics Dashboard.")
        
        # Show current configuration for debugging
        with st.expander("🔧 Debug Information", expanded=False):
            st.write("**Current Configuration:**")
            st.write(f"- Server URL: `{auth_handler.server_url}`")
            st.write(f"- Realm: `{auth_handler.realm}`")
            st.write(f"- Client ID: `{auth_handler.client_id}`")
            st.write(f"- Redirect URI: `{auth_handler.redirect_uri}`")
            st.write(f"- Has Client Secret: `{bool(auth_handler.client_secret)}`")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Login with Keycloak", use_container_width=True):
                # Clear any previous session data
                auth_handler.clear_session()
                if 'processed_code' in st.session_state:
                    del st.session_state['processed_code']
                
                auth_url = auth_handler.get_auth_url()
                st.write(f"🔍 **Redirecting to:** {auth_url}")
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


def simple_render_user_info(auth_handler: SimpleKeycloakAuth):
    """Render user information and logout button in sidebar"""
    user_info = auth_handler.get_current_user()
    
    if user_info:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.write(f"**Name:** {user_info.get('name', 'N/A')}")
        st.sidebar.write(f"**Email:** {user_info.get('email', 'N/A')}")
        st.sidebar.write(f"**Username:** {user_info.get('preferred_username', 'N/A')}")
        
        # Show user roles
        if 'access_token' in st.session_state:
            roles = auth_handler.get_user_roles(st.session_state.access_token)
            if roles:
                st.sidebar.write(f"**Roles:** {', '.join(roles)}")
            else:
                st.sidebar.write("**Roles:** None")
        
        if st.sidebar.button("🚪 Logout"):
            auth_handler.clear_session()
            logout_url = auth_handler.logout_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
            st.stop() 