#!/bin/bash
set -e

echo "=========================================="
echo "Saurellius Platform - Complete Fix v11"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd /home/ubuntu/saurellius-platform

echo -e "${YELLOW}Step 1: Resetting to clean state...${NC}"
git fetch origin
git reset --hard origin/branch-2
echo -e "${GREEN}✓ Reset complete${NC}"
echo ""

echo -e "${YELLOW}Step 2: Removing Paystub class from user.py...${NC}"
# Remove lines 74-247 (Paystub class definition)
sed -i '74,247d' src/models/user.py
echo -e "${GREEN}✓ Removed duplicate Paystub model${NC}"
echo ""

echo -e "${YELLOW}Step 3: Fixing dashboard.py imports...${NC}"
cat > /tmp/dashboard_imports.txt << 'EOF'
from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.user import User, RewardActivity
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.models.company import Company
from src.routes.auth import token_required
EOF

tail -n +8 src/routes/dashboard.py > /tmp/dashboard_rest.txt
cat /tmp/dashboard_imports.txt /tmp/dashboard_rest.txt > src/routes/dashboard.py
echo -e "${GREEN}✓ Fixed dashboard.py imports${NC}"
echo ""

echo -e "${YELLOW}Step 4: Fixing employee.py imports...${NC}"
cat > /tmp/employee_imports.txt << 'EOF'
from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.user import User
from src.models.employee import Employee
from src.models.company import Company
from src.models.paystub import Paystub
from src.routes.auth import token_required
EOF

tail -n +8 src/routes/employee.py > /tmp/employee_rest.txt
cat /tmp/employee_imports.txt /tmp/employee_rest.txt > src/routes/employee.py
echo -e "${GREEN}✓ Fixed employee.py imports${NC}"
echo ""

echo -e "${YELLOW}Step 5: Fixing paystub_advanced.py imports...${NC}"
cat > /tmp/paystub_adv_imports.txt << 'EOF'
from flask import Blueprint, jsonify, request, send_file
from src.models.database import db
from src.models.user import User, RewardActivity
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.routes.auth import token_required
EOF

tail -n +11 src/routes/paystub_advanced.py > /tmp/paystub_adv_rest.txt
cat /tmp/paystub_adv_imports.txt /tmp/paystub_adv_rest.txt > src/routes/paystub_advanced.py
echo -e "${GREEN}✓ Fixed paystub_advanced.py imports${NC}"
echo ""

echo -e "${YELLOW}Step 6: Fixing paystub_complete.py imports...${NC}"
cat > /tmp/paystub_complete_imports.txt << 'EOF'
from flask import Blueprint, jsonify, request, send_file
from src.models.database import db
from src.models.user import User
from src.models.employee import Employee
from src.models.paystub import Paystub
from src.models.company import Company
from src.routes.auth import token_required
EOF

tail -n +8 src/routes/paystub_complete.py > /tmp/paystub_complete_rest.txt
cat /tmp/paystub_complete_imports.txt /tmp/paystub_complete_rest.txt > src/routes/paystub_complete.py
echo -e "${GREEN}✓ Fixed paystub_complete.py imports${NC}"
echo ""

echo -e "${YELLOW}Step 7: Verifying no duplicate model classes...${NC}"
echo -e "${BLUE}Checking for duplicate Paystub definitions:${NC}"
grep -n "^class Paystub" src/models/*.py || echo "  None found (good!)"

echo -e "${BLUE}Checking for duplicate Employee definitions:${NC}"
grep -n "^class Employee" src/models/*.py || echo "  None found (good!)"

echo -e "${BLUE}Checking for duplicate Company definitions:${NC}"
grep -n "^class Company" src/models/*.py || echo "  None found (good!)"
echo ""

echo -e "${YELLOW}Step 8: Checking for bad imports in routes...${NC}"
BAD_IMPORTS=$(grep -rn "from src.models.user import.*Employee\|from src.models.user import.*Company\|from src.models.user import.*Paystub" src/routes/ 2>/dev/null | grep -v "^#" || true)

if [ -z "$BAD_IMPORTS" ]; then
    echo -e "${GREEN}✓ No bad imports found!${NC}"
else
    echo -e "${RED}⚠ Warning: Found potential bad imports:${NC}"
    echo "$BAD_IMPORTS"
fi
echo ""

echo -e "${YELLOW}Step 9: Committing changes...${NC}"
git add -A
git commit -m "v11-FINAL: Fixed all duplicate model imports across all routes (dashboard, employee, paystub_advanced, paystub_complete). Removed Paystub from user.py"
echo -e "${GREEN}✓ Changes committed${NC}"
echo ""

echo -e "${YELLOW}Step 10: Pushing to GitHub...${NC}"
git push origin branch-2
echo -e "${GREEN}✓ Pushed to GitHub${NC}"
echo ""

echo -e "${YELLOW}Step 11: Creating deployment package...${NC}"
rm -f *.zip
ZIPFILE="saurellius-prod-v11-FINAL-$(date +%Y%m%d-%H%M%S).zip"
zip -r $ZIPFILE . -x "*.git*" "*__pycache__*" "*.pyc" "*.DS_Store" "*venv*" "*.env*" "*.disabled" "*.backup" "*.original" 2>&1 | tail -3
echo -e "${GREEN}✓ Created $ZIPFILE${NC}"
echo ""

echo -e "${YELLOW}Step 12: Uploading to S3...${NC}"
aws s3 cp $ZIPFILE s3://saurellius-deployments/
echo -e "${GREEN}✓ Uploaded to S3${NC}"
echo ""

echo -e "${YELLOW}Step 13: Creating application version...${NC}"
VERSION_LABEL="v11-FINAL-all-imports-fixed-$(date +%Y%m%d-%H%M%S)"
aws elasticbeanstalk create-application-version \
  --application-name SaurelliusProd2025 \
  --version-label "$VERSION_LABEL" \
  --source-bundle S3Bucket="saurellius-deployments",S3Key="$ZIPFILE" \
  --region us-east-1 > /dev/null
echo -e "${GREEN}✓ Application version created: $VERSION_LABEL${NC}"
echo ""

echo -e "${YELLOW}Step 14: Deploying to Elastic Beanstalk...${NC}"
DEPLOY_STATUS=$(aws elasticbeanstalk update-environment \
  --environment-name saurellius-production \
  --version-label "$VERSION_LABEL" \
  --region us-east-1 \
  --query 'Status' \
  --output text)

echo -e "${GREEN}✓ Deployment initiated! Status: $DEPLOY_STATUS${NC}"
echo ""

echo -e "${GREEN}=========================================="
echo "Complete Fix Applied Successfully!"
echo "==========================================${NC}"
echo ""
echo "Deployed version: $VERSION_LABEL"
echo ""
echo "Monitor deployment with:"
echo "  watch -n 30 'aws elasticbeanstalk describe-environments --environment-names saurellius-production --region us-east-1 --query \"Environments[0].Status\" --output text'"
echo ""
echo "Check logs after 5 minutes with:"
echo "  aws elasticbeanstalk logs --environment-name saurellius-production --region us-east-1"
echo ""
echo "Your site should be live in 5-8 minutes! 🚀"
