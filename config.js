// 配置文件 - 开发/生产环境切换

// 开发环境：使用本地服务器
const DEV_CONFIG = {
    API_BASE_URL: 'http://localhost:5000',
    FRONTEND_URL: 'http://localhost:8000'
};

// 生产环境：使用线上服务器
// 请将 YOUR_DOMAIN 替换为您的实际域名，例如：
// - https://baifan7574.pythonanywhere.com
// - https://your-domain.com
const PROD_CONFIG = {
    API_BASE_URL: 'https://YOUR_DOMAIN.com',  // 修改为您的实际后端地址
    FRONTEND_URL: 'https://YOUR_DOMAIN.com'   // 修改为您的实际前端地址
};

// 自动检测环境：如果访问 localhost 则使用开发配置，否则使用生产配置
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// 导出配置
const CONFIG = isDevelopment ? DEV_CONFIG : PROD_CONFIG;

// 如果是 Node.js 环境
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}

