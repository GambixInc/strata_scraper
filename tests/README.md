# Tests Directory

This directory contains all test files for the Strata Scraper application.

## Test Files

### Core Test Suite
- **`test_suite.py`** - Comprehensive test suite covering all major functionality
- **`run_tests.py`** - Simple test runner for the main test suite
- **`run_all_tests.py`** - Comprehensive test runner for all test files
- **`test_local.py`** - Local development test runner
- **`test_config.py`** - Test configuration and environment setup

### Authentication Tests
- **`test_auth.py`** - Basic authentication functionality tests
- **`test_cognito_auth.py`** - AWS Cognito authentication tests

### Database Tests
- **`test_database.py`** - SQLite database functionality tests
- **`test_dynamodb.py`** - DynamoDB database functionality tests

### Storage Tests
- **`test_s3_storage.py`** - AWS S3 storage functionality tests
- **`test_file_access.py`** - File system access tests

### API Tests
- **`test_routes.py`** - API endpoint tests
- **`test_tracker.py`** - Site tracking functionality tests

### Production Readiness Tests
- **`test_production_readiness.py`** - Production environment readiness tests
- **`test_infrastructure_production_readiness.py`** - Infrastructure readiness tests

### Utility Tests
- **`test_imports.py`** - Module import tests

## Running Tests

### Run Main Test Suite (Recommended)
```bash
# From root directory
python3 run_tests.py

# From tests directory
python3 tests/test_suite.py

# Run local tests
python3 tests/test_local.py
```

### Run All Individual Tests
```bash
# From tests directory
python3 run_all_tests.py
```

### Run Specific Test
```bash
# Run specific test file
python3 tests/run_all_tests.py test_auth.py
```

### Docker Build Tests
Tests are automatically run during Docker build:
```bash
docker build -t strata-scraper .
```

## Test Categories

### Unit Tests
- Database operations
- Authentication
- File operations
- Utility functions

### Integration Tests
- API endpoints
- S3 storage integration
- DynamoDB integration
- Scraping functionality

### Production Tests
- Environment configuration
- Infrastructure readiness
- Production deployment readiness

## Test Environment

Tests can run in different environments:
- **Local Development**: Uses SQLite database
- **Docker Build**: Uses DynamoDB (production-like)
- **CI/CD**: Uses test-specific configurations

## Test Configuration

Test environment is configured in `test_config.py`:
- Database type (SQLite/DynamoDB)
- S3 bucket configuration
- Test URLs and timeouts
- Environment variables

## Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Add to `run_all_tests.py` if it should be part of comprehensive test suite
4. Ensure tests can run independently
5. Add proper cleanup in `tearDown()` methods

## Test Best Practices

- Use unique test data to avoid conflicts
- Clean up after tests
- Mock external services when appropriate
- Skip tests that require external dependencies
- Provide clear error messages
- Test both success and failure scenarios
