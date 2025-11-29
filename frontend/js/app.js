// ========== 水印功能调试版本 - 2025-11-27 ==========
console.log('🎯🎯🎯 app.js 文件已加载！版本：水印调试版 - 请检查这个日志是否出现！');
// ================================================

// 前端应用主逻辑
// 自动检测环境：开发环境使用localhost，生产环境使用线上地址

const getAppApiBaseUrl = () => {
    // 如果访问 localhost，使用本地开发服务器
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    // 否则使用当前域名（生产环境）
    // 如果您的后端API在不同域名，请修改这里
    return window.location.origin; // 或者改为：'https://your-api-domain.com'
};

/**
 * 安全地解析API响应为JSON
 * 如果响应不是JSON格式（比如HTML错误页面），会返回友好的错误信息
 * @param {Response} response - Fetch API响应对象
 * @param {string} apiUrl - 请求的API URL（用于错误提示）
 * @returns {Promise<Object>} 解析后的JSON对象
 */
async function safeParseJsonResponse(response, apiUrl = '') {
    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('application/json')) {
        try {
            return await response.json();
        } catch (jsonError) {
            console.error('❌ JSON解析失败:', jsonError);
            const errorText = await response.text();
            console.error('响应内容（前500字符）:', errorText.substring(0, 500));
            throw new Error(`服务器返回了无效的JSON响应（状态码: ${response.status}）。请检查网络连接或联系客服。`);
        }
    } else {
        // 非JSON响应（可能是HTML错误页面）
        const responseText = await response.text();
        console.error('❌ 服务器返回了非JSON响应');
        console.error('响应类型:', contentType);
        console.error('响应状态:', response.status, response.statusText);
        console.error('响应内容（前500字符）:', responseText.substring(0, 500));
        console.error('请求URL:', apiUrl);
        
        // 根据状态码提供友好的错误信息
        let errorMessage = '服务器返回了意外的响应格式';
        if (response.status === 404) {
            errorMessage = `API接口不存在（404）。\n\n可能的原因：\n1. 服务器配置错误\n2. API路径不正确\n3. 网络连接问题\n\n请求URL: ${apiUrl}`;
        } else if (response.status === 500) {
            errorMessage = '服务器内部错误（500）。请稍后重试或联系客服。';
        } else if (response.status === 401) {
            errorMessage = '认证失败（401）。请重新登录。';
        } else if (response.status === 403) {
            errorMessage = '访问被拒绝（403）。请检查您的权限或联系客服。';
        } else if (response.status >= 400) {
            errorMessage = `服务器错误（${response.status}）。请检查网络连接或联系客服。`;
        }
        
        throw new Error(errorMessage);
    }
}

class AppManager {
    constructor() {
        this.authManager = new AuthManager();
        this.currentTool = null;
        this.apiBaseUrl = getAppApiBaseUrl(); // 自动选择API地址
        this.isProcessing = false; // 添加处理状态标识
        this.progressInterval = null; // 添加进度间隔标识
        this.currentUploadArea = null; // 添加当前上传区域引用
        this.currentFileInput = null; // 添加当前文件输入引用
        
        // 批量处理相关属性
        this.batchFiles = [];
        this.batchResults = [];
        this.isBatchProcessing = false;
        this.batchProgress = {
            current: 0,
            total: 0,
            completed: 0,
            errors: 0
        };
        
        this.init();
    }

