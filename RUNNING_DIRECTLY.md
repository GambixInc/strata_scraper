# Running Gambix Strata Directly (No Docker)

## 🚀 Quick Start

### Production (AWS S3 + DynamoDB)
```bash
./start_production.sh
```

### Development (Local SQLite + Files)
```bash
./start_dev.sh
```

### Manual Start
```bash
python3 server.py
```

## 🔧 Configuration

### Environment Variables
The app uses these environment variables:

**Production (AWS):**
- `USE_DYNAMODB=true`
- `AWS_REGION=us-east-1`
- `S3_BUCKET_NAME=gambix-strata-production`
- `DYNAMODB_TABLE_PREFIX=gambix_strata_`

**Development (Local):**
- `USE_DYNAMODB=false`
- `DEBUG=true`

### AWS Credentials
For production, you need AWS credentials:

1. **IAM Role** (Recommended for EC2):
   - Attach IAM role to EC2 instance
   - No additional configuration needed

2. **AWS CLI** (Alternative):
   ```bash
   aws configure
   ```

3. **Environment Variables** (Alternative):
   ```bash
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   ```

## 📁 File Structure

```
strata_scraper/
├── server.py              # Main Flask application
├── start_production.sh    # Production startup script
├── start_dev.sh          # Development startup script
├── config/
│   └── app.env.example   # Environment variables template
├── data/                 # SQLite database (development)
├── logs/                 # Application logs
└── strata_design/        # Frontend files
```

## 🌐 Access Points

Once running, the app will be available at:

- **Main App**: http://localhost:8080
- **Health Check**: http://localhost:8080/api/health
- **API Endpoints**: http://localhost:8080/api/*

## 🔍 Troubleshooting

### Database Issues
```bash
# Run database migration
python3 add_cognito_column.py
```

### Permission Issues
```bash
# Make scripts executable
chmod +x start_production.sh start_dev.sh
```

### AWS Issues
```bash
# Test AWS connectivity
aws sts get-caller-identity
```

### Port Issues
```bash
# Check if port is in use
lsof -i :8080
```

## 📝 Logs

Logs are written to:
- `logs/web_scraper.log` (production)
- Console output (development)

## 🛑 Stopping the Server

Press `Ctrl+C` to stop the server gracefully.
