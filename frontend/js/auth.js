// 用户认证管理
// 自动检测环境：开发环境使用localhost，生产环境使用线上地址
const getApiBaseUrl = () => {
    // 如果是本地文件协议或访问 localhost，使用本地开发服务器
    if (window.location.protocol === 'file:' ||
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    // 否则使用当前域名（生产环境）
    return window.location.origin;
};

class AuthManager {
    constructor() {
        this.apiBaseUrl = getApiBaseUrl(); // 自动选择API地址
        this.token = null;
        this.user = null;
        this.planInfo = null;
        this.init();
    }

    // 初始化 - 从localStorage恢复认证状态（移动端优化）
    init() {
        try {
            // 移动端兼容：使用统一的读取方法
            const savedToken = this.getFromStorage('auth_token');
            const savedUser = this.getFromStorage('user_info');

            if (savedToken && savedUser) {
                this.token = savedToken;
                try {
                    this.user = JSON.parse(savedUser);
                    console.log('AuthManager: 从存储恢复认证状态', {
                        hasToken: !!this.token,
                        userId: this.user?.id
                    });
                } catch (e) {
                    console.error('解析用户信息失败:', e);
                    // 清除损坏的数据
                    this.clearStorage();
                }
            }

            // 加载会员信息
            try {
                const savedPlanInfo = this.getFromStorage('plan_info');
                if (savedPlanInfo) {
                    this.planInfo = JSON.parse(savedPlanInfo);
                }
            } catch (e) {
                console.warn('加载会员信息失败:', e);
            }

            // 更新UI
            this.updateUI();

        } catch (error) {
            console.error('AuthManager初始化失败:', error);
            // 清除可能损坏的数据
            this.logout();
        }
    }

    // 清除存储（移动端兼容）
    clearStorage() {
        try {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            localStorage.removeItem('plan_info');
        } catch (e) {
            console.warn('清除localStorage失败:', e);
        }
        try {
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('user_info');
            sessionStorage.removeItem('plan_info');
        } catch (e) {
            console.warn('清除sessionStorage失败:', e);
        }
    }

    // 注册
    async register(email, password, name, inviteCode = null) {
        // 防止重复提交（简单的防抖）
        if (this._registering) {
            console.warn('注册请求正在进行中，忽略重复请求');
            return { success: false, error: '注册请求正在进行中，请稍候...' };
        }

        this._registering = true;

        try {
            const registerData = { email, password, name };
            if (inviteCode && inviteCode.trim()) {
                registerData.invite_code = inviteCode.trim().toUpperCase();
            }

            console.log('发送注册请求:', { email, name, invite_code: registerData.invite_code || '无' });
            const response = await fetch(`${this.apiBaseUrl}/api/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(registerData)
            });

            console.log('注册响应状态:', response.status);
            const data = await response.json();
            console.log('注册响应数据:', data);

            // 只在成功时才保存认证信息
            if (response.ok && data.success !== false) {
                // 处理后端返回的数据结构
                const user = {
                    id: data.user_id || data.user?.id || data.user?.id,
                    email: data.email || data.user?.email,
                    name: data.name || data.user?.name,
                    plan: data.plan || data.user?.plan || 'free'
                };

                // 确保有有效的用户ID
                if (!user.id) {
                    console.error('注册成功但缺少用户ID:', data);
                    return { success: false, error: '注册成功但缺少用户信息' };
                }

                const token = data.token;
                if (!token) {
                    console.error('注册成功但缺少token:', data);
                    return { success: false, error: '注册成功但缺少认证token' };
                }

                this.setAuth(user, token);
                return { success: true, data };
            } else {
                // 注册失败，清除可能已保存的错误数据
                console.error('注册失败:', data);
                return { success: false, error: data.error || data.message || '注册失败' };
            }
        } catch (error) {
            console.error('注册请求异常:', error);
            return { success: false, error: '网络错误，请重试' };
        } finally {
            // 延迟解除防抖，防止快速重复提交
            setTimeout(() => {
                this._registering = false;
            }, 1000);
        }
    }

    // 登录
    async login(email, password) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();
            if (response.ok) {
                // 处理后端返回的数据结构
                const user = data.user || data;
                const token = data.token || 'dev-token-' + (user.id || 'unknown');
                this.setAuth(user, token);
                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: '网络错误，请重试' };
        }
    }

    // 获取微信登录二维码
    async getWechatQRCode() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/wechat-qrcode`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                return {
                    success: true,
                    session_id: data.session_id,
                    qrcode: data.qrcode,
                    auth_url: data.auth_url
                };
            } else {
                const errorMsg = data.error || '获取二维码失败';
                console.error('获取二维码失败:', errorMsg);
                return { success: false, error: errorMsg };
            }
        } catch (error) {
            console.error('获取二维码异常:', error);
            return { success: false, error: '获取二维码失败: ' + error.message };
        }
    }

    // 检查微信登录状态（轮询）
    async checkWechatLogin(sessionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/wechat-check-login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            const data = await response.json();

            if (data.success && data.status === 'success' && data.user && data.token) {
                // 登录成功，保存认证信息
                this.setAuth(data.user, data.token);
                console.log('微信登录成功:', data.user);
                return { success: true, status: 'success', data };
            } else if (data.status === 'waiting') {
                // 等待中
                return { success: false, status: 'waiting', message: data.message };
            } else if (data.status === 'failed') {
                // 失败
                return { success: false, status: 'failed', error: data.error };
            } else {
                return { success: false, status: 'unknown', error: '未知状态' };
            }
        } catch (error) {
            console.error('检查登录状态异常:', error);
            return { success: false, error: '检查登录状态失败: ' + error.message };
        }
    }

    // 微信登录（兼容旧接口，已废弃）
    async wechatLogin(code = null, state = null) {
        console.warn('wechatLogin方法已废弃，请使用二维码登录方式');
        return { success: false, error: '请使用二维码登录方式' };
    }

    // 保存到存储（移动端兼容）
    saveToStorage(key, value) {
        try {
            localStorage.setItem(key, value);
            // 同时保存到sessionStorage作为备份（移动端兼容）
            try {
                sessionStorage.setItem(key, value);
            } catch (e) {
                // sessionStorage也可能失败，忽略
            }
        } catch (e) {
            // 移动端某些情况下localStorage可能不可用，使用sessionStorage
            console.warn('localStorage不可用，使用sessionStorage:', e);
            try {
                sessionStorage.setItem(key, value);
            } catch (e2) {
                console.error('存储不可用:', e2);
            }
        }
    }

    // 从存储读取（移动端兼容）
    getFromStorage(key) {
        try {
            return localStorage.getItem(key) || sessionStorage.getItem(key);
        } catch (e) {
            try {
                return sessionStorage.getItem(key);
            } catch (e2) {
                console.error('存储读取失败:', e2);
                return null;
            }
        }
    }

    // 设置认证信息
    setAuth(user, token) {
        console.log('AuthManager.setAuth 被调用:', { user, token });

        this.user = user;
        this.token = token;

        // 统一使用固定的key保存（移动端兼容）
        this.saveToStorage('auth_token', token);
        this.saveToStorage('user_info', JSON.stringify(user));

        console.log('AuthManager: 认证信息已保存:', {
            savedToken: token,
            savedUser: user
        });

        this.updateUI();
    }

    // 退出登录（移动端兼容）
    logout() {
        this.user = null;
        this.token = null;
        this.planInfo = null;
        this.clearStorage();
        this.updateUI();
        window.location.href = '#login';
    }

    // 检查登录状态
    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    // 获取用户信息
    getUser() {
        return this.user;
    }

    // 获取token（移动端兼容）
    getToken() {
        if (this.token) {
            return this.token;
        }
        // 移动端兼容：从存储读取
        const savedToken = this.getFromStorage('auth_token');
        if (savedToken) {
            this.token = savedToken;
        }
        return savedToken;
    }

    // 获取认证头
    getAuthorizationHeader() {
        const token = this.getToken();
        if (!token) {
            console.warn('AuthManager: 没有找到token，无法设置Authorization头');
            return null;
        }
        return `Bearer ${token}`;
    }

    // 获取会员信息
    async getPlanInfo() {
        if (!this.isAuthenticated()) return null;

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/plan-info`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.planInfo = data.plan_info;
                this.saveToStorage('plan_info', JSON.stringify(data.plan_info));
                return data.plan_info;
            }
        } catch (error) {
            console.error('获取会员信息失败:', error);
        }
        return null;
    }

    // 更新用户信息
    async updateUserInfo() {
        if (!this.isAuthenticated()) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/user-info`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.user = data.user;
                this.saveToStorage('user_info', JSON.stringify(this.user));
                this.updateUI();
            }
        } catch (error) {
            console.error('更新用户信息失败:', error);
        }
    }

    // 升级会员计划
    async upgradePlan(newPlan) {
        if (!this.isAuthenticated()) return { success: false, error: '请先登录' };

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/auth/upgrade-plan`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ plan: newPlan })
            });

            const data = await response.json();
            if (response.ok) {
                // 更新用户信息
                this.user.plan = newPlan;
                this.saveToStorage('user_info', JSON.stringify(this.user));

                // 重新加载使用统计
                await this.loadUserUsageStats();
                this.updateUI();

                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: '网络错误，请重试' };
        }
    }

    // 更新UI
    updateUI() {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const userInfo = document.getElementById('userInfo');
        const userName = document.getElementById('userName');
        const userPlan = document.getElementById('userPlan');
        const userCredits = document.getElementById('userCredits');
        const logoutBtn = document.getElementById('logoutBtn');

        if (this.isAuthenticated()) {
            // 显示用户信息
            if (loginBtn) loginBtn.style.display = 'none';
            if (registerBtn) registerBtn.style.display = 'none';
            if (userInfo) userInfo.style.display = 'flex';

            // 修复用户名显示
            if (userName) {
                const displayName = this.user.name || this.user.email || '用户';
                userName.textContent = displayName;
                console.log('AuthManager设置用户名:', displayName); // 调试日志
            }

            if (userPlan) userPlan.textContent = this.getPlanDisplayName(this.user.plan);

            // 修复使用次数显示 - 移除硬编码，让loadUserUsageStats来处理
            if (userCredits) userCredits.textContent = '加载中...';

            if (logoutBtn) logoutBtn.style.display = 'block';

            // 加载会员信息和使用统计
            this.loadUserUsageStats();
        } else {
            // 显示登录注册按钮
            if (loginBtn) loginBtn.style.display = 'block';
            if (registerBtn) registerBtn.style.display = 'block';
            if (userInfo) userInfo.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'none';
        }
    }

    // 获取会员计划显示名称
    getPlanDisplayName(plan) {
        const planNames = {
            'free': '免费版',
            'basic': '基础版',
            'professional': '专业版',
            'flagship': '旗舰版',
            'enterprise': '企业版'
        };
        return planNames[plan] || '免费版';
    }

    // 加载用户使用统计
    async loadUserUsageStats() {
        if (!this.isAuthenticated()) {
            console.log('用户未认证，跳过加载使用统计');
            return;
        }

        // 检查token是否存在
        const token = this.getToken();
        if (!token) {
            console.warn('Token不存在，跳过加载使用统计');
            return;
        }

        try {
            console.log('正在加载用户使用统计...');
            const response = await fetch(`${this.apiBaseUrl}/api/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();

                console.log('📥 收到用户资料数据:', data);

                // 更新用户信息（从data.user获取）
                if (data.user) {
                    // 确保plan字段正确（优先使用plan，如果没有则使用membership_type）
                    const plan = data.user.plan || data.user.membership_type || 'free';

                    this.user = {
                        ...this.user,
                        ...data.user,
                        plan: plan,  // 确保plan字段正确
                        usage_stats: data.usage_stats
                    };
                } else {
                    // 兼容旧格式
                    const plan = data.plan || data.membership_type || 'free';
                    this.user = {
                        ...this.user,
                        ...data,
                        plan: plan,  // 确保plan字段正确
                        usage_stats: data.usage_stats
                    };
                }

                // 确保plan字段存在
                if (!this.user.plan) {
                    this.user.plan = 'free';
                }

                this.saveToStorage('user_info', JSON.stringify(this.user));

                // 更新使用统计显示
                if (data.usage_stats) {
                    this.updateUsageStatsDisplay(data.usage_stats);
                }

                // 更新UI显示（包括会员等级）
                this.updateUI();

                console.log('✅ 用户使用统计加载成功');
                console.log('📋 当前用户信息:', {
                    id: this.user.id,
                    email: this.user.email,
                    plan: this.user.plan,
                    membership_type: this.user.membership_type
                });
            } else if (response.status === 401) {
                // Token无效，清除认证信息（移动端优化：延迟清除，避免频繁操作）
                console.warn('Token无效（401），清除认证信息');
                // 移动端优化：延迟清除，避免影响用户体验
                setTimeout(() => {
                    this.logout();
                }, 1000);
            } else if (response.status === 403) {
                // 权限不足（移动端优化：显示友好提示）
                console.warn('权限不足（403）');
                // 不清除认证信息，可能是临时权限问题
            } else {
                console.error('加载用户使用统计失败:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('加载用户使用统计异常:', error);
            // 移动端优化：网络错误不立即清除认证信息
            if (error.message && error.message.includes('401')) {
                console.warn('Token无效，清除认证信息');
                setTimeout(() => {
                    this.logout();
                }, 1000);
            } else if (error.message && error.message.includes('网络')) {
                // 网络错误，不清除认证信息，可能是临时网络问题
                console.warn('网络错误，保留认证信息');
            }
        }
    }

    // 更新使用统计显示
    updateUsageStatsDisplay(usageStats) {
        if (!usageStats) return;

        // 修复：更新导航栏的使用次数显示
        const userCredits = document.getElementById('userCredits');
        if (userCredits) {
            // 如果usageStats有daily_limit和today_usage字段（总体统计）
            if (usageStats.daily_limit !== undefined && usageStats.today_usage !== undefined) {
                const totalUsage = usageStats.today_usage;
                const totalLimit = usageStats.daily_limit;
                const usageText = totalLimit > 0 ? `今日已用 ${totalUsage}/${totalLimit}` : '无限制';
                userCredits.textContent = usageText;
                console.log('AuthManager更新使用次数显示:', usageText);
            }
        }

        // 更新各个工具的使用次数显示
        const toolMappings = {
            'background_remover': 'bgRemover',
            'image_compressor': 'compressor',
            'format_converter': 'converter',
            'image_cropper': 'cropper'
        };

        Object.entries(toolMappings).forEach(([toolKey, prefix]) => {
            const stats = usageStats[toolKey];
            if (stats) {
                // 更新使用次数计数
                const countElement = document.getElementById(`${prefix}Count`);
                if (countElement) {
                    countElement.textContent = `${stats.current_usage}/${stats.daily_limit === -1 ? '∞' : stats.daily_limit}`;
                }

                // 更新进度条
                const progressElement = document.getElementById(`${prefix}Progress`);
                if (progressElement && stats.daily_limit > 0) {
                    const percentage = (stats.current_usage / stats.daily_limit) * 100;
                    progressElement.style.width = `${Math.min(percentage, 100)}%`;

                    // 根据使用率设置颜色
                    if (percentage >= 90) {
                        progressElement.style.backgroundColor = '#dc3545'; // 红色
                    } else if (percentage >= 70) {
                        progressElement.style.backgroundColor = '#ffc107'; // 黄色
                    } else {
                        progressElement.style.backgroundColor = '#28a745'; // 绿色
                    }
                } else if (progressElement && stats.daily_limit === -1) {
                    // 无限制时显示满进度条
                    progressElement.style.width = '100%';
                    progressElement.style.backgroundColor = '#007bff';
                }
            }
        });
    }

    // 检查工具使用权限
    async checkToolPermission(toolType) {
        if (!this.isAuthenticated()) {
            return { hasPermission: false, error: '请先登录' };
        }

        try {
            // 将前端工具类型映射到后端工具名称
            const toolMapping = {
                'background-remover': 'background_remover',
                'image-compressor': 'image_compressor',
                'format-converter': 'format_converter',
                'image-cropper': 'image_cropper'
            };

            const backendToolType = toolMapping[toolType] || toolType;

            // 使用专门的权限检查API
            const response = await fetch(`${this.apiBaseUrl}/api/auth/check-permission/${backendToolType}`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                return { hasPermission: false, error: '无法获取权限信息' };
            }

            const data = await response.json();

            if (!data.has_permission) {
                return {
                    hasPermission: false,
                    error: data.message || `今日使用次数已达上限(${data.daily_limit}次)`,
                    canUpgrade: data.can_upgrade
                };
            }

            return { hasPermission: true };
        } catch (error) {
            console.error('检查工具权限失败:', error);
            return { hasPermission: false, error: '网络错误，请重试' };
        }
    }

}

// 将类导出到全局作用域
window.AuthManager = AuthManager;