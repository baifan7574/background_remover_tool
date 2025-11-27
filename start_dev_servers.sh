#!/bin/bash

echo "🚀 启动背景移除工具 - 开发模式"
echo "==================================="

echo ""
echo "🔧 启动后端服务器 (端口 5000)..."
gnome-terminal -- bash -c "cd '$PWD/backend' && python app_supabase_simple.py; exec bash" 2>/dev/null || \
xterm -e "cd '$PWD/backend' && python app_supabase_simple.py" 2>/dev/null || \
(osascript -e 'tell app "Terminal" to do script "cd '"$PWD/backend"' && python app_supabase_simple.py"') 2>/dev/null || \
{
    echo "在后台启动后端服务器..."
    cd backend && python app_supabase_simple.py &
    BACKEND_PID=$!
    echo "后端服务器 PID: $BACKEND_PID"
}

echo ""
echo "⏳ 等待后端服务器启动..."
sleep 3

echo ""
echo "🎨 启动前端服务器 (端口 8000)..."
gnome-terminal -- bash -c "cd '$PWD/frontend' && python -m http.server 8000; exec bash" 2>/dev/null || \
xterm -e "cd '$PWD/frontend' && python -m http.server 8000" 2>/dev/null || \
(osascript -e 'tell app "Terminal" to do script "cd '"$PWD/frontend"' && python -m http.server 8000"') 2>/dev/null || \
{
    echo "在后台启动前端服务器..."
    cd frontend && python -m http.server 8000 &
    FRONTEND_PID=$!
    echo "前端服务器 PID: $FRONTEND_PID"
}

echo ""
echo "✅ 服务器启动完成！"
echo "📱 前端地址: http://localhost:8000"
echo "🔧 后端地址: http://localhost:5000"
echo "🧪 测试页面: http://localhost:8000/auth_test_simple.html"
echo ""
echo "按 Ctrl+C 停止服务器..."

# 如果在后台启动，等待信号
if [ ! -z "$BACKEND_PID" ] && [ ! -z "$FRONTEND_PID" ]; then
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
    wait
fi