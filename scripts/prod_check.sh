#!/bin/bash
#
# Production Sanity Check Script for Living Lytics API
# Usage: ./scripts/prod_check.sh [BASE_URL] [API_KEY] [TEST_EMAIL]
#
# Example:
#   ./scripts/prod_check.sh https://api.livinglytics.com $FASTAPI_SECRET_KEY demo@livinglytics.app
#

set -e

# Configuration
BASE_URL="${1:-https://api.livinglytics.com}"
API_KEY="${2:-$FASTAPI_SECRET_KEY}"
TEST_EMAIL="${3:-demo@livinglytics.app}"

if [ -z "$API_KEY" ]; then
    echo "❌ ERROR: API_KEY not provided"
    echo "Usage: $0 [BASE_URL] [API_KEY] [TEST_EMAIL]"
    exit 1
fi

echo "🔍 Living Lytics API - Production Sanity Check"
echo "=============================================="
echo "Base URL: $BASE_URL"
echo "Test Email: $TEST_EMAIL"
echo ""

# Helper function for HTTP requests
check_endpoint() {
    local name="$1"
    local url="$2"
    local auth="$3"
    
    echo "📡 Testing: $name"
    echo "   URL: $url"
    
    if [ "$auth" = "true" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $API_KEY" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo "   ✅ Status: $http_code"
        echo "   Response: $(echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body")"
    else
        echo "   ❌ Status: $http_code"
        echo "   Response: $body"
        return 1
    fi
    echo ""
}

# 1. Health Check - Readiness
echo "1️⃣  Health Check: Readiness"
echo "================================"
check_endpoint "Readiness" "$BASE_URL/v1/health/readiness" "false"

# 2. Scheduler Status
echo "2️⃣  Digest Scheduler Status"
echo "================================"
check_endpoint "Scheduler" "$BASE_URL/v1/digest/schedule" "true"

# 3. Metrics Timeline
echo "3️⃣  Metrics Timeline"
echo "================================"
check_endpoint "Timeline" "$BASE_URL/v1/metrics/timeline?user_email=$TEST_EMAIL&days=7" "true"

# Final Summary
echo "=============================================="
echo "✅ Production sanity check completed!"
echo ""
echo "All critical endpoints are responding correctly."
echo "Next steps:"
echo "  - Verify scheduler next run time is correct"
echo "  - Check that timeline data looks reasonable"
echo "  - Monitor logs for any errors"
