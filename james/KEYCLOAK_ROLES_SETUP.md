# Keycloak Role-Based Access Control Setup

This guide explains how to set up the `gist-analyst` role in Keycloak to control access to the Gist Analytics Dashboard.

## Overview

The dashboard now requires users to have the `gist-analyst` role to access the analytics features. This provides fine-grained access control and ensures only authorized personnel can view sensitive analytics data.

## Setting Up the Role

### Option 1: Realm Role (Recommended)

1. **Access Keycloak Admin Console**
   - Navigate to your Keycloak admin console
   - Select your realm (e.g., `prorata`)

2. **Create the Role**
   - Go to **Realm Settings** → **Roles**
   - Click **Create Role**
   - Set **Role Name**: `gist-analyst`
   - Set **Description**: `Access to Gist Analytics Dashboard`
   - Click **Save**

3. **Assign Role to Users**
   - Go to **Users** → Select a user
   - Go to **Role Mappings** tab
   - Under **Available Roles**, find `gist-analyst`
   - Click **Assign** to add the role to the user

### Option 2: Client Role

1. **Access Client Settings**
   - Go to **Clients** → Select your client (e.g., `gistdash`)
   - Go to **Roles** tab

2. **Create Client Role**
   - Click **Create Role**
   - Set **Role Name**: `gist-analyst`
   - Set **Description**: `Access to Gist Analytics Dashboard`
   - Click **Save**

3. **Assign Client Role to Users**
   - Go to **Users** → Select a user
   - Go to **Role Mappings** tab
   - Select your client from **Client Roles** dropdown
   - Find `gist-analyst` and click **Assign**

## Role Verification

The dashboard will automatically:

1. **Extract roles** from the JWT access token
2. **Check for the `gist-analyst` role** in:
   - Realm roles (`realm_access.roles`)
   - Client roles (`resource_access.{client_id}.roles`)
   - Top-level roles (some configurations)
3. **Display role information** during login for transparency
4. **Grant or deny access** based on role presence

## User Experience

### Successful Access
- User sees: ✅ **Access Granted** - You have the required `gist-analyst` role
- Dashboard loads normally
- User roles are displayed in the sidebar

### Access Denied
- User sees: ❌ **Access Denied** - You need the `gist-analyst` role
- Clear instructions on what to do next
- Option to logout and try a different account

## Troubleshooting

### User Can't Access Dashboard

1. **Check Role Assignment**
   ```
   Keycloak Admin → Users → [Username] → Role Mappings
   ```
   Verify `gist-analyst` is listed under assigned roles

2. **Check Role Scope**
   - If using client roles, ensure the role is assigned to the correct client
   - If using realm roles, verify the role exists in the correct realm

3. **Token Refresh**
   - Have user logout and login again
   - Roles are embedded in JWT tokens at login time

### Role Not Appearing in Dashboard

1. **Check Token Configuration**
   - Ensure client is configured to include roles in tokens
   - Go to **Clients** → [Your Client] → **Client Scopes**
   - Verify `roles` scope is included

2. **Check Mappers**
   - Go to **Clients** → [Your Client] → **Client Scopes** → **roles**
   - Ensure appropriate role mappers are configured

## Security Considerations

1. **Principle of Least Privilege**
   - Only assign `gist-analyst` role to users who need dashboard access
   - Regularly review role assignments

2. **Role Hierarchy**
   - Consider creating additional roles for different access levels
   - Example: `gist-admin`, `gist-viewer`, `gist-analyst`

3. **Audit Trail**
   - Keycloak logs role assignments and access attempts
   - Monitor for unauthorized access attempts

## Environment Variables

No additional environment variables are needed. The role checking uses the existing Keycloak configuration:

```bash
KEYCLOAK_SERVER_URL=https://your-keycloak-server
KEYCLOAK_REALM=your-realm
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret  # Optional
KEYCLOAK_REDIRECT_URI=http://localhost:8501
```

## Testing

1. **Create Test Users**
   - User with `gist-analyst` role → Should have access
   - User without role → Should be denied access

2. **Verify Role Display**
   - Check that roles appear in the sidebar after login
   - Verify authorization messages are clear and helpful

3. **Test Role Changes**
   - Remove role from user → Access should be denied on next login
   - Add role to user → Access should be granted on next login 