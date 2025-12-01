@echo off
chcp 65001 >nul
REM 快速配置SSH免密登录 - 服务器IP: 43.130.229.184

echo ========================================
echo 配置SSH免密登录
echo 服务器IP: 43.130.229.184
echo ========================================
echo.

set SERVER_IP=43.130.229.184
set SSH_KEY_FILE=%USERPROFILE%\.ssh\id_rsa.pub

REM 检查是否已有SSH密钥
if not exist "%SSH_KEY_FILE%" (
    echo 生成SSH密钥...
    ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -N ""
    echo ✅ SSH密钥已生成
    echo.
)

REM 显示公钥
echo 您的公钥内容：
echo ----------------------------------------
type "%SSH_KEY_FILE%"
echo ----------------------------------------
echo.

echo 请按照以下步骤操作：
echo.
echo 1. 复制上面的公钥内容（从ssh-rsa开始到邮箱结束）
echo 2. SSH登录服务器：ssh root@%SERVER_IP%
echo 3. 输入服务器密码登录
echo 4. 在服务器上执行以下命令：
echo.
echo    mkdir -p ~/.ssh
echo    chmod 700 ~/.ssh
echo    echo "粘贴您的公钥内容" ^>^> ~/.ssh/authorized_keys
echo    chmod 600 ~/.ssh/authorized_keys
echo    exit
echo.
echo 5. 测试免密登录：ssh root@%SERVER_IP%
echo.

pause