    init() {
        // 确保DOM加载完成后再初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.doInit();
            });
        } else {
            this.doInit();
        }
    }
    
    doInit() {
        console.log('开始初始化AppManager...');
        
        // 确保DOM完全加载后再初始化事件
        if (document.readyState === 'complete') {
            this.initComponents();
        } else {
            window.addEventListener('load', () => {
                this.initComponents();
            });
        }
    }

    initComponents() {
        // 初始化应用
        this.setupEventListeners();
        this.checkAuthStatus();
        this.setupSmoothScroll();
        this.setupNavbarScroll();
        this.enhanceUpgradeButton();
        
        // 检查URL中的邀请码参数
        this.checkInviteCodeFromURL();
        
        // 加载用户统计（如果已登录）
        if (this.authManager.isAuthenticated()) {
            this.loadUsageStats();
        }
        
        console.log('AppManager初始化完成');
    }
    
    checkInviteCodeFromURL() {
        // 从URL参数中获取邀请码
        const urlParams = new URLSearchParams(window.location.search);
        const inviteCode = urlParams.get('invite');
        if (inviteCode) {
            // 保存到localStorage，注册时自动填充
            localStorage.setItem('pending_invite_code', inviteCode.toUpperCase());
            console.log('检测到邀请码:', inviteCode);
        }
    }
    
    switchToRegister() {
        // 切换到注册表单
        this.closeModal('loginModal');
        setTimeout(() => {
            this.showModal('registerModal');
            
            // 自动填充邀请码（如果有）
            const pendingInviteCode = localStorage.getItem('pending_invite_code');
            const inviteInput = document.getElementById('registerInviteCode');
            if (pendingInviteCode && inviteInput) {
                inviteInput.value = pendingInviteCode;
            }
        }, 300);
    }
    
    showRegisterModal() {
        const modal = document.getElementById('registerModal');
        if (modal) {
            this.showModal(modal);
            
            // 自动填充邀请码（如果有）
            const pendingInviteCode = localStorage.getItem('pending_invite_code');
            const inviteInput = document.getElementById('registerInviteCode');
            if (pendingInviteCode && inviteInput) {
                inviteInput.value = pendingInviteCode;
            }
        }
    }
    
    // 微信登录功能暂时隐藏（需要微信开放平台认证，费用300元）
    // 等后续开通微信登录后再取消注释
    /*
    async showWechatLoginModal() {
        // 关闭其他模态框
        this.closeModal('loginModal');
        this.closeModal('registerModal');
        
        // 显示微信登录模态框
        const modal = document.getElementById('wechatLoginModal');
        if (modal) {
            this.showModal(modal);
            
            // 获取并显示二维码
            await this.loadWechatQRCode();
        } else {
            console.error('未找到微信登录模态框');
        }
    }
    
    async loadWechatQRCode() {
        const qrCodeContainer = document.querySelector('#wechatLoginModal .qr-code');
        const qrPlaceholder = document.querySelector('#wechatLoginModal .qr-placeholder');
        
        if (!qrCodeContainer) {
            console.error('未找到二维码容器');
            return;
        }
        
        // 显示加载状态
        if (qrPlaceholder) {
            qrPlaceholder.innerHTML = '<div class="qr-icon">⏳</div><p>正在生成二维码...</p>';
            qrPlaceholder.style.display = 'block';
        }
        
        try {
            // 获取二维码
            const result = await this.authManager.getWechatQRCode();
            
            if (result.success) {
                // 显示二维码
                if (qrPlaceholder) {
                    qrPlaceholder.style.display = 'none';
                }
                
                const img = document.createElement('img');
                img.src = result.qrcode;
                img.style.width = '100%';
                img.style.height = 'auto';
                img.style.maxWidth = '300px';
                img.style.margin = '0 auto';
                img.style.display = 'block';
                
                // 清空容器并添加二维码图片
                qrCodeContainer.innerHTML = '';
                qrCodeContainer.appendChild(img);
                
                // 保存session_id并开始轮询
                this.wechatSessionId = result.session_id;
                this.startWechatLoginPolling();
            } else {
                // 显示错误
                if (qrPlaceholder) {
                    qrPlaceholder.innerHTML = `
                        <div class="qr-icon">❌</div>
                        <p>${result.error || '获取二维码失败'}</p>
                        <button class="btn btn-primary" onclick="window.appManager.loadWechatQRCode()" style="margin-top: 10px;">重试</button>
                    `;
                    qrPlaceholder.style.display = 'block';
                }
                console.error('获取二维码失败:', result.error);
            }
        } catch (error) {
            console.error('获取二维码异常:', error);
            if (qrPlaceholder) {
                qrPlaceholder.innerHTML = `
                    <div class="qr-icon">❌</div>
                    <p>获取二维码失败</p>
                    <button class="btn btn-primary" onclick="window.appManager.loadWechatQRCode()" style="margin-top: 10px;">重试</button>
                `;
                qrPlaceholder.style.display = 'block';
            }
        }
    }
    
    startWechatLoginPolling() {
        // 清除之前的轮询
        if (this.wechatPollingInterval) {
            clearInterval(this.wechatPollingInterval);
        }
        
        // 更新提示文字
        const instructions = document.querySelector('#wechatLoginModal .qr-instructions');
        if (instructions) {
            instructions.innerHTML = `
                <h4>扫码登录步骤：</h4>
                <ol>
                    <li>打开微信扫一扫</li>
                    <li>扫描上方二维码</li>
                    <li>确认登录授权</li>
                </ol>
                <p style="color: #1890ff; margin-top: 10px;">⏳ 等待扫码中...</p>
            `;
        }
        
        // 开始轮询检查登录状态
        let pollCount = 0;
        const maxPolls = 120; // 最多轮询2分钟（每1秒一次）
        
        this.wechatPollingInterval = setInterval(async () => {
            pollCount++;
            
            if (!this.wechatSessionId) {
                clearInterval(this.wechatPollingInterval);
                return;
            }
            
            // 检查登录状态
            const result = await this.authManager.checkWechatLogin(this.wechatSessionId);
            
            if (result.success && result.status === 'success') {
                // 登录成功
                clearInterval(this.wechatPollingInterval);
                this.wechatSessionId = null;
                
                // 更新提示
                if (instructions) {
                    instructions.innerHTML = '<p style="color: #52c41a; font-weight: bold;">✅ 登录成功！</p>';
                }
                
                // 关闭模态框
                setTimeout(() => {
                    this.closeModal('wechatLoginModal');
                    
                    // 显示成功提示
                    alert('✅ 微信登录成功！\n\n欢迎 ' + (result.data?.user?.name || result.data?.user?.email || '用户'));
                    
                    // 刷新页面以更新UI
                    window.location.reload();
                }, 1000);
            } else if (result.status === 'failed') {
                // 登录失败
                clearInterval(this.wechatPollingInterval);
                this.wechatSessionId = null;
                
                if (instructions) {
                    instructions.innerHTML = `
                        <p style="color: #ff4d4f; font-weight: bold;">❌ 登录失败</p>
                        <p>${result.error || '授权失败'}</p>
                        <button class="btn btn-primary" onclick="window.appManager.loadWechatQRCode()" style="margin-top: 10px;">重新获取二维码</button>
                    `;
                }
            } else if (pollCount >= maxPolls) {
                // 超时
                clearInterval(this.wechatPollingInterval);
                this.wechatSessionId = null;
                
                if (instructions) {
                    instructions.innerHTML = `
                        <p style="color: #ff9800; font-weight: bold;">⏰ 二维码已过期</p>
                        <button class="btn btn-primary" onclick="window.appManager.loadWechatQRCode()" style="margin-top: 10px;">重新获取二维码</button>
                    `;
                }
            }
        }, 1000); // 每1秒检查一次
    }
    */
    
    // switchToTraditionalLogin 方法保留，但简化（不涉及微信登录）
    switchToTraditionalLogin() {
        // 显示传统登录模态框
        setTimeout(() => {
            this.showLoginModal();
        }, 300);
    }

    setupEventListeners() {
        // 延迟执行，确保DOM完全加载
        setTimeout(() => {
            // 工具卡片点击事件 - 使用更可靠的选择器
            const toolButtons = document.querySelectorAll('.tool-btn, [data-tool]');
            console.log('找到工具按钮数量:', toolButtons.length);
            
            toolButtons.forEach(btn => {
                // 避免重复绑定
                if (!btn.hasAttribute('data-event-bound')) {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // 从data-tool属性获取工具类型
                        const toolType = btn.dataset.tool || btn.getAttribute('data-tool');
                        console.log('工具按钮被点击:', toolType, 'appManager:', window.appManager);
                        
                        if (toolType && window.appManager) {
                            window.appManager.openTool(toolType);
                        } else {
                            console.warn('未找到工具类型或appManager未初始化', {toolType, appManager: window.appManager});
                        }
                    });
                    
                    // 标记已绑定事件
                    btn.setAttribute('data-event-bound', 'true');
                }
            });
            
            // 也为工具卡片本身添加点击事件（但只在点击卡片空白处时触发）
            const toolCards = document.querySelectorAll('.tool-card');
            console.log('找到工具卡片数量:', toolCards.length);
            
            toolCards.forEach(card => {
                if (!card.hasAttribute('data-event-bound')) {
                    card.addEventListener('click', (e) => {
                        // 如果点击的是按钮、链接或其他交互元素，不处理
                        if (e.target.classList.contains('tool-btn') || 
                            e.target.closest('.tool-btn') ||
                            e.target.tagName === 'BUTTON' ||
                            e.target.tagName === 'A' ||
                            e.target.closest('button') ||
                            e.target.closest('a')) {
                            return;
                        }
                        
                        const toolType = card.dataset.tool;
                        console.log('工具卡片被点击:', toolType, 'appManager:', window.appManager);
                        
                        if (toolType && window.appManager) {
                            window.appManager.openTool(toolType);
                        }
                    });
                    
                    card.setAttribute('data-event-bound', 'true');
                }
            });
        }, 200); // 延迟200ms确保DOM和window.appManager都已初始化

        // 模态框关闭事件
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.closeModal(modal);
            });
        });

        // 点击模态框外部关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        });

        // 登录/注册按钮
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        
        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.showLoginModal());
        }
        
        if (registerBtn) {
            registerBtn.addEventListener('click', () => this.showRegisterModal());
        }

        // 用户菜单
        const userMenu = document.getElementById('userMenu');
        if (userMenu) {
            userMenu.addEventListener('click', () => this.toggleUserMenu());
        }

        // 升级会员按钮
        const upgradeBtn = document.getElementById('upgradeBtn');
        if (upgradeBtn) {
            upgradeBtn.addEventListener('click', () => this.showUpgradeModal());
        }

        // 表单提交事件
        this.setupFormListeners();
        
        // 批量处理事件监听器
        this.setupBatchEventListeners();
    }

    setupBatchEventListeners() {
        // 批量模式切换
        const batchModeToggle = document.getElementById('batchMode');
        if (batchModeToggle) {
            batchModeToggle.addEventListener('change', (e) => {
                this.toggleBatchMode(e.target.checked);
            });
        }
        
        // 批量文件输入
        const batchFileInput = document.getElementById('batchFileInput');
        if (batchFileInput) {
            batchFileInput.addEventListener('change', (e) => {
                this.handleBatchFileSelect(e.target.files);
            });
        }
    }

    setupFormListeners() {
        // 登录表单
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleLogin(e);
            });
        }

        // 注册表单
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleRegister(e);
            });
        }
    }

    setupSmoothScroll() {
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const href = anchor.getAttribute('href');
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    setupNavbarScroll() {
        // 导航栏滚动效果
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const navbar = document.querySelector('.navbar');
            const currentScroll = window.pageYOffset;
            
            if (navbar) {
                if (currentScroll > lastScroll && currentScroll > 100) {
                    navbar.style.transform = 'translateY(-100%)';
                } else {
                    navbar.style.transform = 'translateY(0)';
                }
            }
            
            lastScroll = currentScroll;
        });
    }

    enhanceUpgradeButton() {
        // 升级按钮增强效果
        const upgradeBtn = document.getElementById('upgradeBtn');
        if (upgradeBtn) {
            upgradeBtn.addEventListener('mouseenter', () => {
                upgradeBtn.style.transform = 'scale(1.05)';
            });
            
            upgradeBtn.addEventListener('mouseleave', () => {
                upgradeBtn.style.transform = 'scale(1)';
            });
        }
    }

    checkAuthStatus() {
        const token = this.authManager.getToken();
        if (token) {
            this.updateUIForLoggedInUser();
        } else {
            this.updateUIForLoggedOutUser();
        }
    }

    updateUIForLoggedInUser() {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const userInfo = document.getElementById('userInfo');
        const userMenu = document.getElementById('userMenu');
        const upgradeBtn = document.getElementById('upgradeBtn');
        const inviteBtn = document.getElementById('inviteBtn');
        const heroInviteBtn = document.getElementById('heroInviteBtn');
        const inviteBanner = document.getElementById('inviteBanner');
        
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        if (userInfo) userInfo.style.display = 'flex';
        if (userMenu) userMenu.style.display = 'block';
        if (upgradeBtn) upgradeBtn.style.display = 'block';
        
        // 显示邀请相关按钮和横幅
        if (inviteBtn) inviteBtn.style.display = 'inline-block';
        if (heroInviteBtn) heroInviteBtn.style.display = 'inline-block';
        if (inviteBanner) inviteBanner.style.display = 'block';
        
        // 更新用户信息显示
        if (this.authManager.user && userInfo) {
            const userName = userInfo.querySelector('.user-name');
            const userPlan = userInfo.querySelector('.user-plan');
            if (userName) userName.textContent = this.authManager.user.name || '用户';
            if (userPlan) {
                // 确保使用正确的plan字段
                const userPlanValue = this.authManager.user.plan || this.authManager.user.membership_type || 'free';
                const planName = this.getPlanName ? this.getPlanName(userPlanValue) : (userPlanValue === 'free' ? '免费版' : userPlanValue);
                userPlan.textContent = planName;
                console.log('📋 更新导航栏会员等级:', { plan: userPlanValue, planName: planName });
            }
        }
        
        // 加载邀请信息（在导航栏和横幅显示）
        this.loadInviteInfo();
    }

    updateUIForLoggedOutUser() {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const userInfo = document.getElementById('userInfo');
        const userMenu = document.getElementById('userMenu');
        const upgradeBtn = document.getElementById('upgradeBtn');
        const inviteBtn = document.getElementById('inviteBtn');
        const heroInviteBtn = document.getElementById('heroInviteBtn');
        const inviteBanner = document.getElementById('inviteBanner');
        
        if (loginBtn) loginBtn.style.display = 'block';
        if (registerBtn) registerBtn.style.display = 'block';
        if (userInfo) userInfo.style.display = 'none';
        if (userMenu) userMenu.style.display = 'none';
        if (upgradeBtn) upgradeBtn.style.display = 'none';
        
        // 隐藏邀请相关按钮和横幅
        if (inviteBtn) inviteBtn.style.display = 'none';
        if (heroInviteBtn) heroInviteBtn.style.display = 'none';
        if (inviteBanner) inviteBanner.style.display = 'none';
    }

    openTool(toolType) {
        console.log('🚀🚀🚀 openTool被调用，工具类型:', toolType);
        if (toolType === 'add_watermark' || toolType === 'add_watermark_v2') {
            console.log('🎯🎯🎯 这是水印工具！水印工具被打开了！工具类型:', toolType);
        }
        
        // 如果已经在处理中，不允许重复打开
        if (this.isProcessing) {
            console.log('正在处理中，忽略重复请求');
            return;
        }
        
        // 检查用户权限 - 必须已登录
        if (!this.authManager.isAuthenticated()) {
            console.warn('用户未登录，显示登录对话框');
            // 直接显示登录模态框，不使用alert（避免阻塞和多次点击问题）
            this.showLoginModal();
            return;
        }
        
        // 检查token是否存在
        const token = this.authManager.getToken();
        if (!token) {
            console.error('用户已登录但token不存在，需要重新登录');
            // 直接显示登录模态框，不使用alert（避免阻塞和多次点击问题）
            this.authManager.logout();
            this.showLoginModal();
            return;
        }
        
        console.log('✅ 用户已登录，token存在:', token.substring(0, 20) + '...');

        // 如果模态框已经打开，先关闭
        const existingModal = document.getElementById('toolModal');
        if (existingModal && existingModal.style.display === 'flex') {
            this.closeModal(existingModal);
            // 稍等一下再打开新工具，避免冲突
            setTimeout(() => {
                this._doOpenTool(toolType);
            }, 100);
            return;
        }
        
        this._doOpenTool(toolType);
    }
    
    _doOpenTool(toolType) {
        this.currentTool = toolType;
        const modal = document.getElementById('toolModal');
        if (!modal) {
            console.error('找不到toolModal元素');
            alert('工具模态框未找到，请刷新页面重试');
            return;
        }
        
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = modal.querySelector('.modal-body');
        
        if (!modalBody) {
            console.error('找不到modal-body元素');
            return;
        }

        // 设置标题
        const titles = {
            'background_remover': '背景移除工具',
            'image_compressor': '图片压缩工具',
            'format_converter': '格式转换工具',
            'image_cropper': '图片裁剪工具',
            'image_rotate_flip': '图片旋转/翻转工具',
            'keyword_analyzer': '关键词分析工具',
            'listing_generator': 'Listing文案生成工具',
            'currency_converter': '汇率换算工具',
            'add_watermark': '加水印工具',
            'add_watermark_v2': '加水印工具（新版）',
            'remove_watermark': '去水印工具'
        };
        
        modalTitle.textContent = titles[toolType] || '图片处理工具';

        // 重置上传区域
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        if (uploadArea) {
            uploadArea.style.display = 'block';
            uploadArea.classList.remove('has-file');
        }
        
        if (fileInput) {
            fileInput.value = '';
        }

        // 重置批量处理状态
        this.batchFiles = [];
        this.batchResults = [];
        this.isBatchProcessing = false;

        // 根据工具类型设置不同的选项
        this.setupToolOptions(toolType);

        // 关键词分析工具、Listing文案生成和汇率换算工具不需要文件上传，需要特殊处理
        if (toolType === 'keyword_analyzer' || toolType === 'listing_generator' || toolType === 'currency_converter') {
            // 隐藏文件上传区域，显示文本输入
            if (uploadArea) uploadArea.style.display = 'none';
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                // 先清理之前的按钮，避免重复显示
                const existingBtnContainers = modalBody.querySelectorAll('.tool-actions');
                existingBtnContainers.forEach(container => container.remove());
                
                // 根据工具类型添加对应的按钮
                if (toolType === 'keyword_analyzer') {
                    // 为关键词分析工具添加开始分析按钮
                    setTimeout(() => {
                        let startButton = document.getElementById('keywordAnalyzeBtn');
                        if (!startButton) {
                            const btnContainer = document.createElement('div');
                            btnContainer.className = 'tool-actions';
                            btnContainer.id = 'keywordAnalyzeBtnContainer';
                            btnContainer.innerHTML = `
                                <button id="keywordAnalyzeBtn" class="btn btn-primary" style="margin-top: 20px; width: 100%; padding: 12px;">
                                    <i class="fas fa-search"></i> 开始分析
                                </button>
                            `;
                            const toolOptions = document.getElementById('toolOptions');
                            if (toolOptions && toolOptions.nextSibling) {
                                toolOptions.parentNode.insertBefore(btnContainer, toolOptions.nextSibling);
                            } else if (toolOptions) {
                                toolOptions.parentNode.appendChild(btnContainer);
                            } else {
                                modalBody.appendChild(btnContainer);
                            }
                        }
                        
                        // 绑定分析按钮事件
                        startButton = document.getElementById('keywordAnalyzeBtn');
                        if (startButton) {
                            startButton.onclick = () => this.processKeywordAnalysis();
                        }
                    }, 100);
                } else if (toolType === 'listing_generator') {
                    // 为Listing文案生成工具添加生成按钮
                    setTimeout(() => {
                        let startButton = document.getElementById('listingGenerateBtn');
                        if (!startButton) {
                            const btnContainer = document.createElement('div');
                            btnContainer.className = 'tool-actions';
                            btnContainer.id = 'listingGenerateBtnContainer';
                            btnContainer.innerHTML = `
                                <button id="listingGenerateBtn" class="btn btn-primary" style="margin-top: 20px; width: 100%; padding: 12px;">
                                    <i class="fas fa-magic"></i> 生成文案
                                </button>
                            `;
                            const toolOptions = document.getElementById('toolOptions');
                            if (toolOptions && toolOptions.nextSibling) {
                                toolOptions.parentNode.insertBefore(btnContainer, toolOptions.nextSibling);
                            } else if (toolOptions) {
                                toolOptions.parentNode.appendChild(btnContainer);
                            } else {
                                modalBody.appendChild(btnContainer);
                            }
                        }
                        
                        // 绑定生成按钮事件
                        startButton = document.getElementById('listingGenerateBtn');
                        if (startButton) {
                            startButton.onclick = () => this.processListingGeneration();
                        }
                    }, 100);
                } else if (toolType === 'currency_converter') {
                    // 为汇率换算工具添加开始换算按钮
                    setTimeout(() => {
                        let startButton = document.getElementById('currencyConvertBtn');
                        if (!startButton) {
                            const btnContainer = document.createElement('div');
                            btnContainer.className = 'tool-actions';
                            btnContainer.id = 'currencyConvertBtnContainer';
                            btnContainer.innerHTML = `
                                <button id="currencyConvertBtn" class="btn btn-primary" style="margin-top: 20px; width: 100%; padding: 12px;">
                                    <i class="fas fa-exchange-alt"></i> 开始换算
                                </button>
                            `;
                            const toolOptions = document.getElementById('toolOptions');
                            if (toolOptions && toolOptions.nextSibling) {
                                toolOptions.parentNode.insertBefore(btnContainer, toolOptions.nextSibling);
                            } else if (toolOptions) {
                                toolOptions.parentNode.appendChild(btnContainer);
                            } else {
                                modalBody.appendChild(btnContainer);
                            }
                        }
                        
                        // 绑定换算按钮事件
                        startButton = document.getElementById('currencyConvertBtn');
                        if (startButton) {
                            startButton.onclick = () => this.processCurrencyConversion();
                        }
                    }, 100);
                }
            }
        } else {
            // 其他工具使用文件上传
            if (uploadArea) uploadArea.style.display = 'block';
            this.setupFileUpload(toolType);
        }

        // 显示模态框
        this.showModal(modal);
    }

    setupToolOptions(toolType) {
        const optionsContainer = document.getElementById('toolOptions');
        
        if (!optionsContainer) return;

        let optionsHTML = '';

        switch(toolType) {
            case 'image_compressor':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="compressQuality">压缩质量:</label>
                            <input type="range" id="compressQuality" min="1" max="100" value="85" class="form-range">
                            <span id="compressQualityValue">85%</span>
                        </div>
                        <div class="option-group">
                            <label for="compressFormat">输出格式:</label>
                            <select id="compressFormat" class="form-select">
                                <option value="JPEG">JPEG</option>
                                <option value="PNG">PNG</option>
                                <option value="WEBP">WEBP</option>
                            </select>
                        </div>
                        <div class="option-group">
                            <label for="maxSize">最大文件大小 (KB):</label>
                            <input type="number" id="maxSize" min="1" max="5000" placeholder="留空则不限制">
                        </div>
                    </div>
                `;
                break;
            case 'format_converter':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="outputFormat">输出格式:</label>
                            <select id="outputFormat" class="form-select">
                                <option value="PNG">PNG</option>
                                <option value="JPEG">JPEG</option>
                                <option value="WEBP">WEBP</option>
                                <option value="BMP">BMP</option>
                                <option value="GIF">GIF</option>
                            </select>
                        </div>
                        <div class="option-group">
                            <label for="convertQuality">质量:</label>
                            <input type="range" id="convertQuality" min="1" max="100" value="95" class="form-range">
                            <span id="convertQualityValue">95%</span>
                        </div>
                    </div>
                `;
                break;
            case 'image_cropper':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="cropPreset">预设尺寸:</label>
                            <select id="cropPreset" class="form-select">
                                <option value="free">自由裁剪</option>
                                <option value="1:1">1:1 (正方形)</option>
                                <option value="16:9">16:9 (宽屏)</option>
                                <option value="4:3">4:3 (标准)</option>
                                <option value="taobao">淘宝主图 (800x800)</option>
                                <option value="jd">京东商品 (800x800)</option>
                                <option value="pdd">拼多多 (750x1000)</option>
                                <option value="amazon">亚马逊主图 (1000x1000)</option>
                                <option value="temu">Temu主图 (800x800)</option>
                                <option value="shopee">虾皮主图 (800x800)</option>
                            </select>
                        </div>
                    </div>
                `;
                break;
            case 'keyword_analyzer':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="keywordAction">功能选择:</label>
                            <select id="keywordAction" class="form-select">
                                <option value="extract">关键词提取</option>
                                <option value="competition">竞争度查询</option>
                                <option value="trend">趋势分析</option>
                                <option value="compare">竞品对比</option>
                                <option value="longtail">长尾关键词挖掘</option>
                            </select>
                        </div>
                        <div class="option-group" id="productDescriptionGroup">
                            <label for="productDescription">产品描述:</label>
                            <textarea id="productDescription" class="form-textarea" rows="3" placeholder="输入产品描述或关键词，例如：Wireless Bluetooth Headphones with Noise Cancellation"></textarea>
                        </div>
                        <div class="option-group" id="platformGroup" style="display: none;">
                            <label for="targetPlatform">目标平台:</label>
                            <select id="targetPlatform" class="form-select">
                                <option value="amazon">亚马逊 (Amazon)</option>
                                <option value="ebay">eBay</option>
                                <option value="temu">Temu</option>
                                <option value="shopee">虾皮 (Shopee)</option>
                                <option value="all">所有平台</option>
                            </select>
                        </div>
                        <div class="option-group" id="competitorAsinGroup" style="display: none;">
                            <label for="competitorAsin">竞品ASIN:</label>
                            <input type="text" id="competitorAsin" class="form-input" placeholder="输入竞品的ASIN，例如：B08XYZ1234">
                        </div>
                    </div>
                `;
                break;
            case 'listing_generator':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="listingProductInfo">产品信息:</label>
                            <textarea id="listingProductInfo" class="form-textarea" rows="4" placeholder="输入产品信息，例如：无线蓝牙耳机，支持主动降噪，30小时续航，快速充电，适合运动健身使用"></textarea>
                        </div>
                        <div class="option-group">
                            <label for="listingPlatform">目标平台:</label>
                            <select id="listingPlatform" class="form-select">
                                <option value="amazon">亚马逊 (Amazon)</option>
                                <option value="ebay">eBay</option>
                                <option value="temu">Temu</option>
                                <option value="shopee">虾皮 (Shopee)</option>
                            </select>
                        </div>
                        <div class="option-group">
                            <label for="listingLanguage">输出语言:</label>
                            <select id="listingLanguage" class="form-select">
                                <option value="en">英文 (English)</option>
                                <option value="zh">中文 (Chinese)</option>
                            </select>
                        </div>
                        <div class="option-group">
                            <label for="listingStyle">文案风格:</label>
                            <select id="listingStyle" class="form-select">
                                <option value="professional">专业风格</option>
                                <option value="casual">轻松风格</option>
                                <option value="marketing">营销风格</option>
                            </select>
                        </div>
                    </div>
                `;
                break;
            case 'currency_converter':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="currencyAmount">金额:</label>
                            <input type="number" id="currencyAmount" class="form-input" placeholder="输入金额" step="0.01" min="0">
                        </div>
                        <div class="option-group">
                            <label for="fromCurrency">源货币:</label>
                            <select id="fromCurrency" class="form-select">
                                <option value="CNY">人民币 (CNY)</option>
                                <option value="USD">美元 (USD)</option>
                                <option value="EUR">欧元 (EUR)</option>
                                <option value="GBP">英镑 (GBP)</option>
                                <option value="JPY">日元 (JPY)</option>
                                <option value="HKD">港币 (HKD)</option>
                                <option value="SGD">新加坡元 (SGD)</option>
                                <option value="TWD">新台币 (TWD)</option>
                            </select>
                        </div>
                        <div class="option-group">
                            <label for="toCurrency">目标货币:</label>
                            <select id="toCurrency" class="form-select">
                                <option value="USD">美元 (USD)</option>
                                <option value="CNY">人民币 (CNY)</option>
                                <option value="EUR">欧元 (EUR)</option>
                                <option value="GBP">英镑 (GBP)</option>
                                <option value="JPY">日元 (JPY)</option>
                                <option value="HKD">港币 (HKD)</option>
                                <option value="SGD">新加坡元 (SGD)</option>
                                <option value="TWD">新台币 (TWD)</option>
                            </select>
                        </div>
                    </div>
                `;
                break;
            // ========== 旧版水印功能（已注释）==========
            // case 'add_watermark':
            //     ...
            //     break;
            
            // ========== 新版水印功能（简化版）==========
            case 'add_watermark_v2':
                console.log('🎯🎯🎯 创建新版水印工具界面');
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label for="watermarkTextV2">水印文字:</label>
                            <input type="text" id="watermarkTextV2" class="form-input" placeholder="输入水印文字，例如：© 2025 或 版权所有" value="© 2025">
                        </div>
                        <div class="option-group">
                            <label for="watermarkPositionV2">水印位置:</label>
                            <select id="watermarkPositionV2" class="form-select">
                                <option value="top-left">左上角</option>
                                <option value="top-right">右上角</option>
                                <option value="bottom-left">左下角</option>
                                <option value="bottom-right" selected>右下角</option>
                                <option value="center">居中</option>
                            </select>
                        </div>
                        <div class="option-group">
                            <label for="watermarkOpacityV2">透明度:</label>
                            <input type="range" id="watermarkOpacityV2" min="0.1" max="1" step="0.1" value="0.7" class="form-range" oninput="document.getElementById('watermarkOpacityValueV2').textContent = Math.round(this.value * 100) + '%'">
                            <span id="watermarkOpacityValueV2">70%</span>
                        </div>
                        <div class="option-group">
                            <label for="watermarkFontSizeV2">字体大小:</label>
                            <input type="number" id="watermarkFontSizeV2" class="form-input" min="10" max="200" value="50">
                        </div>
                        <div class="option-group">
                            <label for="watermarkColorV2">字体颜色:</label>
                            <input type="color" id="watermarkColorV2" class="form-input" value="#000000">
                        </div>
                    </div>
                `;
                console.log('✅ 新版水印工具界面创建完成');
                break;
            case 'remove_watermark':
                optionsHTML = `
                    <div class="tool-options">
                        <div class="option-group">
                            <label>提示：上传图片后，系统将自动智能识别并移除水印</label>
                        </div>
                    </div>
                `;
                break;
        }

        optionsContainer.innerHTML = optionsHTML;
        
        // 为加水印工具添加事件监听器
        if (toolType === 'add_watermark') {
            const opacitySlider = document.getElementById('watermarkOpacity');
            const opacityValue = document.getElementById('watermarkOpacityValue');
            
            if (opacitySlider && opacityValue) {
                opacitySlider.addEventListener('input', () => {
                    opacityValue.textContent = Math.round(opacitySlider.value * 100) + '%';
                });
            }
        }

        // 添加事件监听器
        if (toolType === 'image_compressor') {
            const qualitySlider = document.getElementById('compressQuality');
            const qualityValue = document.getElementById('compressQualityValue');
            
            if (qualitySlider && qualityValue) {
                qualitySlider.addEventListener('input', () => {
                    qualityValue.textContent = qualitySlider.value + '%';
                });
            }
        } else if (toolType === 'format_converter') {
            const qualitySlider = document.getElementById('convertQuality');
            const qualityValue = document.getElementById('convertQualityValue');
            
            if (qualitySlider && qualityValue) {
                qualitySlider.addEventListener('input', () => {
                    qualityValue.textContent = qualitySlider.value + '%';
                });
            }
        } else if (toolType === 'keyword_analyzer') {
            // 关键词分析工具的选项切换
            const keywordAction = document.getElementById('keywordAction');
            const platformGroup = document.getElementById('platformGroup');
            const competitorAsinGroup = document.getElementById('competitorAsinGroup');
            const productDescriptionGroup = document.getElementById('productDescriptionGroup');
            
            if (keywordAction) {
                keywordAction.addEventListener('change', (e) => {
                    const action = e.target.value;
                    // 显示/隐藏相关选项
                    if (action === 'extract' || action === 'longtail') {
                        if (platformGroup) platformGroup.style.display = 'block';
                        if (competitorAsinGroup) competitorAsinGroup.style.display = 'none';
                    } else if (action === 'competition' || action === 'trend') {
                        if (platformGroup) platformGroup.style.display = 'block';
                        if (competitorAsinGroup) competitorAsinGroup.style.display = 'none';
                    } else if (action === 'compare') {
                        if (platformGroup) platformGroup.style.display = 'none';
                        if (competitorAsinGroup) competitorAsinGroup.style.display = 'block';
                    }
                    
                    // 触发一次change事件，确保初始状态正确
                    if (keywordAction && keywordAction.value) {
                        const event = new Event('change');
                        keywordAction.dispatchEvent(event);
                    }
                });
                
                // 初始化时也需要设置显示状态
                if (keywordAction && keywordAction.value) {
                    const action = keywordAction.value;
                    if (action === 'extract' || action === 'longtail' || action === 'competition' || action === 'trend') {
                        if (platformGroup) platformGroup.style.display = 'block';
                    }
                }
            }
        }
    }

    setupFileUpload(toolType) {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const batchUploadArea = document.getElementById('batchUploadArea');
        const batchFileInput = document.getElementById('batchFileInput');
        
        // 单文件上传设置 - 防止重复绑定事件监听器
        if (uploadArea && fileInput) {
            // 如果已经绑定过事件，先移除旧的监听器
            if (uploadArea.hasAttribute('data-upload-bound')) {
                // 移除旧的监听器（使用克隆元素的方式）
                const newUploadArea = uploadArea.cloneNode(true);
                uploadArea.parentNode.replaceChild(newUploadArea, uploadArea);
                const newFileInput = fileInput.cloneNode(true);
                fileInput.parentNode.replaceChild(newFileInput, fileInput);
                
                // 重新获取元素引用
                const freshUploadArea = document.getElementById('uploadArea');
                const freshFileInput = document.getElementById('fileInput');
                
                if (freshUploadArea && freshFileInput) {
                    this.currentUploadArea = freshUploadArea;
                    this.currentFileInput = freshFileInput;
                    
                    // 重新绑定事件
                    this._bindUploadEvents(freshUploadArea, freshFileInput);
                    freshUploadArea.setAttribute('data-upload-bound', 'true');
                }
                return;
            }
            
            this.currentUploadArea = uploadArea;
            this.currentFileInput = fileInput;
            
            // 绑定事件
            this._bindUploadEvents(uploadArea, fileInput);
            uploadArea.setAttribute('data-upload-bound', 'true');
        }
        
        // 批量上传设置
        if (batchUploadArea && batchFileInput) {
            if (!batchUploadArea.hasAttribute('data-batch-upload-bound')) {
                this._bindBatchUploadEvents(batchUploadArea, batchFileInput);
                batchUploadArea.setAttribute('data-batch-upload-bound', 'true');
            }
        }
    }
    
    _bindUploadEvents(uploadArea, fileInput) {
        // 点击上传区域
        uploadArea.addEventListener('click', (e) => {
            // 如果点击的是内部元素（如文件预览），不触发文件选择
            if (e.target !== uploadArea && !uploadArea.contains(e.target)) {
                return;
            }
            e.stopPropagation();
            fileInput.click();
        });

        // 文件选择
        fileInput.addEventListener('change', (e) => {
            e.stopPropagation();
            const files = e.target.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                // 显示上传加载动画
                this.showUploadLoading(uploadArea);
                // 延迟处理，让用户看到加载动画
                setTimeout(() => {
                    this.handleFileSelect(files[0]);
                }, 300);
            }
        });
    }
    
    _bindBatchUploadEvents(batchUploadArea, batchFileInput) {
        // 点击批量上传区域
        batchUploadArea.addEventListener('click', () => {
            batchFileInput.click();
        });

        // 批量文件选择
        batchFileInput.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files.length > 0) {
                this.handleBatchFileSelect(files);
            }
        });

        // 批量拖拽上传
        batchUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            batchUploadArea.classList.add('dragover');
        });

        batchUploadArea.addEventListener('dragleave', () => {
            batchUploadArea.classList.remove('dragover');
        });

        batchUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            batchUploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleBatchFileSelect(files);
            }
        });
    }

    toggleBatchMode(isBatchMode) {
        const uploadArea = document.getElementById('uploadArea');
        const batchUploadArea = document.getElementById('batchUploadArea');
        const toolOptions = document.getElementById('toolOptions');
        
        if (isBatchMode) {
            // 显示批量上传区域
            if (uploadArea) uploadArea.style.display = 'none';
            if (batchUploadArea) batchUploadArea.style.display = 'block';
            if (toolOptions) toolOptions.style.display = 'none';
        } else {
            // 显示单文件上传区域
            if (uploadArea) uploadArea.style.display = 'block';
            if (batchUploadArea) batchUploadArea.style.display = 'none';
            if (toolOptions) toolOptions.style.display = 'block';
        }
    }

    isBatchMode() {
        const batchModeToggle = document.getElementById('batchMode');
        return batchModeToggle && batchModeToggle.checked;
    }

    handleFileSelect(file) {
        if (!this.validateFile(file)) {
            return;
        }

        const uploadArea = document.getElementById('uploadArea');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        
        if (uploadArea) {
            uploadArea.classList.add('has-file');
        }
        
        if (fileName) {
            fileName.textContent = file.name;
        }
        
        if (fileSize) {
            fileSize.textContent = this.formatFileSize(file.size);
        }

        // 自动开始处理
        console.log('🚀 [handleFileSelect] 开始处理文件，工具类型:', this.currentTool, '文件名:', file.name);
        if (this.currentTool === 'add_watermark' || this.currentTool === 'add_watermark_v2') {
            console.log('🎯 [handleFileSelect] 这是水印工具，准备调用processImage，工具类型:', this.currentTool);
        }
        this.processImage(file);
    }

    handleBatchFileSelect(files) {
        const validFiles = Array.from(files).filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            return;
        }

        this.batchFiles = validFiles;
        this.showBatchPreview();
    }

    showBatchPreview() {
        const batchFileList = document.getElementById('batchFileList');
        const fileItems = document.getElementById('fileItems');
        
        if (!batchFileList || !fileItems) return;

        let fileItemsHTML = '';

        this.batchFiles.forEach((file, index) => {
            fileItemsHTML += `
                <div class="file-item">
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${this.formatFileSize(file.size)}</span>
                    <button class="btn btn-sm btn-danger" onclick="appManager.removeBatchFile(${index})">删除</button>
                </div>
            `;
        });

        fileItems.innerHTML = fileItemsHTML;
        batchFileList.style.display = 'block';
    }

    removeBatchFile(index) {
        this.batchFiles.splice(index, 1);
        
        if (this.batchFiles.length === 0) {
            this.hideBatchPreview();
        } else {
            this.showBatchPreview();
        }
    }

    clearBatchFiles() {
        this.batchFiles = [];
        this.hideBatchPreview();
    }

    hideBatchPreview() {
        const batchFileList = document.getElementById('batchFileList');
        const fileItems = document.getElementById('fileItems');
        
        if (batchFileList) {
            batchFileList.style.display = 'none';
        }
        
        if (fileItems) {
            fileItems.innerHTML = '';
        }
        
        this.batchFiles = [];
    }

    async startBatchProcessing() {
        if (this.batchFiles.length === 0) {
            return;
        }

        this.isBatchProcessing = true;
        this.batchResults = [];
        this.batchProgress = {
            current: 0,
            total: this.batchFiles.length,
            completed: 0,
            errors: 0
        };

        this.showBatchProgress();

        for (let i = 0; i < this.batchFiles.length; i++) {
            const file = this.batchFiles[i];
            this.batchProgress.current = i + 1;
            
            try {
                const result = await this.processImageFile(file);
                this.batchResults.push({ file: file.name, result: result, success: true });
                this.batchProgress.completed++;
            } catch (error) {
                this.batchResults.push({ file: file.name, error: error.message, success: false });
                this.batchProgress.errors++;
            }
            
            this.updateBatchProgress();
        }

        this.isBatchProcessing = false;
        this.showBatchResults();
    }

    showBatchProgress() {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        modalBody.innerHTML = `
            <div class="batch-progress">
                <h3>批量处理进度</h3>
                <div class="progress">
                    <div class="progress-bar" id="batchProgressBar" style="width: 0%"></div>
                </div>
                <div class="progress-text">
                    <span id="batchProgressText">0 / ${this.batchProgress.total}</span>
                    <span>完成: ${this.batchProgress.completed}</span>
                    <span>错误: ${this.batchProgress.errors}</span>
                </div>
            </div>
        `;
    }

    updateBatchProgress() {
        const progressBar = document.getElementById('batchProgressBar');
        const progressText = document.getElementById('batchProgressText');
        
        if (progressBar) {
            const percentage = (this.batchProgress.current / this.batchProgress.total) * 100;
            progressBar.style.width = percentage + '%';
        }
        
        if (progressText) {
            progressText.textContent = `${this.batchProgress.current} / ${this.batchProgress.total}`;
        }
    }

    showBatchResults() {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        let resultsHTML = `
            <div class="batch-results">
                <h3>批量处理完成</h3>
                <div class="results-summary">
                    <span>总计: ${this.batchResults.length}</span>
                    <span>成功: ${this.batchProgress.completed}</span>
                    <span>失败: ${this.batchProgress.errors}</span>
                </div>
                <div class="results-list">
        `;

        this.batchResults.forEach((result, index) => {
            const statusClass = result.success ? 'success' : 'error';
            const statusText = result.success ? '成功' : '失败';
            
            resultsHTML += `
                <div class="result-item ${statusClass}">
                    <span class="file-name">${result.file}</span>
                    <span class="status">${statusText}</span>
                    ${result.success ? `<a href="${result.result}" download class="btn btn-sm btn-primary">下载</a>` : ''}
                    ${!result.success ? `<span class="error-message">${result.error}</span>` : ''}
                </div>
            `;
        });

        resultsHTML += `
                </div>
                <button class="btn btn-primary" onclick="appManager.downloadAllResults()">下载所有结果</button>
                <button class="btn btn-secondary" onclick="appManager.closeModal(document.getElementById('toolModal'))">关闭</button>
            </div>
        `;

        modalBody.innerHTML = resultsHTML;
    }

    downloadAllResults() {
        this.batchResults.forEach((result, index) => {
            if (result.success && result.result) {
                const link = document.createElement('a');
                link.href = result.result;
                link.download = `processed_${index + 1}.jpg`;
                link.click();
            }
        });
    }

    async processImage(file) {
        try {
            console.log('🚀 [processImage] 函数被调用，工具类型:', this.currentTool);
            if (this.currentTool === 'add_watermark' || this.currentTool === 'add_watermark_v2') {
                console.log('🎯 [processImage] 这是水印工具！工具类型:', this.currentTool);
            }
            this.isProcessing = true;
            this.showProcessingStatus(this.currentTool);
            
            // 获取工具选项
            console.log('📋 [processImage] 准备获取工具选项...');
            const toolOptions = this.getToolOptions();
            console.log('📋 [processImage] 获取到的工具选项:', toolOptions);
            
            // 转换文件为base64
            const base64Image = await this.fileToBase64(file);
            
            // 准备请求数据
            const requestData = {
                image: base64Image,
                ...toolOptions
            };

            // 调试：打印水印相关参数（新版）
            if (this.currentTool === 'add_watermark_v2') {
                console.log('🎯🎯🎯 [processImage] 新版水印 - 准备发送的参数:', {
                    watermark_text: requestData.watermark_text,
                    watermark_position: requestData.watermark_position,
                    opacity: requestData.opacity,
                    font_size: requestData.font_size,
                    font_color: requestData.font_color,
                    toolOptions: toolOptions,
                    requestData: requestData
                });
            }

            // 根据工具类型设置不同的URL
            let apiUrl;
            switch(this.currentTool) {
                case 'background_remover':
                    apiUrl = `${this.apiBaseUrl}/api/tools/remove-background`;
                    break;
                case 'image_compressor':
                    apiUrl = `${this.apiBaseUrl}/api/tools/compress-image`;
                    break;
                case 'format_converter':
                    apiUrl = `${this.apiBaseUrl}/api/tools/convert-format`;
                    this.updateProgress(20, '准备格式转换参数...');
                    break;
                case 'image_cropper':
                    apiUrl = `${this.apiBaseUrl}/api/tools/crop-image`;
                    this.updateProgress(20, '准备裁剪参数...');
                    break;
                case 'image_rotate_flip':
                    apiUrl = `${this.apiBaseUrl}/api/tools/rotate-flip`;
                    this.updateProgress(20, '准备旋转/翻转参数...');
                    break;
                // 旧版水印功能（已注释）
                // case 'add_watermark':
                //     apiUrl = `${this.apiBaseUrl}/api/tools/add-watermark`;
                //     break;
                
                // 新版水印功能
                case 'add_watermark_v2':
                    console.log('🎯🎯🎯 新版水印功能 - 设置API URL');
                    apiUrl = `${this.apiBaseUrl}/api/tools/add-watermark-v2`;
                    this.updateProgress(20, '准备水印参数（新版）...');
                    break;
                case 'remove_watermark':
                    apiUrl = `${this.apiBaseUrl}/api/tools/remove-watermark`;
                    this.updateProgress(20, '准备去水印参数...');
                    break;
                default:
                    apiUrl = `${this.apiBaseUrl}/api/tools/background-remover`;
            }

            this.updateProgress(30, '发送处理请求...');
            
            // 调用API - 发送JSON数据
            const headers = {
                'Content-Type': 'application/json'
            };
            
            // 如果有token则添加认证头
            const token = this.authManager.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
                console.log('发送认证头，token:', token.substring(0, 20) + '...');
            } else {
                console.warn('没有token，无法调用API');
                throw new Error('请先登录');
            }
            
            console.log('发送API请求:', apiUrl, { headers, hasBody: !!requestData.image });
            
            // 调试：打印实际发送的数据（新版水印功能）
            if (this.currentTool === 'add_watermark_v2') {
                console.log('🎯🎯🎯 [processImage] 新版水印 - 实际发送的请求体:', JSON.stringify({
                    hasImage: !!requestData.image,
                    watermark_text: requestData.watermark_text,
                    watermark_position: requestData.watermark_position,
                    opacity: requestData.opacity,
                    font_size: requestData.font_size,
                    font_color: requestData.font_color
                }, null, 2));
                console.log('🎯🎯🎯 [processImage] 新版水印 - 准备发送POST请求到:', apiUrl);
            }
            
            let response;
            try {
                response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(requestData)
                });
                
                console.log('API响应状态:', response.status, response.statusText);
                
                if (this.currentTool === 'add_watermark_v2') {
                    console.log('🎯🎯🎯 [processImage] 新版水印 - 收到响应，状态码:', response.status);
                }
            } catch (error) {
                console.error('❌❌❌ [processImage] 请求发送失败:', error);
                if (this.currentTool === 'add_watermark_v2') {
                    console.error('❌❌❌ [processImage] 新版水印 - 请求失败:', error.message);
                }
                throw error;
            }

            this.updateProgress(80, '等待服务器响应...');
            
            // 检查响应状态（移动端优化）
            if (response.status === 401) {
                console.error('❌ 认证失败(401)，可能需要重新登录');
                try {
                    const errorData = await safeParseJsonResponse(response, apiUrl).catch(() => ({}));
                    console.error('401错误详情:', errorData);
                } catch (e) {
                    console.error('无法解析401响应:', e);
                }
                // 移动端优化：延迟清除，避免频繁操作
                setTimeout(() => {
                    this.authManager.logout();
                    this.closeModal('toolModal');
                    // 移动端优化：使用更友好的提示
                    const isMobile = window.innerWidth <= 768;
                    if (isMobile) {
                        // 移动端：使用确认对话框
                        if (confirm('登录已过期，是否重新登录？')) {
                            this.showLoginModal();
                        }
                    } else {
                        // 桌面端：使用alert
                        alert('登录已过期，请重新登录');
                        this.showLoginModal();
                    }
                }, 500);
                this.isProcessing = false;
                return;
            }
            
            if (response.status === 403) {
                console.error('❌ 权限不足(403)');
                // 移动端优化：显示友好提示
                const errorMsg = '权限不足，请检查您的会员等级或联系客服';
                const isMobile = window.innerWidth <= 768;
                if (isMobile) {
                    alert(errorMsg);
                } else {
                    this.showNotification(errorMsg, 'error');
                }
                this.isProcessing = false;
                return;
            }
            
            // 使用安全的JSON解析函数，避免解析HTML错误页面
            const result = await safeParseJsonResponse(response, apiUrl);
            
            console.log('API响应:', { status: response.status, success: result.success, hasError: !!result.error });
            
            // 调试：新版水印功能的响应
            if (this.currentTool === 'add_watermark_v2') {
                console.log('🎯🎯🎯 [processImage] 新版水印 - 收到完整响应:', result);
                console.log('🎯 processed_image存在:', !!result.processed_image);
                if (result.processed_image) {
                    console.log('🎯 processed_image长度:', result.processed_image.length, '前50字符:', result.processed_image.substring(0, 50));
                }
            }

            if (response.ok && result.success !== false) {
                this.updateProgress(100, '处理完成！');
                
                // 调试：新版水印功能
                if (this.currentTool === 'add_watermark_v2') {
                    console.log('🎯🎯🎯 [processImage] 新版水印 - 准备显示结果');
                    console.log('🎯 结果数据:', result);
                }
                
                // 延迟显示成功结果，让用户看到100%进度
                setTimeout(() => {
                    if (this.currentTool === 'add_watermark_v2') {
                        console.log('🎯🎯🎯 [processImage] 新版水印 - 调用showSuccessResult');
                    }
                    this.showSuccessResult(result, this.currentTool);
                    // 更新使用统计
                    this.loadUsageStats();
                    // 重置处理状态
                    this.isProcessing = false;
                    // 恢复按钮
                    this.disableButtons(false);
                }, 500);
            } else {
                const errorMsg = result.error || result.message || '处理失败';
                console.error('API调用失败:', errorMsg);
                
                // 检查是否是使用次数达到上限
                if (response.status === 400 && (errorMsg.includes('今日使用次数已达上限') || errorMsg.includes('使用次数已达上限'))) {
                    this.isProcessing = false;
                    this.closeModal('toolModal');
                    
                    // 显示提示并跳转到支付页面
                    const userConfirmed = confirm(
                        `今日使用次数已达上限！\n\n` +
                        `免费版用户每日使用次数有限，升级会员可享受更多使用次数。\n\n` +
                        `是否前往升级会员？`
                    );
                    
                    if (userConfirmed) {
                        window.location.href = 'payment.html';
                    }
                    return;
                }
                
                throw new Error(errorMsg);
            }
        } catch (error) {
            this.isProcessing = false;
            this.disableButtons(false);
            this.showError(error.message);
        }
    }
    
    disableButtons(disable) {
        // 禁用/启用模态框内的所有按钮
        const modal = document.getElementById('toolModal');
        if (modal) {
            const buttons = modal.querySelectorAll('button, .btn, a.btn');
            buttons.forEach(btn => {
                if (disable) {
                    btn.classList.add('processing');
                    btn.disabled = true;
                } else {
                    btn.classList.remove('processing');
                    btn.disabled = false;
                }
            });
        }
    }

    async processImageFile(file) {
        // 获取工具选项
        const toolOptions = this.getToolOptions();
        
        // 转换文件为base64
        const base64Image = await this.fileToBase64(file);
        
        // 准备请求数据
        const requestData = {
            image: base64Image,
            ...toolOptions
        };
        
        // 调试：打印水印相关参数
        if (this.currentTool === 'add_watermark') {
            console.log('🔍 准备发送的水印参数:', {
                watermark_text: requestData.watermark_text,
                watermark_position: requestData.watermark_position,
                opacity: requestData.opacity,
                font_size: requestData.font_size,
                font_color: requestData.font_color
            });
        }

        // 根据工具类型设置不同的URL
        let apiUrl;
        switch(this.currentTool) {
            case 'background_remover':
                apiUrl = `${this.apiBaseUrl}/api/tools/remove-background`;
                break;
            case 'image_compressor':
                apiUrl = `${this.apiBaseUrl}/api/tools/compress-image`;
                break;
            case 'format_converter':
                apiUrl = `${this.apiBaseUrl}/api/tools/convert-format`;
                break;
            case 'image_cropper':
                apiUrl = `${this.apiBaseUrl}/api/tools/crop-image`;
                break;
            case 'image_rotate_flip':
                apiUrl = `${this.apiBaseUrl}/api/tools/rotate-flip`;
                break;
            case 'keyword_analyzer':
                apiUrl = `${this.apiBaseUrl}/api/tools/keyword-analyzer`;
                break;
            // 旧版水印功能（已注释）
            // case 'add_watermark':
            //     apiUrl = `${this.apiBaseUrl}/api/tools/add-watermark`;
            //     break;
            
            // 新版水印功能
            case 'add_watermark_v2':
                console.log('🎯🎯🎯 新版水印功能 - processImageFile - 设置API URL');
                apiUrl = `${this.apiBaseUrl}/api/tools/add-watermark-v2`;
                break;
            case 'remove_watermark':
                apiUrl = `${this.apiBaseUrl}/api/tools/remove-watermark`;
                break;
            case 'image_rotate_flip':
                apiUrl = `${this.apiBaseUrl}/api/tools/rotate-flip`;
                break;
            default:
                apiUrl = `${this.apiBaseUrl}/api/tools/background-remover`;
        }
        
        // 调用API
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const token = this.authManager.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestData)
        });

        const result = await safeParseJsonResponse(response, apiUrl);

        if (response.ok) {
            // 新版水印功能也返回 processed_image
            return result.processed_image || result.converted_image || result.cropped_image;
        } else {
            const errorMsg = result.error || '处理失败';
            
            // 检查是否是使用次数达到上限
            if (response.status === 400 && (errorMsg.includes('今日使用次数已达上限') || errorMsg.includes('使用次数已达上限'))) {
                this.closeModal('toolModal');
                
                const userConfirmed = confirm(
                    `今日使用次数已达上限！\n\n` +
                    `免费版用户每日使用次数有限，升级会员可享受更多使用次数。\n\n` +
                    `是否前往升级会员？`
                );
                
                if (userConfirmed) {
                    window.location.href = 'payment.html';
                }
                throw new Error(errorMsg);
            }
            
            throw new Error(errorMsg);
        }
    }

    getToolOptions() {
        const options = {};
        
        switch(this.currentTool) {
            case 'image_compressor':
                const compressQuality = document.getElementById('compressQuality');
                const compressFormat = document.getElementById('compressFormat');
                const maxSize = document.getElementById('maxSize');
                
                if (compressQuality) options.quality = parseInt(compressQuality.value);
                if (compressFormat) options.format = compressFormat.value;
                if (maxSize && maxSize.value) options.max_size = parseInt(maxSize.value);
                break;
                
            case 'format_converter':
                const outputFormat = document.getElementById('outputFormat');
                const convertQuality = document.getElementById('convertQuality');
                
                if (outputFormat) options.format = outputFormat.value;
                if (convertQuality) options.quality = parseInt(convertQuality.value);
                break;
                
            case 'image_cropper':
                const cropPreset = document.getElementById('cropPreset');
                if (cropPreset) options.preset = cropPreset.value;
                break;
            case 'image_rotate_flip':
                const rotateFlipOperation = document.querySelector('input[name="rotateFlipOperation"]:checked');
                if (rotateFlipOperation) {
                    options.operation = rotateFlipOperation.value;
                } else {
                    options.operation = 'rotate_90_cw'; // 默认值
                }
                break;
            case 'keyword_analyzer':
                const keywordAction = document.getElementById('keywordAction');
                const productDescription = document.getElementById('productDescription');
                const targetPlatform = document.getElementById('targetPlatform');
                const competitorAsin = document.getElementById('competitorAsin');
                
                if (keywordAction) options.action = keywordAction.value;
                if (productDescription) options.product_description = productDescription.value;
                
                // 确保正确获取平台选择
                if (targetPlatform) {
                    const selectedPlatform = targetPlatform.value;
                    console.log('🔍 getToolOptions - 平台选择元素值:', selectedPlatform);
                    options.platform = selectedPlatform || 'amazon';
                } else {
                    console.warn('⚠️ 未找到平台选择元素');
                    options.platform = 'amazon'; // 默认值
                }
                
                if (competitorAsin) options.competitor_asin = competitorAsin.value;
                
                console.log('🔍 getToolOptions - 最终平台值:', options.platform);
                break;
            case 'listing_generator':
                const listingProductInfo = document.getElementById('listingProductInfo');
                const listingPlatform = document.getElementById('listingPlatform');
                const listingLanguage = document.getElementById('listingLanguage');
                const listingStyle = document.getElementById('listingStyle');
                
                if (listingProductInfo) options.product_info = listingProductInfo.value;
                if (listingPlatform) options.platform = listingPlatform.value;
                if (listingLanguage) options.language = listingLanguage.value;
                if (listingStyle) options.style = listingStyle.value;
                break;
            case 'currency_converter':
                const currencyAmount = document.getElementById('currencyAmount');
                const fromCurrency = document.getElementById('fromCurrency');
                const toCurrency = document.getElementById('toCurrency');
                
                if (currencyAmount) options.amount = parseFloat(currencyAmount.value) || 0;
                if (fromCurrency) options.from_currency = fromCurrency.value;
                if (toCurrency) options.to_currency = toCurrency.value;
                break;
            // 旧版水印功能（已注释）
            // case 'add_watermark':
            //     ...
            //     break;
            
            // 新版水印功能（简化版）
            case 'add_watermark_v2':
                console.log('🎯🎯🎯 [getToolOptions] 新版水印 - 开始获取参数！');
                const watermarkTextV2 = document.getElementById('watermarkTextV2');
                const watermarkPositionV2 = document.getElementById('watermarkPositionV2');
                const watermarkOpacityV2 = document.getElementById('watermarkOpacityV2');
                const watermarkFontSizeV2 = document.getElementById('watermarkFontSizeV2');
                const watermarkColorV2 = document.getElementById('watermarkColorV2');
                
                console.log('🎯 [getToolOptions] 新版 - 找到的元素:', {
                    watermarkTextV2: !!watermarkTextV2,
                    watermarkPositionV2: !!watermarkPositionV2,
                    watermarkOpacityV2: !!watermarkOpacityV2,
                    watermarkFontSizeV2: !!watermarkFontSizeV2,
                    watermarkColorV2: !!watermarkColorV2
                });
                
                if (watermarkTextV2) {
                    options.watermark_text = watermarkTextV2.value;
                    console.log('✅ 水印文字:', watermarkTextV2.value);
                }
                if (watermarkPositionV2) {
                    options.watermark_position = watermarkPositionV2.value;
                    console.log('✅✅✅ 新版水印位置:', watermarkPositionV2.value, '类型:', typeof watermarkPositionV2.value);
                } else {
                    console.error('❌❌❌ 找不到新版水印位置选择框！');
                }
                if (watermarkOpacityV2) {
                    options.opacity = parseFloat(watermarkOpacityV2.value);
                    console.log('✅ 透明度:', options.opacity);
                }
                if (watermarkFontSizeV2) {
                    options.font_size = parseInt(watermarkFontSizeV2.value);
                    console.log('✅ 字体大小:', options.font_size);
                }
                if (watermarkColorV2) {
                    options.font_color = watermarkColorV2.value;
                    console.log('✅ 字体颜色:', options.font_color);
                }
                
                console.log('🎯🎯🎯 [getToolOptions] 新版 - 最终选项:', options);
                break;
            case 'remove_watermark':
                // 去水印不需要额外选项
                break;
        }
        
        return options;
    }

    async processKeywordAnalysis() {
        // 关键词分析专用处理函数（不需要文件上传）
        if (!this.currentTool || this.currentTool !== 'keyword_analyzer') {
            return;
        }

        const keywordAction = document.getElementById('keywordAction');
        const productDescription = document.getElementById('productDescription');
        
        if (!keywordAction || !productDescription) {
            alert('请先选择功能和输入产品描述');
            return;
        }

        const action = keywordAction.value;
        const description = productDescription.value.trim();

        if (!description) {
            alert('请输入产品描述');
            return;
        }

        try {
            this.isProcessing = true;
            this.showProcessingStatus(this.currentTool);

            // 直接获取平台选择元素的值，确保获取最新的选择
            const targetPlatform = document.getElementById('targetPlatform');
            let selectedPlatform = 'amazon'; // 默认值
            
            if (targetPlatform && targetPlatform.value) {
                selectedPlatform = targetPlatform.value;
                console.log('📊 直接读取平台选择元素值:', selectedPlatform);
            } else {
                // 如果直接读取失败，尝试从getToolOptions获取
                const options = this.getToolOptions();
                selectedPlatform = options.platform || 'amazon';
                console.log('📊 从getToolOptions获取平台值:', selectedPlatform);
            }
            
            const options = this.getToolOptions();
            console.log('📊 发送请求 - 选择的平台:', selectedPlatform);
            
            // 确保平台参数使用直接读取的值，覆盖options中的值
            const requestData = {
                action: action,
                product_description: description,
                keyword: description, // 也发送keyword字段，方便后端统一处理
                platform: selectedPlatform, // 使用直接读取的平台值
                competitor_asins: options.competitor_asins || options.competitor_asin || '',
                competitor_asin: options.competitor_asin || options.competitor_asins || '',
                days: options.days || 30,
                depth: options.depth || 3
            };
            
            // 合并options，但platform使用直接读取的值
            Object.assign(requestData, options);
            requestData.platform = selectedPlatform; // 确保平台值正确
            
            console.log('📊 发送请求 - 完整数据:', requestData);
            console.log('📊 发送请求 - 平台参数确认:', requestData.platform);

            const apiUrl = `${this.apiBaseUrl}/api/tools/keyword-analyzer`;
            
            this.updateProgress(30, '发送分析请求...');

            const headers = {
                'Content-Type': 'application/json'
            };

            const token = this.authManager.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            } else {
                throw new Error('请先登录');
            }

            this.updateProgress(50, '正在分析关键词...');
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestData)
            });

            this.updateProgress(80, '处理分析结果...');

            if (response.status === 401) {
                this.authManager.logout();
                alert('登录已过期，请重新登录');
                this.closeModal('toolModal');
                this.showLoginModal();
                this.isProcessing = false;
                return;
            }

            const result = await safeParseJsonResponse(response, apiUrl);

            if (response.ok && result.success !== false) {
                this.updateProgress(100, '分析完成！');
                setTimeout(() => {
                    this.showKeywordAnalysisResult(result, action);
                    this.loadUsageStats();
                    this.isProcessing = false;
                }, 500);
            } else {
                const errorMsg = result.error || '关键词分析失败';
                
                // 检查是否是使用次数达到上限
                if (response.status === 400 && (errorMsg.includes('今日使用次数已达上限') || errorMsg.includes('使用次数已达上限'))) {
                    this.isProcessing = false;
                    this.closeModal('toolModal');
                    
                    const userConfirmed = confirm(
                        `今日使用次数已达上限！\n\n` +
                        `免费版用户每日使用次数有限，升级会员可享受更多使用次数。\n\n` +
                        `是否前往升级会员？`
                    );
                    
                    if (userConfirmed) {
                        window.location.href = 'payment.html';
                    }
                    return;
                }
                
                this.showError(errorMsg);
                this.isProcessing = false;
            }
        } catch (error) {
            console.error('关键词分析错误:', error);
            this.showError(`关键词分析失败: ${error.message}`);
            this.isProcessing = false;
        }
    }

    // 平台名称映射
    getPlatformName(platformCode) {
        const platformMap = {
            'amazon': '亚马逊 (Amazon)',
            'ebay': 'eBay',
            'temu': 'Temu',
            'shopee': '虾皮 (Shopee)',
            'all': '所有平台',
            'Amazon': '亚马逊 (Amazon)',
            'eBay': 'eBay',
            'Temu': 'Temu',
            'Shopee': '虾皮 (Shopee)',
            'All': '所有平台'
        };
        return platformMap[platformCode] || platformCode || '未知平台';
    }

    async processListingGeneration() {
        // Listing文案生成专用处理函数（不需要文件上传）
        if (!this.currentTool || this.currentTool !== 'listing_generator') {
            return;
        }

        const productInfo = document.getElementById('listingProductInfo');
        const platform = document.getElementById('listingPlatform');
        const language = document.getElementById('listingLanguage');
        const style = document.getElementById('listingStyle');
        
        if (!productInfo || !platform || !language || !style) {
            alert('请先填写完整信息');
            return;
        }

        const productInfoText = productInfo.value.trim();
        const selectedPlatform = platform.value;
        const selectedLanguage = language.value;
        const selectedStyle = style.value;

        if (!productInfoText) {
            alert('请输入产品信息');
            return;
        }

        try {
            this.isProcessing = true;
            this.showProcessingStatus(this.currentTool);

            const requestData = {
                product_info: productInfoText,
                platform: selectedPlatform,
                language: selectedLanguage,
                style: selectedStyle
            };

            const apiUrl = `${this.apiBaseUrl}/api/tools/generate-listing`;
            
            this.updateProgress(20, '准备生成文案...');

            const headers = {
                'Content-Type': 'application/json'
            };

            const token = this.authManager.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            } else {
                throw new Error('请先登录');
            }

            this.updateProgress(40, 'AI正在生成文案...');
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestData)
            });

            this.updateProgress(80, '处理结果...');

            if (response.status === 401) {
                this.authManager.logout();
                alert('登录已过期，请重新登录');
                this.closeModal('toolModal');
                this.showLoginModal();
                this.isProcessing = false;
                return;
            }

            const result = await safeParseJsonResponse(response, apiUrl);

            if (response.ok && result.success !== false) {
                this.updateProgress(100, '生成完成！');
                setTimeout(() => {
                    this.showListingGenerationResult(result);
                    this.loadUsageStats();
                    this.isProcessing = false;
                }, 500);
            } else {
                const errorMsg = result.error || '生成失败';
                
                // 检查是否是使用次数达到上限
                if (response.status === 400 && (errorMsg.includes('今日使用次数已达上限') || errorMsg.includes('使用次数已达上限'))) {
                    this.isProcessing = false;
                    this.closeModal('toolModal');
                    
                    const userConfirmed = confirm(
                        `今日使用次数已达上限！\n\n` +
                        `免费版用户每日使用次数有限，升级会员可享受更多使用次数。\n\n` +
                        `是否前往升级会员？`
                    );
                    
                    if (userConfirmed) {
                        window.location.href = 'payment.html';
                    }
                    return;
                }
                
                this.showError(errorMsg);
                this.isProcessing = false;
            }
        } catch (error) {
            console.error('Listing文案生成失败:', error);
            this.isProcessing = false;
            this.showError(`生成失败: ${error.message}`);
            this.hideProcessingStatus();
        }
    }

    async processCurrencyConversion() {
        // 汇率换算专用处理函数（不需要文件上传）
        if (!this.currentTool || this.currentTool !== 'currency_converter') {
            return;
        }

        const currencyAmount = document.getElementById('currencyAmount');
        const fromCurrency = document.getElementById('fromCurrency');
        const toCurrency = document.getElementById('toCurrency');
        
        if (!currencyAmount || !fromCurrency || !toCurrency) {
            alert('请先填写完整信息');
            return;
        }

        const amount = parseFloat(currencyAmount.value);
        const from = fromCurrency.value;
        const to = toCurrency.value;

        if (!amount || amount <= 0) {
            alert('请输入有效的金额（大于0）');
            return;
        }

        if (from === to) {
            alert('源货币和目标货币不能相同');
            return;
        }

        try {
            this.isProcessing = true;
            this.showProcessingStatus(this.currentTool);

            const options = this.getToolOptions();
            const requestData = {
                amount: amount,
                from_currency: from,
                to_currency: to,
                ...options
            };

            const apiUrl = `${this.apiBaseUrl}/api/tools/currency-converter`;
            
            this.updateProgress(30, '获取实时汇率...');

            const headers = {
                'Content-Type': 'application/json'
            };

            const token = this.authManager.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            } else {
                throw new Error('请先登录');
            }

            this.updateProgress(60, '正在换算...');
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestData)
            });

            this.updateProgress(80, '处理结果...');

            if (response.status === 401) {
                this.authManager.logout();
                alert('登录已过期，请重新登录');
                this.closeModal('toolModal');
                this.showLoginModal();
                this.isProcessing = false;
                return;
            }

            const result = await safeParseJsonResponse(response, apiUrl);

            if (response.ok && result.success !== false) {
                this.updateProgress(100, '换算完成！');
                setTimeout(() => {
                    this.showCurrencyConversionResult(result);
                    this.loadUsageStats();
                    this.isProcessing = false;
                }, 500);
            } else {
                const errorMsg = result.error || '汇率换算失败';
                
                // 检查是否是使用次数达到上限
                if (response.status === 400 && (errorMsg.includes('今日使用次数已达上限') || errorMsg.includes('使用次数已达上限'))) {
                    this.isProcessing = false;
                    this.closeModal('toolModal');
                    
                    const userConfirmed = confirm(
                        `今日使用次数已达上限！\n\n` +
                        `免费版用户每日使用次数有限，升级会员可享受更多使用次数。\n\n` +
                        `是否前往升级会员？`
                    );
                    
                    if (userConfirmed) {
                        window.location.href = 'payment.html';
                    }
                    return;
                }
                
                this.showError(errorMsg);
                this.isProcessing = false;
            }
        } catch (error) {
            console.error('汇率换算错误:', error);
            this.showError(`汇率换算失败: ${error.message}`);
            this.isProcessing = false;
        }
    }

    showListingGenerationResult(result) {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        if (!modalBody) return;

        const title = result.title || '未生成标题';
        const description = result.description || '未生成描述';
        const keyFeatures = result.key_features || [];
        const keywords = result.keywords || [];
        const platform = this.getPlatformName(result.platform || 'amazon');
        const language = result.language === 'zh' ? '中文' : '英文';
        const style = result.style === 'professional' ? '专业风格' : 
                     result.style === 'casual' ? '轻松风格' : '营销风格';

        const featuresHTML = keyFeatures.length > 0 
            ? `<div style="margin-top: 15px;">
                <strong>主要特点：</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    ${keyFeatures.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
               </div>`
            : '';

        const keywordsHTML = keywords.length > 0
            ? `<div style="margin-top: 15px;">
                <strong>关键词：</strong>
                <div style="margin-top: 10px;">
                    ${keywords.map(keyword => `<span style="display: inline-block; margin: 5px; padding: 5px 10px; background: #e9ecef; border-radius: 4px; font-size: 0.9rem;">${keyword}</span>`).join('')}
                </div>
               </div>`
            : '';

        const resultHTML = `
            <div class="result-container">
                <h3>Listing文案生成完成！</h3>
                <div class="result-info" style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <div style="margin-bottom: 15px; color: #666; font-size: 0.9rem;">
                        <span>平台：${platform}</span> | 
                        <span>语言：${language}</span> | 
                        <span>风格：${style}</span>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <strong style="display: block; margin-bottom: 10px; color: #333;">产品标题：</strong>
                        <div style="padding: 15px; background: white; border-left: 4px solid #007bff; border-radius: 4px; font-size: 1.1rem; line-height: 1.6;">
                            ${title}
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <strong style="display: block; margin-bottom: 10px; color: #333;">产品描述：</strong>
                        <div style="padding: 15px; background: white; border-left: 4px solid #28a745; border-radius: 4px; line-height: 1.8; white-space: pre-wrap;">
                            ${description}
                        </div>
                    </div>
                    
                    ${featuresHTML}
                    ${keywordsHTML}
                    
                    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                        <button onclick="this.nextElementSibling.select(); document.execCommand('copy'); alert('已复制到剪贴板！');" 
                                class="btn btn-outline" style="margin-right: 10px;">
                            <i class="fas fa-copy"></i> 复制标题
                        </button>
                        <textarea readonly style="position: absolute; left: -9999px;">${title}</textarea>
                        
                        <button onclick="this.nextElementSibling.select(); document.execCommand('copy'); alert('已复制到剪贴板！');" 
                                class="btn btn-outline">
                            <i class="fas fa-copy"></i> 复制描述
                        </button>
                        <textarea readonly style="position: absolute; left: -9999px;">${description}</textarea>
                    </div>
                </div>
                
                ${result.current_usage !== undefined ? `
                <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 4px; font-size: 0.9rem; color: #0066cc;">
                    <i class="fas fa-info-circle"></i> 
                    今日已使用 ${result.current_usage} / ${result.daily_limit === -1 ? '∞' : result.daily_limit} 次
                    ${result.remaining_usage !== undefined && result.remaining_usage >= 0 ? `（剩余 ${result.remaining_usage} 次）` : ''}
                </div>
                ` : ''}
            </div>
        `;

        modalBody.innerHTML = resultHTML;
    }

    showCurrencyConversionResult(result) {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        if (!modalBody) return;

        const resultHTML = `
            <div class="result-container">
                <h3>汇率换算完成！</h3>
                <div class="result-info" style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 2rem; font-weight: bold; color: #007bff; margin-bottom: 10px;">
                            ${result.amount} ${result.from_currency}
                        </div>
                        <div style="font-size: 1.5rem; color: #666; margin: 10px 0;">=</div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #28a745; margin-top: 10px;">
                            ${result.converted_amount} ${result.to_currency}
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p style="margin: 5px 0;"><strong>汇率:</strong> 1 ${result.from_currency} = ${result.exchange_rate} ${result.to_currency}</p>
                        <p style="margin: 5px 0;"><strong>今日使用:</strong> ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                        <p style="margin: 5px 0;"><strong>剩余次数:</strong> ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                    </div>
                </div>
                <div class="result-actions" style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                    <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新换算</button>
                </div>
            </div>
        `;

        modalBody.innerHTML = resultHTML;
        this.showModal(modal);
    }

    showKeywordAnalysisResult(result, action) {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        if (!modalBody) return;

        // 调试：输出接收到的数据
        console.log('📊 关键词分析结果:', action, result);
        console.log('📊 平台信息:', result.platform, '映射为:', this.getPlatformName(result.platform));

        let resultHTML = '';
        const keywords = result.keywords || [];
        // 后端返回的competition_data是数组，不是对象
        const competitionData = result.competition_data || result.keywords || [];
        const trendData = result.trend_data || [];
        const comparisonData = result.comparison_data || result.competitors || {};
        const longtailKeywords = result.longtail_keywords || [];

        // 调试：输出解析后的数据
        console.log('🔍 解析后的数据:', {
            action,
            keywords: keywords.length,
            competitionData: Array.isArray(competitionData) ? competitionData.length : 'not array',
            trendData: Array.isArray(trendData) ? trendData.length : 'not array',
            longtailKeywords: longtailKeywords.length
        });

        switch(action) {
            case 'extract':
                resultHTML = this.generateKeywordExtractHTML(keywords, result);
                break;
            case 'competition':
                resultHTML = this.generateCompetitionHTML(competitionData, result);
                break;
            case 'trend':
                resultHTML = this.generateTrendHTML(trendData, result);
                break;
            case 'compare':
                resultHTML = this.generateCompareHTML(comparisonData, result);
                break;
            case 'longtail':
                resultHTML = this.generateLongtailHTML(longtailKeywords, result);
                break;
            default:
                resultHTML = this.generateKeywordExtractHTML(keywords, result);
        }

        modalBody.innerHTML = resultHTML;
        this.showModal(modal);
    }

    generateKeywordExtractHTML(keywords, result) {
        const keywordsList = keywords.length > 0 
            ? keywords.map((kw, idx) => `
                <div class="keyword-item" style="padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #007bff;">
                    <strong>${idx + 1}. ${kw.keyword || kw}</strong>
                    ${kw.platform ? `<span class="badge" style="background: #28a745; color: white; padding: 2px 8px; border-radius: 3px; margin-left: 10px; font-size: 12px;">${kw.platform}</span>` : ''}
                    ${kw.score ? `<span style="float: right; color: #666;">相关性: ${kw.score}/10</span>` : ''}
                </div>
            `).join('')
            : '<p style="color: #999; text-align: center; padding: 20px;">未找到关键词</p>';

        return `
            <div class="result-container">
                <h3>关键词提取完成！</h3>
                <div class="result-info" style="margin: 20px 0;">
                    <p><strong>产品描述:</strong> ${result.product_description || '未提供'}</p>
                    <p><strong>平台:</strong> ${this.getPlatformName(result.platform || 'all')}</p>
                    <p><strong>关键词数量:</strong> ${keywords.length}</p>
                    <p><strong>今日使用:</strong> ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                    <p><strong>剩余次数:</strong> ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                </div>
                <div class="keywords-list" style="max-height: 400px; overflow-y: auto; margin: 20px 0;">
                    ${keywordsList}
                </div>
                <div class="result-actions" style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="appManager.exportKeywords('excel')">导出Excel</button>
                    <button class="btn btn-primary" onclick="appManager.exportKeywords('csv')">导出CSV</button>
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                    <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新分析</button>
                </div>
            </div>
        `;
    }

    generateCompetitionHTML(competitionData, result) {
        console.log('🔍 竞争度HTML生成 - 输入数据:', competitionData);
        console.log('🔍 竞争度HTML生成 - result:', result);
        
        // 后端返回的competition_data是数组，直接使用
        // 如果不是数组，尝试从keywords属性获取
        let dataArray = [];
        if (Array.isArray(competitionData)) {
            dataArray = competitionData;
        } else if (competitionData && competitionData.keywords) {
            dataArray = competitionData.keywords;
        } else if (result.competition_data && Array.isArray(result.competition_data)) {
            dataArray = result.competition_data;
        } else if (result.keywords && Array.isArray(result.keywords)) {
            dataArray = result.keywords;
        }
        
        console.log('🔍 竞争度HTML生成 - 最终数据数组:', dataArray, '长度:', dataArray.length);
        
        const competitionList = dataArray.length > 0 ? 
            dataArray.map((item, idx) => {
                // 后端返回的字段是competition，不是competition_level
                const competition = item.competition || item.competition_level || 'unknown';
                const competitionLower = competition.toLowerCase();
                const bgColor = competitionLower === 'high' ? '#dc3545' : 
                                competitionLower === 'medium' ? '#ffc107' : '#28a745';
                const cpcValue = item.cpc ? (typeof item.cpc === 'number' ? '$' + item.cpc.toFixed(2) : item.cpc) : '$0.00';
                return `
                <tr>
                    <td>${idx + 1}</td>
                    <td><strong>${item.keyword || ''}</strong></td>
                    <td>${item.search_volume || 0}</td>
                    <td><span class="badge" style="background: ${bgColor}; color: white; padding: 4px 8px; border-radius: 3px;">${competition}</span></td>
                    <td>${cpcValue}</td>
                    <td>${item.trend || 'N/A'}</td>
                </tr>
            `;
            }).join('')
            : '<tr><td colspan="6" style="text-align: center; color: #999;">暂无数据</td></tr>';

        return `
            <div class="result-container">
                <h3>竞争度分析完成！</h3>
                <div class="result-info" style="margin: 20px 0;">
                    <p><strong>平台:</strong> ${this.getPlatformName(result.platform || 'amazon')}</p>
                    <p><strong>今日使用:</strong> ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                </div>
                <div class="competition-table" style="overflow-x: auto; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 10px; border: 1px solid #ddd;">#</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">关键词</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">搜索量</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">竞争度</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">CPC</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">趋势</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${competitionList}
                        </tbody>
                    </table>
                </div>
                <div class="result-actions" style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="appManager.exportKeywords('excel')">导出Excel</button>
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                </div>
            </div>
        `;
    }

    generateTrendHTML(trendData, result) {
        console.log('🔍 趋势HTML生成 - 输入数据:', trendData);
        console.log('🔍 趋势HTML生成 - result:', result);
        
        // 后端返回的trend_data是数组
        let trendArray = [];
        if (Array.isArray(trendData)) {
            trendArray = trendData;
        } else if (trendData && trendData.trend_data) {
            trendArray = trendData.trend_data;
        } else if (result.trend_data && Array.isArray(result.trend_data)) {
            trendArray = result.trend_data;
        }
        
        console.log('🔍 趋势HTML生成 - 最终数据数组:', trendArray, '长度:', trendArray.length);
        
        let trendList = '';
        if (trendArray.length > 0) {
            trendList = trendArray.slice(0, 10).map((item, idx) => `
                <tr>
                    <td>${idx + 1}</td>
                    <td>${item.date || 'N/A'}</td>
                    <td>${item.search_volume || 0}</td>
                    <td>${item.competition ? (item.competition * 100).toFixed(0) + '%' : 'N/A'}</td>
                    <td>$${item.cpc ? (typeof item.cpc === 'number' ? item.cpc.toFixed(2) : item.cpc) : '0.00'}</td>
                </tr>
            `).join('');
        } else {
            trendList = '<tr><td colspan="5" style="text-align: center; color: #999;">暂无数据</td></tr>';
        }
        
        return `
            <div class="result-container">
                <h3>趋势分析完成！</h3>
                <div class="result-info" style="margin: 20px 0;">
                    <p><strong>关键词:</strong> ${result.keyword || 'N/A'}</p>
                    <p><strong>平台:</strong> ${this.getPlatformName(result.platform || 'amazon')}</p>
                    <p><strong>平均搜索量:</strong> ${result.avg_search_volume || 0}</p>
                    <p><strong>总体趋势:</strong> ${result.overall_trend || 'N/A'} ${result.trend_percentage ? '(' + result.trend_percentage + '%)' : ''}</p>
                </div>
                <div class="trend-table" style="overflow-x: auto; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 10px; border: 1px solid #ddd;">#</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">日期</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">搜索量</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">竞争度</th>
                                <th style="padding: 10px; border: 1px solid #ddd;">CPC</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${trendList}
                        </tbody>
                    </table>
                </div>
                <div class="result-actions" style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="appManager.exportKeywords('excel')">导出Excel</button>
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                </div>
            </div>
        `;
    }

    generateCompareHTML(comparisonData, result) {
        // 后端返回的competitors是数组
        const competitors = result.competitors || [];
        const commonKeywords = result.common_keywords || [];
        
        let competitorList = '';
        if (competitors.length > 0) {
            competitorList = competitors.map((comp, idx) => `
                <div class="competitor-item" style="padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #007bff;">
                    <h4>${idx + 1}. ${comp.title || comp.asin}</h4>
                    <p><strong>ASIN:</strong> ${comp.asin || 'N/A'}</p>
                    <p><strong>关键词数量:</strong> ${comp.keyword_count || 0}</p>
                    ${comp.top_keyword ? `<p><strong>主要关键词:</strong> ${comp.top_keyword}</p>` : ''}
                    ${comp.keywords && comp.keywords.length > 0 ? `
                        <p><strong>关键词列表:</strong> ${comp.keywords.slice(0, 5).join(', ')}${comp.keywords.length > 5 ? '...' : ''}</p>
                    ` : ''}
                </div>
            `).join('');
        } else {
            competitorList = '<p style="color: #999; text-align: center; padding: 20px;">暂无竞品数据</p>';
        }
        
        return `
            <div class="result-container">
                <h3>竞品对比完成！</h3>
                <div class="result-info" style="margin: 20px 0;">
                    <p><strong>平台:</strong> ${this.getPlatformName(result.platform || 'amazon')}</p>
                    <p><strong>竞品数量:</strong> ${competitors.length}</p>
                    <p><strong>共同关键词数量:</strong> ${commonKeywords.length}</p>
                    ${result.overlap_ratio ? `<p><strong>重叠率:</strong> ${(result.overlap_ratio * 100).toFixed(1)}%</p>` : ''}
                </div>
                ${commonKeywords.length > 0 ? `
                    <div class="common-keywords" style="margin: 20px 0;">
                        <h4>共同关键词:</h4>
                        <div style="padding: 10px; background: #e7f3ff; border-radius: 5px;">
                            ${commonKeywords.slice(0, 10).join(', ')}${commonKeywords.length > 10 ? '...' : ''}
                        </div>
                    </div>
                ` : ''}
                <div class="competitors-list" style="max-height: 400px; overflow-y: auto; margin: 20px 0;">
                    ${competitorList}
                </div>
                <div class="result-actions" style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="appManager.exportKeywords('excel')">导出Excel</button>
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                </div>
            </div>
        `;
    }

    generateLongtailHTML(longtailKeywords, result) {
        const longtailList = longtailKeywords.length > 0 
            ? longtailKeywords.map((kw, idx) => `
                <div class="keyword-item" style="padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px;">
                    ${idx + 1}. ${kw.keyword || kw}
                </div>
            `).join('')
            : '<p style="color: #999; text-align: center; padding: 20px;">未找到长尾关键词</p>';

        return `
            <div class="result-container">
                <h3>长尾关键词挖掘完成！</h3>
                <div class="result-info" style="margin: 20px 0;">
                    <p><strong>种子关键词:</strong> ${result.seed_keyword || 'N/A'}</p>
                    <p><strong>平台:</strong> ${this.getPlatformName(result.platform || 'amazon')}</p>
                    <p><strong>长尾关键词数量:</strong> ${longtailKeywords.length}</p>
                </div>
                <div class="longtail-list" style="max-height: 400px; overflow-y: auto; margin: 20px 0;">
                    ${longtailList}
                </div>
                <div class="result-actions" style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="appManager.exportKeywords('excel')">导出Excel</button>
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                </div>
            </div>
        `;
    }

    exportKeywords(format) {
        // 导出关键词功能
        try {
            const modal = document.getElementById('toolModal');
            const modalBody = modal.querySelector('.modal-body');
            if (!modalBody) return;
            
            // 提取关键词数据
            let keywords = [];
            const keywordItems = modalBody.querySelectorAll('.keyword-item');
            
            keywordItems.forEach((item, idx) => {
                const keywordText = item.querySelector('strong')?.textContent.replace(/^\d+\.\s*/, '') || '';
                if (keywordText) {
                    keywords.push({
                        '序号': idx + 1,
                        '关键词': keywordText,
                        '平台': item.querySelector('.badge')?.textContent || 'all',
                        '相关性': item.querySelector('span[style*="float"]')?.textContent.replace(/相关性:\s*/, '') || ''
                    });
                }
            });
            
            // 如果没有从HTML提取到关键词，尝试从表格提取
            if (keywords.length === 0) {
                const table = modalBody.querySelector('table');
                if (table) {
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach((row, idx) => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            keywords.push({
                                '序号': idx + 1,
                                '关键词': cells[1].textContent.trim(),
                                '搜索量': cells[2].textContent.trim(),
                                '竞争度': cells[3].textContent.trim(),
                                'CPC': cells[4].textContent.trim(),
                                '趋势': cells[5].textContent.trim()
                            });
                        }
                    });
                }
            }
            
            if (keywords.length === 0) {
                alert('没有找到可导出的关键词数据');
                return;
            }
            
            if (format === 'excel') {
                // 导出Excel（简化版，使用CSV格式）
                this.exportToCSV(keywords, 'keywords.xlsx');
            } else if (format === 'csv') {
                // 导出CSV
                this.exportToCSV(keywords, 'keywords.csv');
            }
        } catch (error) {
            console.error('导出失败:', error);
            alert(`导出失败: ${error.message}`);
        }
    }

    exportToCSV(data, filename) {
        // 导出CSV文件
        if (!data || data.length === 0) {
            alert('没有数据可导出');
            return;
        }
        
        // 获取表头
        const headers = Object.keys(data[0]);
        
        // 创建CSV内容
        let csvContent = headers.join(',') + '\n';
        
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header] || '';
                // 处理包含逗号的值
                if (value.toString().includes(',') || value.toString().includes('"')) {
                    return `"${value.toString().replace(/"/g, '""')}"`;
                }
                return value;
            });
            csvContent += values.join(',') + '\n';
        });
        
        // 创建Blob并下载
        const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log(`✅ 已导出 ${filename}，包含 ${data.length} 条关键词`);
    }

    // 将文件转换为base64
    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => {
                // 移除data:image/...;base64,前缀，只保留base64数据
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = error => reject(error);
        });
    }

    validateFile(file) {
        // 检查文件类型
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('不支持的文件格式，请选择 JPG、PNG、WEBP、GIF 或 BMP 格式的图片');
            return false;
        }

        // 检查文件大小
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            this.showError('文件大小超过限制，请选择小于 16MB 的图片');
            return false;
        }

        return true;
    }

    // 更新进度显示
    updateProgress(progress, status) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill) {
            // 平滑过渡动画
            progressFill.style.transition = 'width 0.5s ease-out';
            progressFill.style.width = `${progress}%`;
            
            // 根据进度改变颜色
            if (progress < 30) {
                progressFill.style.background = 'linear-gradient(90deg, #007bff, #0056b3)';
            } else if (progress < 70) {
                progressFill.style.background = 'linear-gradient(90deg, #28a745, #1e7e34)';
            } else {
                progressFill.style.background = 'linear-gradient(90deg, #ffd700, #ffed4e)';
            }
        }
        
        if (progressText) {
            progressText.textContent = `${progress}% - ${status}`;
            // 添加闪烁效果提示用户
            progressText.style.animation = 'none';
            setTimeout(() => {
                if (progressText) {
                    progressText.style.animation = 'pulse 1s ease-in-out';
                }
            }, 10);
        }
    }

    showProcessingStatus(toolName) {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        // 根据工具类型设置不同的提示词
        const toolType = toolName || this.currentTool || 'background_remover';
        const processingMessages = {
            'background_remover': {
                title: '正在处理您的图片',
                subtitle: 'AI智能识别背景，请稍候...',
                tip: '💡 提示：处理时间取决于图片大小和复杂度'
            },
            'image_compressor': {
                title: '正在压缩您的图片',
                subtitle: '优化图片大小，保持质量，请稍候...',
                tip: '💡 提示：压缩时间取决于图片大小和压缩质量'
            },
            'format_converter': {
                title: '正在转换图片格式',
                subtitle: '转换图片格式，请稍候...',
                tip: '💡 提示：转换时间取决于图片大小和格式'
            },
            'image_cropper': {
                title: '正在裁剪您的图片',
                subtitle: '精确裁剪图片尺寸，请稍候...',
                tip: '💡 提示：裁剪时间取决于图片大小'
            },
            'keyword_analyzer': {
                title: '正在分析关键词',
                subtitle: 'AI智能提取关键词，分析竞争度，请稍候...',
                tip: '💡 提示：分析时间取决于关键词数量和复杂度'
            },
            'currency_converter': {
                title: '正在处理汇率换算',
                subtitle: '获取实时汇率，计算换算结果，请稍候...',
                tip: '💡 提示：换算时间取决于网络连接速度'
            },
            'add_watermark': {
                title: '正在添加水印',
                subtitle: '处理图片，添加水印文字，请稍候...',
                tip: '💡 提示：处理时间取决于图片大小'
            },
            'remove_watermark': {
                title: '正在移除水印',
                subtitle: '智能识别水印区域，修复图片，请稍候...',
                tip: '💡 提示：处理时间取决于图片大小和水印复杂度'
            }
        };
        
        const messages = processingMessages[toolType] || processingMessages['background_remover'];
        
        modalBody.innerHTML = `
            <style>
                .processing-container {
                    text-align: center;
                    padding: 40px 20px;
                }
                .processing-animation {
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 30px;
                    position: relative;
                }
                .processing-animation .spinner {
                    width: 100%;
                    height: 100%;
                    border: 5px solid rgba(255, 215, 0, 0.2);
                    border-top: 5px solid #ffd700;
                    border-right: 5px solid #ffed4e;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                    box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.6; }
                }
                .processing-text {
                    margin-top: 20px;
                }
                .processing-title {
                    font-size: 20px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                    animation: pulse 2s ease-in-out infinite;
                }
                .processing-subtitle {
                    font-size: 15px;
                    color: #666;
                    margin-bottom: 20px;
                }
                .processing-progress {
                    margin: 25px 0;
                }
                .progress-bar {
                    width: 100%;
                    height: 12px;
                    background-color: #f0f0f0;
                    border-radius: 10px;
                    overflow: hidden;
                    margin-bottom: 12px;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                }
                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #007bff, #28a745, #ffd700);
                    width: 0%;
                    transition: width 0.5s ease-out;
                    border-radius: 10px;
                    position: relative;
                    overflow: hidden;
                }
                .progress-fill::after {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    bottom: 0;
                    right: 0;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                    animation: shimmer 2s infinite;
                }
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
                .progress-text {
                    font-size: 15px;
                    color: #333;
                    font-weight: 600;
                }
                .processing-tips {
                    margin-top: 25px;
                    padding: 15px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 10px;
                    border-left: 4px solid #ffd700;
                }
                .tip {
                    font-size: 13px;
                    color: #666;
                    line-height: 1.6;
                }
            </style>
            <div class="processing-container">
                <div class="processing-animation">
                    <div class="spinner"></div>
                </div>
                <div class="processing-text">
                    <div class="processing-title">${messages.title}</div>
                    <div class="processing-subtitle">${messages.subtitle}</div>
                    <div class="processing-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <div class="progress-text" id="progressText">0% - 准备中...</div>
                    </div>
                </div>
                <div class="processing-tips">
                    <div class="tip">${messages.tip}</div>
                </div>
            </div>
        `;
        
        this.showModal(modal);
    }

    showSuccessResult(result, toolType) {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        let resultHTML = '';
        let imageUrl = '';
        
        switch(toolType) {
            case 'background_remover':
                imageUrl = result.processed_image || '';
                const warningMsg = result.warning || '';
                resultHTML = `
                    <div class="result-container">
                        <h3>背景移除完成！</h3>
                        ${warningMsg ? `<div class="alert alert-warning" style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                            <strong>⚠️ 警告：</strong>${warningMsg}
                        </div>` : ''}
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="背景移除结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="background_removed.png" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
                
            case 'image_compressor':
                imageUrl = result.compressed_image || '';
                const format = result.compressed_image ? (result.compressed_image.includes('jpeg') || result.compressed_image.includes('jpg') ? 'jpg' : result.compressed_image.includes('png') ? 'png' : result.compressed_image.includes('webp') ? 'webp' : 'jpg') : 'jpg';
                resultHTML = `
                    <div class="result-container">
                        <h3>图片压缩完成！</h3>
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="压缩结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>原始大小: ${result.original_size ? (result.original_size / 1024).toFixed(2) + ' KB' : '未知'}</p>
                            <p>压缩后大小: ${result.compressed_size ? (result.compressed_size / 1024).toFixed(2) + ' KB' : '未知'}</p>
                            <p>压缩率: ${result.compression_ratio ? result.compression_ratio + '%' : '未知'}</p>
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="compressed_image.${format}" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
                
            case 'format_converter':
                imageUrl = result.converted_image || '';
                const outputExt = result.output_format ? result.output_format.toLowerCase() : 'png';
                resultHTML = `
                    <div class="result-container">
                        <h3>格式转换完成！</h3>
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="转换结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>目标格式: ${result.output_format || '未知'}</p>
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="converted_image.${outputExt}" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
                
            case 'image_cropper':
                imageUrl = result.cropped_image || '';
                const cropInfo = result.crop_info || {};
                resultHTML = `
                    <div class="result-container">
                        <h3>图片裁剪完成！</h3>
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="裁剪结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>裁剪区域: ${cropInfo.width || '未知'} x ${cropInfo.height || '未知'}</p>
                            <p>位置: (${cropInfo.x || 0}, ${cropInfo.y || 0})</p>
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="cropped_image.png" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
            case 'image_rotate_flip':
                imageUrl = result.processed_image || '';
                const operationName = result.operation_name || result.operation || '旋转/翻转';
                resultHTML = `
                    <div class="result-container">
                        <h3>图片${operationName}完成！</h3>
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="处理结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>操作类型: ${operationName}</p>
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="rotated_image.png" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
                
            // 旧版水印功能（已注释）
            // case 'add_watermark':
            //     ...
            //     break;
            
            // 新版水印功能
            case 'add_watermark_v2':
                console.log('🎯🎯🎯 [showSuccessResult] 新版水印 - 显示结果');
                console.log('🎯 结果数据:', result);
                imageUrl = result.processed_image || '';
                console.log('🎯 图片URL:', imageUrl ? '有图片' : '无图片');
                resultHTML = `
                    <div class="result-container">
                        <h3>水印添加完成！（新版）</h3>
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="加水印结果" class="result-image" onerror="console.error('❌ 图片加载失败:', this.src)">
                        </div>
                        <div class="result-info">
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="watermarked_v2.png" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                console.log('✅ 新版水印结果HTML已生成');
                break;
                
            case 'add_watermark':
                imageUrl = result.processed_image || '';
                const watermarkWarning = result.warning || '';
                resultHTML = `
                    <div class="result-container">
                        <h3>水印添加完成！</h3>
                        ${watermarkWarning ? `<div class="alert alert-warning" style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                            <strong>⚠️ 提示：</strong>${watermarkWarning}
                        </div>` : ''}
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="加水印结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="watermarked.png" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
                
            case 'remove_watermark':
                imageUrl = result.processed_image || '';
                resultHTML = `
                    <div class="result-container">
                        <h3>水印移除完成！</h3>
                        <div class="result-preview">
                            <img src="${imageUrl}" alt="去水印结果" class="result-image">
                        </div>
                        <div class="result-info">
                            <p>今日使用: ${result.current_usage || 0}/${result.daily_limit || '∞'}</p>
                            <p>剩余次数: ${result.remaining_usage !== undefined ? (result.remaining_usage === -1 ? '无限制' : result.remaining_usage) : '未知'}</p>
                        </div>
                        <div class="result-actions">
                            <a href="${imageUrl}" download="watermark_removed.png" class="btn btn-primary">下载图片</a>
                            <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                            <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新处理</button>
                        </div>
                    </div>
                `;
                break;
        }
        
        modalBody.innerHTML = resultHTML;
        this.showModal(modal);
    }

    showError(message) {
        const modal = document.getElementById('toolModal');
        const modalBody = modal.querySelector('.modal-body');
        
        // 友好的错误提示
        let friendlyMessage = message;
        if (message.includes('网络') || message.includes('Network') || message.includes('fetch')) {
            friendlyMessage = '网络连接失败，请检查您的网络连接后重试';
        } else if (message.includes('超时') || message.includes('timeout')) {
            friendlyMessage = '处理超时，请稍后重试或尝试使用较小的图片';
        } else if (message.includes('大小') || message.includes('size')) {
            friendlyMessage = '图片文件过大，请使用小于16MB的图片';
        } else if (message.includes('格式') || message.includes('format')) {
            friendlyMessage = '不支持的图片格式，请使用JPG、PNG或WebP格式';
        } else if (message.includes('登录') || message.includes('auth')) {
            friendlyMessage = '登录已过期，请重新登录';
        }
        
        modalBody.innerHTML = `
            <style>
                .error-container {
                    text-align: center;
                    padding: 40px 20px;
                }
                .error-icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                    animation: shake 0.5s ease-in-out;
                }
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-10px); }
                    75% { transform: translateX(10px); }
                }
                .error-container h3 {
                    font-size: 22px;
                    color: #dc3545;
                    margin-bottom: 15px;
                    font-weight: bold;
                }
                .error-message {
                    font-size: 16px;
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 30px;
                    padding: 15px;
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    border-radius: 5px;
                    text-align: left;
                }
                .error-actions {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                }
            </style>
            <div class="error-container">
                <div class="error-icon">❌</div>
                <h3>处理失败</h3>
                <p class="error-message">${friendlyMessage}</p>
                <div class="error-actions">
                    <button class="btn btn-primary" onclick="if(window.appManager) { window.appManager.closeModal('toolModal'); }">关闭</button>
                    <button class="btn btn-secondary" onclick="if(window.appManager) { window.appManager.resetTool(); window.appManager.showModal('toolModal'); }">重新尝试</button>
                </div>
            </div>
        `;
        
        this.showModal(modal);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    isDevelopmentMode() {
        return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    }

    // 模态框相关方法
    showModal(modal) {
        // 如果传入的是字符串（模态框ID），先获取元素
        if (typeof modal === 'string') {
            modal = document.getElementById(modal);
        }
        
        if (modal && modal.style) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        } else {
            console.warn('showModal: 无法找到模态框元素', modal);
        }
    }
    
    resetTool() {
        // 重置处理状态
        this.isProcessing = false;
        
        // 保存当前工具类型（不重置，因为重新处理时需要使用相同的工具）
        const toolType = this.currentTool;
        
        // 重置进度
        this.updateProgress(0, '');
        
        // 重置批量处理状态
        this.batchFiles = [];
        this.batchResults = [];
        this.isBatchProcessing = false;
        
        // 清除模态框body的内容，重置为初始状态
        const modalBody = document.querySelector('#toolModal .modal-body');
        if (modalBody) {
            // 重置为初始状态
            const uploadHTML = `
                <div id="uploadArea" class="upload-area">
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">点击或拖拽图片到这里</div>
                    <div id="fileName" class="file-name"></div>
                    <div id="fileSize" class="file-size"></div>
                </div>
                <input type="file" id="fileInput" accept="image/*" style="display: none;">
                <div id="toolOptions"></div>
            `;
            
            modalBody.innerHTML = uploadHTML;
            
            // 重置上传区域状态
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const fileName = document.getElementById('fileName');
            const fileSize = document.getElementById('fileSize');
            
            if (uploadArea) {
                uploadArea.classList.remove('has-file');
                uploadArea.style.display = 'block';
            }
            
            if (fileInput) {
                fileInput.value = '';
            }
            
            if (fileName) {
                fileName.textContent = '';
            }
            
            if (fileSize) {
                fileSize.textContent = '';
            }
            
            // 重建工具选项（如果之前有工具类型）
            if (toolType) {
                this.setupToolOptions(toolType);
            }
            
            // 重新绑定文件上传事件（如果之前有工具类型）
            if (toolType) {
                this.setupFileUpload(toolType);
            }
        }
    }

    closeModal(modal) {
        // 如果传入的是字符串（模态框ID），先获取元素
        if (typeof modal === 'string') {
            modal = document.getElementById(modal);
        }
        
        // 如果传入的是DOM元素选择器，先获取元素
        if (modal && typeof modal === 'object' && modal.nodeType === undefined) {
            // 可能是jQuery对象或其他对象
            if (modal.length && modal[0]) {
                modal = modal[0];
            }
        }
        
        if (modal && modal.style) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            
            // 微信登录相关代码暂时注释（等后续开通后再启用）
            /*
            if (modal.id === 'wechatLoginModal') {
                if (this.wechatPollingInterval) {
                    clearInterval(this.wechatPollingInterval);
                    this.wechatPollingInterval = null;
                }
                this.wechatSessionId = null;
            }
            */
            
            // 如果是工具模态框，清除结果内容
            if (modal.id === 'toolModal') {
                this.resetTool();
            }
        } else {
            console.warn('closeModal: 无法找到模态框元素', modal);
        }
    }

    showLoginModal() {
        // 显示登录模态框，并清除之前的错误提示和表单
        this.clearLoginError();
        const modal = document.getElementById('loginModal');
        if (modal) {
            // 如果模态框已经显示，不重复打开（避免重复点击问题）
            if (modal.style.display === 'flex') {
                return;
            }
            // 清空表单
            const emailInput = document.getElementById('loginEmail');
            const passwordInput = document.getElementById('loginPassword');
            if (emailInput) emailInput.value = '';
            if (passwordInput) passwordInput.value = '';
            this.showModal(modal);
        }
    }

    showRegisterModal() {
        const modal = document.getElementById('registerModal');
        this.showModal(modal);
    }
    
    // 微信登录功能暂时隐藏（需要微信开放平台认证，费用300元）
    // 等后续开通微信登录后再取消注释
    /*
    async showWechatLoginModal() {
        // 关闭其他模态框
        this.closeModal('loginModal');
        this.closeModal('registerModal');
        
        // 显示微信登录模态框
        const modal = document.getElementById('wechatLoginModal');
        if (modal) {
            this.showModal(modal);
            
            // 获取并显示二维码
            await this.loadWechatQRCode();
        } else {
            console.error('未找到微信登录模态框');
        }
    }
    */
    
    // switchToTraditionalLogin 方法保留，但简化（不涉及微信登录）
    switchToTraditionalLogin() {
        // 显示传统登录模态框
        setTimeout(() => {
            this.showLoginModal();
        }, 300);
    }

    showUpgradeModal() {
        const modal = document.getElementById('upgradeModal');
        this.showModal(modal);
    }

    toggleUserMenu() {
        const menu = document.getElementById('userDropdown');
        if (menu) {
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail').value.trim().toLowerCase();
        const password = document.getElementById('loginPassword').value;
        
        // 清除之前的错误提示
        this.clearLoginError();
        
        // 基本验证
        if (!email || !password) {
            this.showLoginError('请填写邮箱和密码');
            return;
        }
        
        try {
            const result = await this.authManager.login(email, password);
            if (result.success) {
                this.closeModal(document.getElementById('loginModal'));
                this.updateUIForLoggedInUser();
                this.loadUsageStats();
                // 清空表单
                document.getElementById('loginEmail').value = '';
                document.getElementById('loginPassword').value = '';
            } else {
                // 在登录表单中显示错误，而不是alert
                this.showLoginError(result.error || '登录失败，请检查邮箱和密码是否正确');
                // 清空密码框
                document.getElementById('loginPassword').value = '';
            }
        } catch (error) {
            this.showLoginError('登录失败: ' + error.message);
            // 清空密码框
            document.getElementById('loginPassword').value = '';
        }
    }
    
    showLoginError(message) {
        // 在登录表单中显示错误提示
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) return;
        
        // 查找或创建错误提示元素
        let errorDiv = loginForm.querySelector('.login-error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'login-error-message';
            errorDiv.style.cssText = 'background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 12px; border-radius: 6px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;';
            loginForm.insertBefore(errorDiv, loginForm.firstChild);
        }
        
        errorDiv.innerHTML = `
            <span style="flex: 1;">${message}</span>
            <button type="button" onclick="if(window.appManager) window.appManager.clearLoginError();" style="background: none; border: none; color: #721c24; font-size: 20px; cursor: pointer; padding: 0; margin-left: 10px; line-height: 1; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">&times;</button>
        `;
        errorDiv.style.display = 'flex';
    }
    
    clearLoginError() {
        // 清除登录错误提示
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) return;
        
        const errorDiv = loginForm.querySelector('.login-error-message');
        if (errorDiv) {
            errorDiv.style.display = 'none';
            errorDiv.innerHTML = '';
        }
    }
    
    switchToLogin() {
        // 切换到登录模态框
        this.closeModal(document.getElementById('registerModal'));
        this.showLoginModal();
    }

    async handleRegister(e) {
        e.preventDefault();
        
        // 防止重复提交
        const submitButton = e.target.querySelector('button[type="submit"]');
        const originalText = submitButton ? submitButton.textContent : '注册';
        
        if (submitButton && submitButton.disabled) {
            console.log('注册正在处理中，忽略重复提交');
            return;
        }
        
        // 禁用提交按钮，防止重复提交
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = '注册中...';
        }
        
        try {
            // 获取所有注册字段
            const name = document.getElementById('registerName')?.value?.trim();
            const email = document.getElementById('registerEmail')?.value?.trim().toLowerCase();
            const password = document.getElementById('registerPassword')?.value;
            const confirmPassword = document.getElementById('confirmPassword')?.value;
            
            // 优先使用输入框的值，如果没有则从localStorage获取
            let inviteCode = document.getElementById('registerInviteCode')?.value?.trim().toUpperCase();
            if (!inviteCode) {
                inviteCode = localStorage.getItem('pending_invite_code');
            }
            if (inviteCode) {
                inviteCode = inviteCode.toUpperCase();
            }
            
            // 验证必填字段
            if (!name) {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText;
                }
                alert('请输入姓名');
                return;
            }
            if (!email) {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText;
                }
                alert('请输入邮箱地址');
                return;
            }
            if (!password) {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText;
                }
                alert('请输入密码');
                return;
            }
            if (password.length < 6) {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText;
                }
                alert('密码至少6位');
                return;
            }
            if (password !== confirmPassword) {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText;
                }
                alert('两次输入的密码不一致');
                return;
            }
            
            console.log('开始注册:', { email, name, invite_code: inviteCode || '无' });
            const result = await this.authManager.register(email, password, name, inviteCode);
            console.log('注册结果:', result);
            
            if (result.success) {
                // 注册成功，先关闭模态框
                this.closeModal('registerModal');
                
                // 延迟加载统计信息，确保token已正确保存
                setTimeout(() => {
                    this.updateUIForLoggedInUser();
                    // 延迟加载统计，避免立即调用导致401
                    setTimeout(() => {
                        this.loadUsageStats();
                    }, 500);
                }, 100);
                
                alert('注册成功！欢迎使用！');
                
                // 清空注册表单
                document.getElementById('registerForm')?.reset();
            } else {
                // 注册失败，显示错误信息
                const errorMsg = result.error || '注册失败';
                console.error('注册失败:', errorMsg);
                alert('注册失败: ' + errorMsg);
                
                // 如果错误是"用户已存在"，提示用户直接登录
                if (errorMsg.includes('用户已存在') || errorMsg.includes('already exists')) {
                    alert('该邮箱已注册，请直接登录！');
                    // 切换到登录页面
                    this.closeModal('registerModal');
                    setTimeout(() => {
                        this.showLoginModal();
                        // 自动填充邮箱
                        const loginEmail = document.getElementById('loginEmail');
                        if (loginEmail) {
                            loginEmail.value = email;
                        }
                    }, 300);
                } else {
                    // 其他错误，清空邮箱输入框让用户重新输入
                    const emailInput = document.getElementById('registerEmail');
                    if (emailInput) {
                        emailInput.value = '';
                        emailInput.focus();
                    }
                }
            }
        } catch (error) {
            console.error('注册错误:', error);
            alert('注册失败: ' + (error.message || '未知错误'));
        } finally {
            // 恢复提交按钮（延迟一点，避免太快恢复导致重复提交）
            setTimeout(() => {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText || '注册';
                }
            }, 1000);
        }
    }

    async loadUsageStats() {
        if (!this.authManager.isAuthenticated()) {
            console.log('用户未登录，跳过加载使用统计');
            return;
        }

        try {
            // 检查token是否存在
            const token = this.authManager.getToken();
            if (!token) {
                console.warn('Token不存在，跳过加载使用统计');
                return;
            }
            
            // 使用 loadUserUsageStats 方法，它会自动更新显示
            await this.authManager.loadUserUsageStats();
        } catch (error) {
            console.error('加载使用统计失败:', error);
            // 如果是401错误，说明token无效，可能需要重新登录
            if (error.message && error.message.includes('401')) {
                console.warn('Token无效，可能需要重新登录');
            }
        }
    }

    updateUsageStatsDisplay(stats) {
        const usageStats = document.getElementById('usageStats');
        if (usageStats) {
            usageStats.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">今日使用:</span>
                    <span class="stat-value">${stats.today_usage || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">剩余次数:</span>
                    <span class="stat-value">${stats.remaining_credits || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">会员等级:</span>
                    <span class="stat-value">${stats.membership_level || '免费'}</span>
                </div>
            `;
        }
    }

    // 退出登录
    logout() {
        this.authManager.logout();
        this.updateUIForLoggedOutUser();
        // 刷新页面以确保状态同步
        window.location.reload();
    }

    // 显示用户资料
    showProfile() {
        const profileModal = document.getElementById('profileModal');
        if (profileModal) {
            this.showModal(profileModal);
            this.loadUserProfile();
        }
    }

    // 加载用户资料
    async loadUserProfile() {
        if (!this.authManager.isAuthenticated()) {
            return;
        }

        try {
            // 先加载最新的用户信息（从API获取）
            await this.authManager.loadUserUsageStats();
            
            // 获取最新的用户信息
            const user = this.authManager.getUser();
            if (user) {
                const profileName = document.getElementById('profileName');
                const profileEmail = document.getElementById('profileEmail');
                const profilePlan = document.getElementById('profilePlan');
                const profileCredits = document.getElementById('profileCredits');
                const profileUsage = document.getElementById('profileUsage');
                const profileDays = document.getElementById('profileDays');

                if (profileName) profileName.textContent = user.name || user.email || '用户';
                if (profileEmail) profileEmail.textContent = user.email || '';
                
                // 显示会员等级（确保使用正确的plan字段）
                const userPlan = user.plan || user.membership_type || 'free';
                const planName = this.getPlanName(userPlan);
                
                console.log('📋 更新个人资料页面会员信息:', {
                    plan: userPlan,
                    planName: planName,
                    user: user
                });
                
                if (profilePlan) {
                    profilePlan.textContent = planName;
                    // 根据会员等级设置样式
                    profilePlan.className = 'plan-badge';
                    if (userPlan && userPlan !== 'free') {
                        profilePlan.style.background = '#667eea';
                        profilePlan.style.color = 'white';
                    } else {
                        profilePlan.style.background = '#f0f0f0';
                        profilePlan.style.color = '#666';
                    }
                }
                
                // 显示会员等级（在stat-card中）
                if (profileCredits) {
                    profileCredits.textContent = planName;
                }
                
                // 显示使用统计
                await this.loadUsageStats();
                
                // 更新使用次数显示
                if (user.usage_stats) {
                    const stats = user.usage_stats;
                    if (profileUsage) {
                        profileUsage.textContent = stats.today_usage || 0;
                    }
                    if (profileDays) {
                        profileDays.textContent = stats.usage_days || 0;
                    }
                    
                    // 更新各个工具的使用次数
                    this.updateProfileUsageStats(stats);
                }
                
                // 加载邀请码信息
                await this.loadInviteInfo();
            }
        } catch (error) {
            console.error('加载用户资料失败:', error);
        }
    }
    
    // 更新个人资料页面的使用统计
    updateProfileUsageStats(stats) {
        if (!stats) {
            console.warn('使用统计数据为空');
            return;
        }
        
        console.log('更新个人资料页面使用统计:', stats);
        
        // 更新各个工具的使用次数显示
        const toolMappings = {
            'background_remover': { count: 'bgRemoverCount', progress: 'bgRemoverProgress' },
            'image_compressor': { count: 'compressorCount', progress: 'compressorProgress' },
            'format_converter': { count: 'converterCount', progress: 'converterProgress' },
            'image_cropper': { count: 'cropperCount', progress: 'cropperProgress' },
            'image_enhancer': { count: 'enhancerCount', progress: 'enhancerProgress' },
            'remove_watermark': { count: 'watermarkCount', progress: 'watermarkProgress' },
            'keyword_analyzer': { count: 'keywordCount', progress: 'keywordProgress' },
            'currency_converter': { count: 'currencyCount', progress: 'currencyProgress' },
            'unit_converter': { count: 'unitCount', progress: 'unitProgress' },
            'shipping_calculator': { count: 'shippingCount', progress: 'shippingProgress' },
            'add_watermark': { count: 'addWatermarkCount', progress: 'addWatermarkProgress' }
        };
        
        Object.entries(toolMappings).forEach(([toolKey, elements]) => {
            const toolStats = stats[toolKey];
            if (toolStats) {
                // 更新使用次数
                const countElement = document.getElementById(elements.count);
                if (countElement) {
                    const current = toolStats.current_usage || 0;
                    const limit = toolStats.daily_limit === -1 ? '∞' : toolStats.daily_limit;
                    countElement.textContent = `${current}/${limit}`;
                    console.log(`更新 ${toolKey} 使用次数: ${current}/${limit}`);
                }
                
                // 更新进度条
                const progressElement = document.getElementById(elements.progress);
                if (progressElement) {
                    if (toolStats.daily_limit > 0) {
                        const percentage = ((toolStats.current_usage || 0) / toolStats.daily_limit) * 100;
                        progressElement.style.width = `${Math.min(percentage, 100)}%`;
                        
                        // 根据使用率设置颜色
                        if (percentage >= 90) {
                            progressElement.style.backgroundColor = '#dc3545'; // 红色
                        } else if (percentage >= 70) {
                            progressElement.style.backgroundColor = '#ffc107'; // 黄色
                        } else {
                            progressElement.style.backgroundColor = '#28a745'; // 绿色
                        }
                    } else if (toolStats.daily_limit === -1) {
                        // 无限制时显示满进度条
                        progressElement.style.width = '100%';
                        progressElement.style.backgroundColor = '#667eea'; // 紫色
                    }
                }
            } else {
                // 如果没有统计数据，显示0
                const countElement = document.getElementById(elements.count);
                if (countElement) {
                    countElement.textContent = '0/0';
                }
            }
        });
    }
    
    // 加载邀请码信息（用户资料页面和主页）
    async loadInviteInfo() {
        try {
            const token = this.authManager.getToken();
            if (!token) return;
            
            const response = await fetch(`${this.apiBaseUrl}/api/invite/stats`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // 用户资料页面的邀请码
                    const inviteCodeDisplay = document.getElementById('inviteCodeDisplay');
                    const invitedCount = document.getElementById('invitedCount');
                    
                    // 邀请模态框的邀请码
                    const inviteCodeModal = document.getElementById('inviteCodeModal');
                    const invitedCountModal = document.getElementById('invitedCountModal');
                    
                    if (inviteCodeDisplay) {
                        inviteCodeDisplay.value = data.invite_code || '未生成';
                    }
                    if (invitedCount) {
                        invitedCount.textContent = `已邀请: ${data.invited_count || 0}人`;
                    }
                    if (inviteCodeModal) {
                        inviteCodeModal.value = data.invite_code || '未生成';
                    }
                    if (invitedCountModal) {
                        invitedCountModal.textContent = `已邀请: ${data.invited_count || 0}人`;
                    }
                }
            }
        } catch (error) {
            console.error('加载邀请信息失败:', error);
        }
    }
    
    // 显示邀请推荐模态框
    showInviteModal() {
        if (!this.authManager.isAuthenticated()) {
            alert('请先登录后再邀请好友');
            this.showLoginModal();
            return;
        }
        
        const modal = document.getElementById('inviteModal');
        if (!modal) {
            console.error('未找到邀请模态框元素');
            alert('邀请模态框加载失败，请刷新页面重试');
            return;
        }
        
        this.showModal(modal);
        // 延迟加载邀请信息，确保模态框已显示
        setTimeout(() => {
            this.loadInviteInfoForModal();
        }, 100);
    }
    
    // 为模态框加载邀请信息
    async loadInviteInfoForModal() {
        try {
            const token = this.authManager.getToken();
            if (!token) {
                console.error('未找到token，无法加载邀请信息');
                return;
            }
            
            // 显示加载状态
            const inviteCodeModal = document.getElementById('inviteCodeModal');
            const invitedCountModal = document.getElementById('invitedCountModal');
            if (inviteCodeModal) {
                inviteCodeModal.value = '加载中...';
            }
            
            const response = await fetch(`${this.apiBaseUrl}/api/invite/stats`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                console.error('获取邀请信息失败:', response.status, response.statusText);
                const errorData = await response.json().catch(() => ({}));
                console.error('错误详情:', errorData);
                
                if (inviteCodeModal) {
                    inviteCodeModal.value = '加载失败，请刷新重试';
                }
                return;
            }
            
            const data = await response.json();
            console.log('邀请信息响应:', data);
            
            if (data.success) {
                const inviteCode = data.invite_code || '';
                
                if (inviteCodeModal) {
                    inviteCodeModal.value = inviteCode || '未生成';
                }
                if (invitedCountModal) {
                    invitedCountModal.textContent = `已邀请: ${data.invited_count || 0}人`;
                }
                
                // 如果还是没有邀请码，尝试调用生成接口
                if (!inviteCode || inviteCode === '未生成') {
                    console.log('邀请码为空，尝试生成...');
                    await this.generateInviteCode();
                }
            } else {
                console.error('API返回失败:', data);
                if (inviteCodeModal) {
                    inviteCodeModal.value = '获取失败，请刷新重试';
                }
            }
        } catch (error) {
            console.error('加载邀请信息失败:', error);
            const inviteCodeModal = document.getElementById('inviteCodeModal');
            if (inviteCodeModal) {
                inviteCodeModal.value = '加载失败: ' + error.message;
            }
        }
    }
    
    // 生成邀请码
    async generateInviteCode() {
        try {
            const token = this.authManager.getToken();
            if (!token) return;
            
            const response = await fetch(`${this.apiBaseUrl}/api/invite/code`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.invite_code) {
                    const inviteCodeModal = document.getElementById('inviteCodeModal');
                    const inviteCodeDisplay = document.getElementById('inviteCodeDisplay');
                    
                    if (inviteCodeModal) {
                        inviteCodeModal.value = data.invite_code;
                    }
                    if (inviteCodeDisplay) {
                        inviteCodeDisplay.value = data.invite_code;
                    }
                    console.log('✅ 邀请码生成成功:', data.invite_code);
                }
            }
        } catch (error) {
            console.error('生成邀请码失败:', error);
        }
    }
    
    // 复制邀请码（用户资料页面）
    copyInviteCode() {
        const inviteCodeDisplay = document.getElementById('inviteCodeDisplay');
        if (inviteCodeDisplay && inviteCodeDisplay.value && inviteCodeDisplay.value !== '加载中...') {
            inviteCodeDisplay.select();
            document.execCommand('copy');
            alert('邀请码已复制到剪贴板！\n\n分享给好友，双方各得免费使用次数奖励！');
        } else {
            alert('邀请码未加载，请稍候再试');
        }
    }
    
    // 复制邀请码（模态框）
    copyInviteCodeModal() {
        const inviteCodeModal = document.getElementById('inviteCodeModal');
        if (inviteCodeModal && inviteCodeModal.value && inviteCodeModal.value !== '加载中...') {
            inviteCodeModal.select();
            document.execCommand('copy');
            alert('✅ 邀请码已复制到剪贴板！\n\n分享给好友，双方各得免费使用次数奖励！');
        } else {
            alert('邀请码未加载，请稍候再试');
        }
    }
    
    // 分享邀请码
    shareInviteCode(type) {
        const inviteCodeModal = document.getElementById('inviteCodeModal');
        if (!inviteCodeModal || !inviteCodeModal.value || inviteCodeModal.value === '加载中...') {
            alert('邀请码未加载，请稍候再试');
            return;
        }
        
        const inviteCode = inviteCodeModal.value;
        const inviteUrl = `${window.location.origin}${window.location.pathname}?invite=${inviteCode}`;
        
        if (type === 'link') {
            // 复制邀请链接
            navigator.clipboard.writeText(inviteUrl).then(() => {
                alert('✅ 邀请链接已复制到剪贴板！\n\n' + inviteUrl + '\n\n分享给好友即可获得奖励！');
            }).catch(() => {
                // 降级方案
                const textarea = document.createElement('textarea');
                textarea.value = inviteUrl;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                alert('✅ 邀请链接已复制到剪贴板！\n\n' + inviteUrl);
            });
        } else if (type === 'code') {
            // 复制邀请码
            navigator.clipboard.writeText(inviteCode).then(() => {
                alert('✅ 邀请码已复制到剪贴板！\n\n邀请码：' + inviteCode + '\n\n分享给好友，注册时输入即可获得奖励！');
            }).catch(() => {
                inviteCodeModal.select();
                document.execCommand('copy');
                alert('✅ 邀请码已复制到剪贴板！\n\n邀请码：' + inviteCode);
            });
        }
    }

    // 获取套餐名称
    getPlanName(plan) {
        const planNames = {
            'free': '免费版',
            'basic': '基础版',
            'professional': '专业版',
            'flagship': '旗舰版',
            'enterprise': '企业版'
        };
        return planNames[plan] || '免费版';
    }

    // 开发模式检查
    isDevelopmentMode() {
        return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    }
}

