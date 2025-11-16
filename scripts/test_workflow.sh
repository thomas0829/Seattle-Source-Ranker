#!/bin/bash
# 測試 GitHub Actions workflow 的本地執行
# 這個腳本模擬 GitHub Actions 的執行流程

set -e  # 遇到錯誤立即退出

echo "🧪 Testing GitHub Actions workflow locally..."
echo "=============================================="

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Redis
echo -e "\n${YELLOW}1. Checking Redis...${NC}"
if pgrep -x "redis-server" > /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Please start Redis: redis-server &"
    exit 1
fi

# 檢查 .env.tokens
echo -e "\n${YELLOW}2. Checking .env.tokens...${NC}"
if [ -f ".env.tokens" ]; then
    TOKEN_COUNT=$(grep -c "GITHUB_TOKEN_" .env.tokens || true)
    echo -e "${GREEN}✅ Found .env.tokens with $TOKEN_COUNT tokens${NC}"
else
    echo -e "${RED}❌ .env.tokens not found${NC}"
    exit 1
fi

# 檢查 Python 依賴
echo -e "\n${YELLOW}3. Checking Python dependencies...${NC}"
if python3 -c "import celery, redis, requests, dotenv" 2>/dev/null; then
    echo -e "${GREEN}✅ All Python dependencies installed${NC}"
else
    echo -e "${RED}❌ Missing dependencies${NC}"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# 測試小規模收集
echo -e "\n${YELLOW}4. Running test collection (100 users)...${NC}"
python3 << 'PYTHON_EOF'
import sys
from distributed.distributed_collector import DistributedCollector

try:
    collector = DistributedCollector(
        batch_size=50,
        auto_manage_workers=True,
        num_workers=4,  # 使用較少 worker 測試
        concurrency=2
    )
    
    print("Starting test collection...")
    collector.collect(max_users=100)
    print("\n✅ Test collection completed successfully!")
    
except Exception as e:
    print(f"\n❌ Test collection failed: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Collection test passed${NC}"
else
    echo -e "${RED}❌ Collection test failed${NC}"
    exit 1
fi

# 清理舊數據
echo -e "\n${YELLOW}5. Cleaning old data files...${NC}"
cd data
OLD_PROJECTS=$(ls -t seattle_projects_*.json 2>/dev/null | tail -n +2)
OLD_USERS=$(ls -t seattle_users_*.json 2>/dev/null | tail -n +2)

if [ -n "$OLD_PROJECTS" ] || [ -n "$OLD_USERS" ]; then
    echo "Found old files to clean:"
    [ -n "$OLD_PROJECTS" ] && echo "$OLD_PROJECTS" | sed 's/^/  - /'
    [ -n "$OLD_USERS" ] && echo "$OLD_USERS" | sed 's/^/  - /'
    
    read -p "Delete old files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        [ -n "$OLD_PROJECTS" ] && echo "$OLD_PROJECTS" | xargs rm -v
        [ -n "$OLD_USERS" ] && echo "$OLD_USERS" | xargs rm -v
        echo -e "${GREEN}✅ Old files cleaned${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipped cleaning${NC}"
    fi
else
    echo -e "${GREEN}✅ No old files to clean${NC}"
fi
cd ..

# 測試 README 更新
echo -e "\n${YELLOW}6. Testing README update...${NC}"
if python3 scripts/update_readme.py; then
    echo -e "${GREEN}✅ README update test passed${NC}"
else
    echo -e "${RED}❌ README update test failed${NC}"
    exit 1
fi

# 檢查輸出文件
echo -e "\n${YELLOW}7. Checking output files...${NC}"
if [ -f "data/ranked_project_local_seattle.json" ]; then
    echo -e "${GREEN}✅ ranked_project_local_seattle.json exists${NC}"
else
    echo -e "${YELLOW}⚠️  ranked_project_local_seattle.json not found${NC}"
fi

if [ -f "data/ranked_by_language_seattle.json" ]; then
    echo -e "${GREEN}✅ ranked_by_language_seattle.json exists${NC}"
else
    echo -e "${YELLOW}⚠️  ranked_by_language_seattle.json not found${NC}"
fi

# 測試前端構建 (可選)
read -p $'\n'"Build frontend? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}8. Building frontend...${NC}"
    cd frontend
    if npm ci && npm run build; then
        echo -e "${GREEN}✅ Frontend build successful${NC}"
    else
        echo -e "${RED}❌ Frontend build failed${NC}"
        exit 1
    fi
    cd ..
fi

echo -e "\n${GREEN}=============================================="
echo "🎉 All tests passed! Workflow is ready."
echo -e "==============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Commit and push the workflow file"
echo "2. Add GitHub Secrets (GITHUB_TOKEN_1 to GITHUB_TOKEN_6)"
echo "3. Enable GitHub Pages (gh-pages branch)"
echo "4. Manually trigger the workflow or wait for scheduled run"
