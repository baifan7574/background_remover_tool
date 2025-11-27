// 用户认证管理
// 自动检测环境：开发环境使用localhost，生产环境使用线上地址
const getApiBaseUrl = () => {
    // 如果访问 localhost，使用本地开发服务器
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    // 否则使用当前域名（生产环境）
    // 如果您的后端API在不同域名，请修改这里
    return window.location.origin; // 或者改为：'https://your-api-domain.com'
};

class AuthManager {
    constructor() {
        this.apiBaseUrl = getApiBaseUrl(); // 自动选择API地址
        this.token = null;
        this.user = null;
        this.planInfo = null;
        this.init();
    }

    // 初始化 - 从localStorage恢复认证状态
    init() {
        try {
            // 统一使用auth_token作为key
            const savedToken = localStorage.getItem('auth_token');
            const savedUser = localStorage.getItem('user_info');
            
            if (savedToken && savedUser) {
                this.token = savedToken;
                this.user = JSON.parse(savedUser);
                console.log('AuthManager: 从localStorage恢复认证状态', {
                    token: this.token,
                    user: this.user
                });
            }
            
            // 加载会员信息
            const savedPlanInfo = localStorage.getItem('plan_info');
            if (savedPlanInfo) {
                this.planInfo = JSON.parse(savedPlanInfo);
            }
            
            // 更新UI
            this.updateUI();
            
        } catch (error) {
            console.error('AuthManager初始化失败:', error);
            // 清除可能损坏的数据
            this.logout();
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

    // 微信登录
    async wechatLogin(code = null, state = null) {
        try {
            // 如果没有提供code，使用模拟的授权码（用于测试）
            const mockCode = code || 'mock_wechat_code_' + Date.now();
            const mockState = state || 'mock_wechat_state_' + Math.random().toString(36).substr(2, 9);
            
            console.log('开始微信登录，code:', mockCode);
            
            const response = await fetch(`${this.apiBaseUrl}/api/auth/wechat-login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code: mockCode, state: mockState })
            });

            const data = await response.json();
            
            if (response.ok && data.user && data.token) {
                // 登录成功，保存认证信息
                this.setAuth(data.user, data.token);
                console.log('微信登录成功:', data.user);
                return { success: true, data };
            } else {
                const errorMsg = data.error || data.message || '微信登录失败';
                console.error('微信登录失败:', errorMsg);
                return { success: false, error: errorMsg };
            }
        } catch (error) {
            console.error('微信登录异常:', error);
            return { success: false, error: '微信登录失败，请重试: ' + error.message };
        }
    }

    // 设置认证信息
    setAuth(user, token) {
        console.log('AuthManager.setAuth 被调用:', { user, token });
        
        this.user = user;
        this.token = token;
        
        // 统一使用固定的key保存到localStorage
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_info', JSON.stringify(user));
        
        console.log('AuthManager: 认证信息已保存到localStorage:', {
            savedToken: token,
            savedUser: user,
            localStorageToken: localStorage.getItem('auth_token'),
            localStorageUser: localStorage.getItem('user_info')
        });
        
        this.updateUI();
    }

    // 退出登录
    logout() {
        this.user = null;
        this.token = null;
        this.planInfo = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        localStorage.removeItem('plan_info');
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

    // 获取token
    getToken() {
        return this.token;
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
                localStorage.setItem('plan_info', JSON.stringify(data.plan_info));
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
                localStorage.setItem('user_info', JSON.stringify(this.user));
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
                localStorage.setItem('user_info', JSON.stringify(this.user));
                
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
                
                localStorage.setItem('user_info', JSON.stringify(this.user));
                
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
                // Token无效，清除认证信息
                console.warn('Token无效，清除认证信息');
                this.logout();
            } else {
                console.error('加载用户使用统计失败:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('加载用户使用统计异常:', error);
            // 如果是401错误，清除认证信息
            if (error.message && error.message.includes('401')) {
                console.warn('Token无效，清除认证信息');
                this.logout();
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