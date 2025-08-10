# AWS Cognito Authentication Setup

This document describes the authentication system implemented for the Gambix Strata platform using AWS Cognito.

## Overview

The authentication system uses AWS Cognito for user authentication and management. The backend validates Cognito tokens and manages user profiles in the local database. This provides secure, scalable authentication while maintaining user data locally.

## Features

- **AWS Cognito Integration**: Uses AWS Cognito for authentication
- **Token Validation**: Validates Cognito tokens on protected endpoints
- **User Profile Management**: Get and update user profiles
- **Protected Routes**: Authentication middleware for API endpoints
- **Automatic User Creation**: Creates users in local database on first access
- **Project Management**: Secure project creation and management

## API Endpoints

### User Profile Endpoints

#### GET `/api/user/profile`
Get current user's profile information.

**Headers:**
```
Authorization: Bearer <cognito_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T00:00:00Z",
    "preferences": {}
  }
}
```

#### PUT `/api/user/profile`
Update current user's profile information.

**Headers:**
```
Authorization: Bearer <cognito_token>
```

**Request Body:**
```json
{
  "name": "John Smith",
  "preferences": {
    "theme": "dark",
    "notifications": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Smith",
    "role": "user",
    "preferences": {
      "theme": "dark",
      "notifications": true
    }
  }
}
```

### Project Management Endpoints

#### GET `/api/projects`
Get all projects for the current user.

**Headers:**
```
Authorization: Bearer <cognito_token>
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "project_uuid",
      "url": "https://example.com",
      "icon": "fas fa-globe",
      "status": "active",
      "healthScore": 85,
      "recommendations": 5,
      "autoOptimize": true,
      "lastUpdated": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST `/api/projects`
Create a new project.

**Headers:**
```
Authorization: Bearer <cognito_token>
```

**Request Body:**
```json
{
  "websiteUrl": "https://example.com",
  "category": "Technology",
  "description": "My website project"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "project_uuid",
    "message": "Project created successfully"
  }
}
```

### Dashboard Endpoints

#### GET `/api/dashboard`
Get dashboard data for the current user.

**Headers:**
```
Authorization: Bearer <cognito_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_projects": 5,
    "active_projects": 4,
    "total_health_score": 82,
    "recent_activity": [],
    "alerts": []
  }
}
```

## Protected Endpoints

The following endpoints require authentication (include `Authorization: Bearer <cognito_token>` header):

- `GET /api/user/profile`
- `PUT /api/user/profile`
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/dashboard`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT, -- Not used with Cognito
    role TEXT CHECK(role IN ('admin', 'user', 'viewer')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    preferences TEXT -- JSON string
);
```

## Security Features

1. **AWS Cognito Tokens**: Secure, signed tokens from AWS Cognito
2. **Token Validation**: Validates token signature and expiration
3. **Rate Limiting**: API endpoints are rate-limited to prevent abuse
4. **CORS Protection**: Cross-origin requests are properly configured
5. **Input Validation**: All inputs are validated and sanitized
6. **Error Handling**: Secure error messages that don't leak sensitive information

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# AWS Cognito Configuration
AWS_REGION=us-east-1
AWS_USER_POOLS_ID=us-east-1_XXXXXXXXX

# Server Configuration
PORT=8080
HOST=0.0.0.0
DEBUG=False

# Database Configuration
DATABASE_PATH=gambix_strata.db

# Security Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Testing

Run the authentication test script:

```bash
python3 test_cognito_auth.py
```

This will test:
1. User profile retrieval (requires valid token)
2. Project listing (requires valid token)
3. Dashboard data retrieval (requires valid token)
4. Project creation (requires valid token)
5. Invalid token handling

## Frontend Integration

### Token Storage
Store the Cognito token in localStorage or secure storage:
```javascript
localStorage.setItem('authToken', cognitoToken);
```

### API Requests
Include the token in all authenticated requests:
```javascript
const headers = {
  'Authorization': `Bearer ${cognitoToken}`,
  'Content-Type': 'application/json'
};

fetch('/api/projects', { headers });
```

### Error Handling
Handle authentication errors (401, 403):
```javascript
if (response.status === 401) {
  // Token expired or invalid
  localStorage.removeItem('authToken');
  redirectToLogin();
}
```

## User Management Flow

1. **User Authentication**: User authenticates via AWS Cognito (frontend)
2. **Token Validation**: Backend validates Cognito token on each request
3. **User Creation**: If user doesn't exist in local database, create them automatically
4. **Profile Management**: User can update their profile preferences
5. **Project Management**: User can create and manage their projects

## Best Practices

1. **Token Expiration**: Cognito tokens have built-in expiration
2. **Token Refresh**: Implement token refresh logic in frontend
3. **Rate Limiting**: All auth endpoints are rate-limited
4. **HTTPS**: Use HTTPS in production
5. **Secret Management**: Use environment variables for AWS configuration
6. **Logging**: Monitor authentication attempts and failures
7. **Backup**: Regularly backup the database

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure CORS_ORIGINS includes your frontend URL
2. **Token Expired**: Tokens expire automatically, implement refresh logic
3. **Invalid Token**: Check token format and signature
4. **Database Errors**: Ensure database is properly initialized
5. **Rate Limiting**: Reduce request frequency if hitting limits

### Debug Mode

Enable debug mode for detailed error messages:
```bash
DEBUG=True
```

## Future Enhancements

1. **Token Refresh**: Automatic token refresh on expiration
2. **User Groups**: Support for Cognito user groups and roles
3. **MFA Support**: Multi-factor authentication support
4. **Audit Logging**: Detailed authentication audit trails
5. **User Preferences**: Enhanced user preference management
