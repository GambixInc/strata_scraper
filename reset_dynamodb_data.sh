#!/bin/bash
# Reset DynamoDB data for Gambix Strata

set -e  # Exit on any error

echo "🗑️  Resetting DynamoDB data for Gambix Strata"
echo ""

# Configuration
TABLE_PREFIX="${DYNAMODB_TABLE_PREFIX:-gambix_strata_}"
REGION="${AWS_REGION:-us-east-1}"

echo "📋 Configuration:"
echo "   DynamoDB Prefix: $TABLE_PREFIX"
echo "   AWS Region: $REGION"
echo ""

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not found. Please configure AWS CLI or ensure IAM role is attached."
    exit 1
fi

echo "✅ AWS credentials verified"
aws sts get-caller-identity
echo ""

# List all tables with the prefix
echo "📋 Finding DynamoDB tables with prefix: $TABLE_PREFIX"
TABLES=$(aws dynamodb list-tables --region $REGION --query "TableNames[?starts_with(@, '$TABLE_PREFIX')]" --output text)

if [ -z "$TABLES" ]; then
    echo "❌ No tables found with prefix: $TABLE_PREFIX"
    echo ""
    echo "Available tables:"
    aws dynamodb list-tables --region $REGION --query "TableNames[?contains(@, 'gambix_strata')]" --output table
    exit 1
fi

echo "Found tables:"
echo "$TABLES" | tr '\t' '\n' | while read table; do
    echo "   - $table"
done
echo ""

# Confirm deletion
echo "⚠️  WARNING: This will DELETE ALL DATA from the following tables:"
echo "$TABLES" | tr '\t' '\n' | while read table; do
    echo "   - $table"
done
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled"
    exit 0
fi

echo ""
echo "🗑️  Starting data deletion..."

# Delete data from each table
echo "$TABLES" | tr '\t' '\n' | while read table; do
    echo "Deleting data from: $table"
    
    # Get all items from the table
    ITEMS=$(aws dynamodb scan --table-name "$table" --region $REGION --query "Items[*]" --output json)
    
    if [ "$ITEMS" != "[]" ]; then
        # Delete each item
        echo "$ITEMS" | jq -c '.[]' | while read item; do
            # Extract the primary key (assuming it's the first key in the item)
            KEY=$(echo "$item" | jq 'keys | .[0]')
            KEY_NAME=$(echo "$KEY" | tr -d '"')
            KEY_VALUE=$(echo "$item" | jq ".[$KEY]")
            
            echo "   Deleting item with $KEY_NAME: $KEY_VALUE"
            
            # Create the key JSON for deletion
            KEY_JSON="{\"$KEY_NAME\": $KEY_VALUE}"
            
            # Delete the item
            aws dynamodb delete-item \
                --table-name "$table" \
                --key "$KEY_JSON" \
                --region $REGION > /dev/null 2>&1
        done
        
        echo "   ✅ Deleted all items from $table"
    else
        echo "   ℹ️  Table $table is already empty"
    fi
done

echo ""
echo "✅ DynamoDB data reset completed!"
echo ""
echo "📋 Summary:"
echo "   - All data deleted from tables with prefix: $TABLE_PREFIX"
echo "   - Tables are now empty and ready for fresh data"
echo ""
echo "🔄 Next steps:"
echo "   1. Fix the backend to store actual user information"
echo "   2. Test user registration and project creation"
echo "   3. Verify data is stored correctly in DynamoDB"