// 将AppManager类暴露到全局作用域（确保在所有情况下都可用）
if (typeof window !== 'undefined') {
    window.AppManager = AppManager;
    
    // 如果页面加载时立即需要，尝试自动初始化
    if (document.readyState === 'complete' && typeof window.appManager === 'undefined') {
        // 页面已经加载完成，但appManager未初始化，尝试初始化
        setTimeout(() => {
            if (typeof AuthManager !== 'undefined' && typeof window.appManager === 'undefined') {
                try {
                    console.log('🎯🎯🎯 自动初始化AppManager...');
                    window.authManager = window.authManager || new AuthManager();
                    window.appManager = new AppManager();
                    console.log('🎯🎯🎯 AppManager创建完成！', window.appManager);
                    console.log('✅ AppManager自动初始化完成');
                } catch (error) {
                    console.error('❌ AppManager自动初始化失败:', error);
                }
            }
        }, 100);
    }
}

// 微信登录功能暂时隐藏（需要微信开放平台认证，费用300元）
// 等后续开通微信登录后再取消注释
/*
// 全局微信登录函数（已废弃，使用二维码登录）
async function simulateWechatLogin() {
    console.warn('simulateWechatLogin已废弃，请使用二维码登录');
    alert('请使用微信扫码登录');
}
*/