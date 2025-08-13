# 🧪 S3 Integration Testing Guide

This guide covers different ways to test the S3 integration locally, especially when you have different AWS accounts for local development vs production.

## 🎯 **Testing Strategies Overview**

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **LocalStack** | ✅ No AWS costs<br>✅ Isolated testing<br>✅ Fast setup | ❌ Limited S3 features | Development & CI/CD |
| **Local Fallback** | ✅ No setup required<br>✅ Tests fallback logic | ❌ Doesn't test S3 | Basic functionality |
| **Separate AWS Account** | ✅ Real S3 testing<br>✅ Full feature set | ❌ AWS costs<br>❌ Account management | Production-like testing |
| **Mock Testing** | ✅ Fast execution<br>✅ No external deps | ❌ Doesn't test real S3 | Unit tests |

## 🐳 **Method 1: LocalStack (Separate Project)**

For LocalStack testing, please refer to the separate LocalStack project at `../localstack_project/`.

```bash
# Navigate to the separate LocalStack project
cd ../localstack_project

# Setup and test LocalStack
./setup_localstack.sh
```

## 🔄 **Method 2: Local Fallback Testing**

### Test Fallback Logic
```bash
# Test that app works without S3
# (The app automatically falls back to local storage when S3 is not configured)

# This will verify:
# ✅ S3 unavailable → falls back to local
# ✅ Invalid credentials → falls back to local
# ✅ Server handles S3 failures gracefully
```

### Manual Fallback Test
```bash
# Clear AWS credentials
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY S3_BUCKET_NAME

# Run the scraper
python main.py

# Should automatically use local storage
```

## ☁️ **Method 3: Separate AWS Account**

### Create Test AWS Account
1. Create a new AWS account for testing
2. Create an S3 bucket: `strata-scraper-test`
3. Create IAM user with S3 permissions
4. Generate access keys

### Configure Test Environment
```bash
# Create test environment file
cat > .env.test << EOF
AWS_ACCESS_KEY_ID=your-test-access-key
AWS_SECRET_ACCESS_KEY=your-test-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=strata-scraper-test
S3_ENDPOINT_URL=https://s3.amazonaws.com
EOF

# Test with test environment
python test_s3_storage.py --env-file .env.test
```

## 🧩 **Method 4: Mock Testing**

### Create Mock Test
```python
# test_mock_s3.py
import unittest
from unittest.mock import patch, MagicMock
from s3_storage import S3Storage

class TestS3Storage(unittest.TestCase):
    @patch('boto3.client')
    def test_s3_upload_success(self, mock_boto3):
        # Mock successful S3 upload
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        
        s3_storage = S3Storage()
        result = s3_storage.upload_file_content("test", "test.txt")
        
        self.assertTrue(result)
        mock_s3.put_object.assert_called_once()

if __name__ == '__main__':
    unittest.main()
```

## 🔍 **Testing Checklist**

### ✅ **Basic Functionality**
- [ ] App starts without S3 credentials
- [ ] App falls back to local storage when S3 fails
- [ ] Files are saved correctly in both modes
- [ ] Database stores correct storage location

### ✅ **S3 Integration**
- [ ] S3 connection test passes
- [ ] File upload to S3 works
- [ ] Presigned URL generation works
- [ ] File listing works
- [ ] File deletion works

### ✅ **Error Handling**
- [ ] Invalid credentials handled gracefully
- [ ] Network errors don't crash the app
- [ ] Missing bucket handled properly
- [ ] Permission errors logged correctly

### ✅ **API Endpoints**
- [ ] `/api/scrape` works with S3
- [ ] `/api/scrape` falls back to local
- [ ] Response includes storage type
- [ ] Project creation works with S3

## 🚀 **Quick Test Commands**

### Test Everything Locally
```bash
# 1. Test S3 functionality (if configured)
python test_s3_storage.py

# 2. Test with LocalStack (separate project)
cd ../localstack_project
./setup_localstack.sh

# 3. Test the main scraper
python main.py

# 4. Test the API server
python server.py &
curl -X POST http://localhost:8080/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
kill %1
```

### Test in Docker
```bash
# Test with LocalStack (separate project)
cd ../localstack_project
docker compose -f docker-compose.localstack.yml --profile localstack up -d
```

# Test with local fallback
docker-compose up -d
curl http://localhost:8080/api/health
docker-compose down
```

## 🐛 **Troubleshooting**

### Common Issues

**LocalStack not starting:**
```bash
# Check if port 4566 is available
lsof -i :4566

# Restart LocalStack
docker-compose -f docker-compose.localstack.yml --profile localstack down
docker-compose -f docker-compose.localstack.yml --profile localstack up -d
```

**S3 connection failing:**
```bash
# Check environment variables
env | grep AWS

# Test S3 connection manually
aws s3 ls s3://your-bucket --endpoint-url=http://localhost:4566
```

**App not falling back to local:**
```bash
# Clear all AWS environment variables
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY S3_BUCKET_NAME AWS_REGION

# Restart the app
python server.py
```

## 📊 **Performance Testing**

### Test Upload Performance
```bash
# Create large test file
dd if=/dev/zero of=test_large.txt bs=1M count=10

# Test upload time
time python -c "
from s3_storage import S3Storage
s3 = S3Storage()
with open('test_large.txt', 'r') as f:
    s3.upload_file_content(f.read(), 'test/large.txt')
"
```

### Test Concurrent Uploads
```python
# test_concurrent.py
import threading
import time
from s3_storage import S3Storage

def upload_file(i):
    s3 = S3Storage()
    content = f"Test content {i}"
    s3.upload_file_content(content, f"test/concurrent_{i}.txt")

# Test 10 concurrent uploads
threads = []
start_time = time.time()

for i in range(10):
    t = threading.Thread(target=upload_file, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"Uploaded 10 files in {time.time() - start_time:.2f} seconds")
```

## 🎯 **Recommended Testing Workflow**

1. **Start with LocalStack** for development
2. **Test fallback logic** to ensure robustness
3. **Use separate AWS account** for production-like testing
4. **Run performance tests** before production deployment

This approach ensures your S3 integration works correctly without interfering with your production AWS account.
