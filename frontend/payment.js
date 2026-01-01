/**
 * 支付管理模块
 * 处理支付宝、微信支付的界面和交互
 */

class PaymentManager {
    constructor() {
        this.currentPlan = null;
        this.currentBillingPeriod = 'monthly';  // 'monthly' 或 'yearly'
        this.currentPaymentMethod = null;
        this.orderData = null;
        // 自动检测API地址
        this.apiBaseUrl = this.getApiBaseUrl();
        this.init();
    }

    getApiBaseUrl() {
        // 如果是本地文件协议或访问 localhost，使用本地开发服务器
        if (window.location.protocol === 'file:' ||
            window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        }
        // 否则使用当前域名（生产环境）
        return window.location.origin;
    }

    init() {
        this.bindEvents();
        this.loadMembershipPlans();
        this.setupPaymentForms();
    }

    bindEvents() {
        // 绑定支付方式选择事件
        document.querySelectorAll('.method-card').forEach(method => {
            method.addEventListener('click', (e) => {
                const methodType = e.currentTarget.dataset.method;
                if (methodType) {
                    this.selectPaymentMethod(methodType);
                }
            });
        });

        // 绑定月付/年付切换事件
        const monthlyBtn = document.getElementById('monthlyBtn');
        const yearlyBtn = document.getElementById('yearlyBtn');
        if (monthlyBtn) {
            monthlyBtn.addEventListener('click', () => {
                this.selectBillingPeriod('monthly');
            });
        }
        if (yearlyBtn) {
            yearlyBtn.addEventListener('click', () => {
                this.selectBillingPeriod('yearly');
            });
        }

        // 绑定支付确认按钮事件
        const confirmPaymentBtn = document.getElementById('confirmPaymentBtn');
        if (confirmPaymentBtn) {
            confirmPaymentBtn.addEventListener('click', () => {
                this.confirmPayment();
            });
        }

        // 绑定关闭支付模态框事件
        document.querySelectorAll('.close-payment-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closePaymentModal();
            });
        });
    }

    bindUpgradeButtons() {
        // 绑定升级按钮事件
        const upgradeButtons = document.querySelectorAll('.upgrade-btn');
        console.log('找到升级按钮数量:', upgradeButtons.length);

        upgradeButtons.forEach((btn, index) => {
            // 先移除可能存在的旧监听器（通过克隆节点）
            const newBtn = btn.cloneNode(true);
            if (btn.parentNode) {
                btn.parentNode.replaceChild(newBtn, btn);
            }

            // 绑定新的事件
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const plan = newBtn.dataset.plan || newBtn.getAttribute('data-plan');
                console.log(`点击升级按钮 ${index}, 计划:`, plan, '按钮元素:', newBtn);
                if (plan) {
                    this.showUpgradeModal(plan);
                } else {
                    console.error('升级按钮缺少 plan 属性，按钮:', newBtn);
                }
            });
        });

        console.log('✅ 升级按钮事件绑定完成');
    }

    async loadMembershipPlans() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/payment/plans`);
            const result = await response.json();

            if (result.success) {
                this.renderMembershipPlans(result.plans);
            } else {
                console.error('加载会员计划失败:', result.error);
            }
        } catch (error) {
            console.error('加载会员计划异常:', error);
        }
    }

    renderMembershipPlans(plans) {
        const plansContainer = document.getElementById('membershipPlans');
        if (!plansContainer) return;

        plansContainer.innerHTML = '';

        Object.entries(plans).forEach(([planId, planInfo]) => {
            const planCard = document.createElement('div');
            planCard.className = 'plan-card';
            planCard.innerHTML = `
                <div class="plan-header">
                    <h3>${planInfo.name}</h3>
                    <div class="price">
                        <span class="currency">¥</span>
                        <span class="amount">${planInfo.price_yuan}</span>
                        <span class="period">${planId === 'buyout' ? '/ 终身授权' : '/ 免费试用'}</span>
                    </div>
                </div>
                <div class="plan-features">
                    <ul>
                        ${planInfo.features.map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                </div>
                <button class="upgrade-btn" data-plan="${planId}" onclick="if(window.paymentManager) { window.paymentManager.showUpgradeModal('${planId}'); } else { console.error('PaymentManager未初始化'); }">
                    立即升级
                </button>
            `;
            plansContainer.appendChild(planCard);
        });

        // 重新绑定升级按钮事件（因为按钮是动态生成的）
        this.bindUpgradeButtons();
    }

    bindUpgradeButtons() {
        // 绑定升级按钮事件
        document.querySelectorAll('.upgrade-btn').forEach(btn => {
            // 先移除可能存在的旧监听器（通过克隆节点）
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);

            // 绑定新的事件
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const plan = newBtn.dataset.plan || newBtn.getAttribute('data-plan');
                if (plan) {
                    console.log('点击升级按钮，计划:', plan);
                    this.showUpgradeModal(plan);
                } else {
                    console.error('升级按钮缺少 plan 属性');
                }
            });
        });
    }

    showUpgradeModal(plan) {
        console.log('显示升级模态框，计划:', plan);
        this.currentPlan = plan;

        // 清除之前的错误消息（用户已选择会员计划）
        this.clearMessages();

        const modal = document.getElementById('upgradeModal');
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            this.loadPlanDetails(plan);
        } else {
            console.error('未找到升级模态框元素');
        }
    }

    closePaymentModal() {
        // 关闭所有支付相关模态框
        const modals = ['upgradeModal', 'qrPaymentModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'none';
            }
        });

        document.body.style.overflow = 'auto';

        // 重置状态
        this.currentPlan = null;
        this.currentBillingPeriod = 'monthly';
        this.currentPaymentMethod = null;
        this.orderData = null;

        // 重置支付方式选择
        document.querySelectorAll('.payment-method').forEach(el => {
            el.classList.remove('selected');
        });

        // 重置月付/年付选择
        const monthlyBtn = document.getElementById('monthlyBtn');
        const yearlyBtn = document.getElementById('yearlyBtn');
        if (monthlyBtn && yearlyBtn) {
            monthlyBtn.classList.add('active');
            monthlyBtn.style.background = 'white';
            monthlyBtn.style.color = '#333';
            yearlyBtn.classList.remove('active');
            yearlyBtn.style.background = 'transparent';
            yearlyBtn.style.color = '#666';
        }

        // 隐藏支付表单
        const alipayForm = document.getElementById('alipayForm');
        const wechatForm = document.getElementById('wechatForm');
        if (alipayForm) alipayForm.style.display = 'none';
        if (wechatForm) wechatForm.style.display = 'none';
    }

    async loadPlanDetails(plan) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/payment/plans`);
            const result = await response.json();

            if (result.success && result.plans[plan]) {
                const planInfo = result.plans[plan];
                this.renderPlanDetails(planInfo);
            }
        } catch (error) {
            console.error('加载计划详情失败:', error);
        }
    }

    renderPlanDetails(planInfo) {
        const planNameEl = document.getElementById('selectedPlanName');
        const planPriceEl = document.getElementById('selectedPlanPrice');
        const planFeaturesEl = document.getElementById('selectedPlanFeatures');
        const yearlySavingsEl = document.getElementById('yearlySavings');

        if (planNameEl) planNameEl.textContent = planInfo.name;

        // 针对 buyout 计划隐藏周期选择，显示终身文字
        if (planInfo.id === 'buyout') {
            const periodText = document.querySelector('.period');
            if (periodText) periodText.textContent = '/ 终身授权';

            const billingOptions = document.querySelector('.billing-options');
            if (billingOptions) billingOptions.style.display = 'none';
        } else {
            // 非 buyout 计划，确保周期选择可见
            const billingOptions = document.querySelector('.billing-options');
            if (billingOptions) billingOptions.style.display = 'flex'; // 或者 'block'，取决于你的布局
        }

        // 根据当前选择的计费周期显示价格
        this.updatePriceDisplay(planInfo);

        if (planFeaturesEl) {
            planFeaturesEl.innerHTML = planInfo.features
                .map(feature => `<li><i class="fas fa-check"></i>${feature}</li>`)
                .join('');
        }
    }

    selectBillingPeriod(period) {
        this.currentBillingPeriod = period;

        // 更新按钮样式
        const monthlyBtn = document.getElementById('monthlyBtn');
        const yearlyBtn = document.getElementById('yearlyBtn');

        if (monthlyBtn && yearlyBtn) {
            if (period === 'monthly') {
                monthlyBtn.classList.add('active');
                monthlyBtn.style.background = 'white';
                monthlyBtn.style.color = '#333';
                yearlyBtn.classList.remove('active');
                yearlyBtn.style.background = 'transparent';
                yearlyBtn.style.color = '#666';
            } else {
                yearlyBtn.classList.add('active');
                yearlyBtn.style.background = 'white';
                yearlyBtn.style.color = '#333';
                monthlyBtn.classList.remove('active');
                monthlyBtn.style.background = 'transparent';
                monthlyBtn.style.color = '#666';
            }
        }

        // 更新价格显示
        if (this.currentPlan) {
            // 重新加载计划详情以更新价格
            this.loadPlanDetails(this.currentPlan);
        }
    }

    updatePriceDisplay(planInfo) {
        const planPriceEl = document.getElementById('selectedPlanPrice');
        const yearlySavingsEl = document.getElementById('yearlySavings');

        if (!planPriceEl) return;

        if (this.currentBillingPeriod === 'yearly' && planInfo.price_yearly > 0) {
            // 年付价格
            const monthlyPrice = planInfo.price_monthly;
            const yearlyPrice = planInfo.price_yearly;
            const monthlyAvg = Math.round(yearlyPrice / 12 * 10) / 10;
            const savings = (monthlyPrice * 12) - yearlyPrice;
            const discountRate = Math.round((savings / (monthlyPrice * 12)) * 100);

            planPriceEl.innerHTML = `
                <span style="font-size: 2rem; color: #667eea; font-weight: bold;">¥${yearlyPrice}</span>
                <span style="font-size: 1rem; color: #666;">/年</span>
                <div style="font-size: 0.9rem; color: #999; margin-top: 5px;">
                    相当于 ¥${monthlyAvg}/月
                </div>
            `;

            if (yearlySavingsEl && savings > 0) {
                yearlySavingsEl.style.display = 'block';
                yearlySavingsEl.innerHTML = `💰 节省 ¥${savings}/年（${discountRate}%折扣）`;
            }
        } else {
            // 月付价格
            planPriceEl.innerHTML = `
                <span style="font-size: 2rem; color: #667eea; font-weight: bold;">¥${planInfo.price_monthly}</span>
                <span style="font-size: 1rem; color: #666;">/月</span>
            `;

            if (yearlySavingsEl) {
                yearlySavingsEl.style.display = 'none';
            }
        }
    }

    selectPaymentMethod(method) {
        this.currentPaymentMethod = method;
        console.log('选择支付方式:', method);

        // 清除之前的错误消息（用户已选择支付方式）
        this.clearMessages();

        // 更新UI
        document.querySelectorAll('.method-card').forEach(el => {
            el.classList.remove('selected');
        });

        const selectedMethod = document.querySelector(`.method-card[data-method="${method}"]`);
        if (selectedMethod) {
            selectedMethod.classList.add('selected');
        }

        // 显示对应的支付表单
        this.showPaymentForm(method);

        // 处理 PayPal 逻辑
        const paypalInfo = document.getElementById('paypalInfo');
        const confirmBtn = document.getElementById('confirmPaymentBtn');

        if (method === 'paypal') {
            if (paypalInfo) paypalInfo.style.display = 'block';
            if (confirmBtn) {
                confirmBtn.innerHTML = '<i class="fab fa-paypal"></i> Pay with PayPal';
                confirmBtn.style.background = '#0070ba';
                confirmBtn.style.color = 'white';
            }
        } else {
            if (paypalInfo) paypalInfo.style.display = 'none';
            if (confirmBtn) {
                confirmBtn.innerHTML = '立即支付';
                confirmBtn.style.background = ''; // 恢复 CSS 原样
                confirmBtn.style.color = '';
            }
        }
    }

    showPaymentForm(method) {
        const alipayForm = document.getElementById('alipayForm');
        const wechatForm = document.getElementById('wechatForm');

        if (method === 'alipay_qrcode') {
            if (alipayForm) alipayForm.style.display = 'block';
            if (wechatForm) wechatForm.style.display = 'none';
        } else if (method === 'wechat_qrcode') {
            if (alipayForm) alipayForm.style.display = 'none';
            if (wechatForm) wechatForm.style.display = 'block';
        } else {
            if (alipayForm) alipayForm.style.display = 'none';
            if (wechatForm) wechatForm.style.display = 'none';
        }
    }

    setupPaymentForms() {
        // 设置支付表单验证
        const paymentForm = document.getElementById('paymentForm');
        if (paymentForm) {
            paymentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.processPayment();
            });
        }
    }

    async confirmPayment() {
        // 清除之前的错误消息
        this.clearMessages();

        if (!this.currentPlan || !this.currentPaymentMethod) {
            this.showMessage('请选择会员计划和支付方式', 'error');
            console.error('确认支付失败 - currentPlan:', this.currentPlan, 'currentPaymentMethod:', this.currentPaymentMethod);
            return;
        }

        // 特殊处理 PayPal：直接跳转收款页面
        if (this.currentPaymentMethod === 'paypal') {
            const PAYPAL_LINK = "https://www.paypal.me/baifan7575/28";
            this.showMessage('正在跳转至 PayPal 支付安全页面...', 'success');
            setTimeout(() => {
                window.open(PAYPAL_LINK, '_blank');
            }, 1000);
            return;
        }

        console.log('确认支付 - currentPlan:', this.currentPlan, 'currentPaymentMethod:', this.currentPaymentMethod);

        try {
            // 获取用户token（使用authManager）
            let token = null;
            if (window.authManager) {
                token = window.authManager.getToken();
            } else {
                // 使用auth_token作为key，与auth.js保持一致
                token = localStorage.getItem('auth_token');
            }

            if (!token) {
                this.showMessage('请先登录', 'error');
                window.location.href = 'index.html';
                return;
            }

            // 获取用户ID
            let userId = null;
            if (window.authManager && window.authManager.getUser) {
                const user = window.authManager.getUser();
                userId = user ? user.id : null;
            }

            if (!userId) {
                userId = this.getUserIdFromToken(token);
            }

            // 创建订单
            const orderData = {
                plan: this.currentPlan,
                billing_period: this.currentBillingPeriod,  // monthly 或 yearly
                payment_method: this.currentPaymentMethod,
                device_info: {
                    user_agent: navigator.userAgent,
                    screen_resolution: `${screen.width}x${screen.height}`,
                    language: navigator.language
                }
            };

            const response = await fetch(`${this.apiBaseUrl}/api/payment/create-order`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(orderData)
            });

            if (response.status === 401) {
                this.showMessage('登录已过期，请重新登录', 'error');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 2000);
                return;
            }

            const result = await response.json();

            if (result.success) {
                this.orderData = result.order;
                this.showMessage(`✅ 订单创建成功！订单号: ${result.order.order_no}`, 'success');

                // 显示支付信息
                if (result.payment_info) {
                    this.showPaymentInfo(result.payment_info);
                } else {
                    // 如果没有支付信息，说明支付网关未接入，显示提示
                    this.showMessage(
                        '💡 支付接口已就绪，等待接入支付宝/微信支付网关。\n\n' +
                        '订单已创建，请联系管理员完成支付。',
                        'info'
                    );
                }
            } else {
                this.showMessage(result.error || '创建订单失败', 'error');
            }

        } catch (error) {
            console.error('确认支付失败:', error);
            this.showMessage('支付处理失败: ' + error.message, 'error');
        }
    }

    showPaymentInfo(paymentInfo) {
        // 显示支付信息
        const paymentStatus = document.getElementById('paymentStatus');
        if (paymentStatus) {
            paymentStatus.style.display = 'block';

            // 隐藏支付方式选择和确认按钮，防止重复提交
            const paymentMethodsDiv = document.querySelector('.payment-methods');
            const actionsDiv = document.querySelector('.actions');
            if (paymentMethodsDiv) paymentMethodsDiv.style.display = 'none';
            if (actionsDiv) actionsDiv.style.display = 'none';

            // 如果是收款码支付
            if (paymentInfo.type === 'qrcode') {
                const qrcodeTypeName = paymentInfo.qrcode_type === 'alipay' ? '支付宝' : '微信';
                paymentStatus.innerHTML = `
                    <div class="payment-qrcode-container" style="padding: 30px; background: var(--bg-card); border: 1px solid var(--glass-border); border-radius: 24px; margin-top: 25px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                        <h4 style="margin-bottom: 20px; color: var(--accent-gold); font-size: 1.2rem; font-weight: 600;">
                            <i class="fas fa-qrcode" style="margin-right: 8px;"></i>
                            请使用${qrcodeTypeName}扫码支付
                        </h4>
                        <div style="margin: 25px 0; display: inline-block; padding: 15px; background: white; border-radius: 16px; box-shadow: 0 0 20px rgba(255,255,255,0.1);">
                            <img src="${this.apiBaseUrl}${paymentInfo.qrcode_url}" 
                                 alt="${qrcodeTypeName}收款码" 
                                 style="width: 200px; height: 200px; display: block;">
                        </div>
                        <div style="line-height: 1.8; color: var(--text-secondary); margin-top: 15px; font-size: 0.95rem; text-align: left; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px; display: inline-block; width: 100%; max-width: 320px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span>订单号</span>
                                <span style="color: var(--text-primary); font-family: monospace;">${paymentInfo.order_no}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span>金额</span>
                                <span style="color: var(--accent-gold); font-weight: bold; font-size: 1.1rem;">¥${paymentInfo.amount}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>会员计划</span>
                                <span style="color: var(--text-primary);">${paymentInfo.plan_name}</span>
                            </div>
                        </div>
                        <p style="margin-top: 20px; color: var(--accent-blue); font-size: 0.9rem;">
                            <i class="fas fa-info-circle" style="margin-right: 5px;"></i>
                            ${paymentInfo.message || '请扫码支付，支付完成后点击下方按钮'}
                        </p>
                        <div style="margin-top: 25px;">
                            <button onclick="window.paymentManager.markAsPaid('${paymentInfo.order_no}')" 
                                    class="btn-gold"
                                    style="padding: 12px 30px; border-radius: 50px; font-size: 1rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; min-width: 200px; box-shadow: 0 5px 15px rgba(251, 191, 36, 0.3); transition: transform 0.2s;">
                                <i class="fas fa-check-circle" style="margin-right: 8px;"></i>
                                我已支付，等待确认
                            </button>
                        </div>
                        <div id="payment-waiting-status" style="margin-top: 15px; display: none; color: var(--accent-blue); font-size: 0.9rem;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                                <i class="fas fa-spinner fa-spin"></i>
                                <span>等待管理员确认中...</span>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                // 其他支付方式（原有逻辑）
                paymentStatus.innerHTML = `
                    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; margin-top: 20px;">
                        <h4 style="margin-bottom: 15px; color: #333;">支付信息</h4>
                        <div style="line-height: 1.8; color: #666;">
                            <p><strong>订单号：</strong>${paymentInfo.order_no}</p>
                            <p><strong>金额：</strong>¥${paymentInfo.amount}</p>
                            <p><strong>会员计划：</strong>${paymentInfo.plan_name}</p>
                            <p><strong>支付方式：</strong>${paymentInfo.payment_method === 'alipay' ? '支付宝' : '微信支付'}</p>
                            <p style="margin-top: 15px; color: #667eea; font-weight: bold;">${paymentInfo.message || '等待接入支付网关'}</p>
                        </div>
                    </div>
                `;
            }
        }
    }

    async markAsPaid(orderNo) {
        const waitingStatus = document.getElementById('payment-waiting-status');
        const payBtn = document.querySelector('button[onclick*="markAsPaid"]');

        if (waitingStatus) {
            waitingStatus.style.display = 'block';
        }

        if (payBtn) {
            payBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> 已提交，等待确认...';
            payBtn.disabled = true;
            payBtn.style.opacity = '0.7';
            payBtn.style.cursor = 'not-allowed';
        }

        // 通知后端用户已支付
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/payment/mark-paid`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_no: orderNo
                })
            });

            const result = await response.json();
            if (result.success) {
                console.log('✅ 已通知后端用户已支付');
                // 开始轮询订单状态
                this.startPollingOrderStatus(orderNo);
            }
        } catch (error) {
            console.error('通知后端失败:', error);
            // 即使通知失败，也不影响后续流程
        }

        this.showMessage('已提交，等待管理员确认。通常1-2小时内完成确认。', 'info');

        // 可以定期查询订单状态
        this.startOrderStatusCheck(orderNo);
    }

    startOrderStatusCheck(orderNo) {
        // 每5秒查询一次订单状态（缩短间隔，更快响应）
        let checkCount = 0;
        const maxChecks = 120; // 最多查询120次（10分钟）

        // 如果已经检测到paid状态，停止查询
        if (this.orderStatusCheckInterval) {
            clearInterval(this.orderStatusCheckInterval);
        }

        this.orderStatusCheckInterval = setInterval(async () => {
            try {
                checkCount++;

                // 获取token（从authManager获取）
                const token = window.authManager ? window.authManager.getToken() : null;
                const headers = {
                    'Content-Type': 'application/json'
                };
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }

                const response = await fetch(`${this.apiBaseUrl}/api/payment/query-order/${orderNo}`, {
                    headers: headers
                });

                const result = await response.json();

                console.log(`[订单状态查询 ${checkCount}] 订单状态:`, result.order?.status);

                if (result.success && result.order && result.order.status === 'paid') {
                    clearInterval(this.orderStatusCheckInterval);
                    this.orderStatusCheckInterval = null;
                    console.log('✅ 订单已确认，开始刷新用户信息...');

                    // 显示成功消息（使用alert确保用户看到）
                    alert('✅ 支付已确认！会员已开通！正在刷新信息...');
                    this.showMessage('✅ 支付已确认！会员已开通！正在刷新信息...', 'success');

                    // 刷新用户信息
                    if (window.appManager && window.appManager.authManager) {
                        try {
                            // 重新加载用户信息（这会更新会员等级）
                            await window.appManager.authManager.loadUserUsageStats();
                            console.log('✅ 用户信息已刷新');

                            // 刷新页面显示
                            if (window.appManager.loadUsageStats) {
                                await window.appManager.loadUsageStats();
                                console.log('✅ 使用统计已刷新');
                            }

                            // 更新UI显示
                            if (window.appManager.updateUIForLoggedInUser) {
                                window.appManager.updateUIForLoggedInUser();
                                console.log('✅ UI已更新');
                            }

                            // 显示最终成功消息和返回主页按钮
                            alert('✅ 会员已开通！页面已更新！');
                            this.showMessage('✅ 会员已开通！页面已更新！', 'success');

                            // 显示返回主页按钮
                            this.showBackToHomeButton();

                        } catch (error) {
                            console.error('刷新用户信息失败:', error);
                            // 即使刷新失败，也显示返回主页按钮
                            alert('✅ 会员已开通！');
                            this.showBackToHomeButton();
                        }
                    } else {
                        // 如果没有appManager，显示返回主页按钮
                        alert('✅ 会员已开通！');
                        this.showBackToHomeButton();
                    }
                } else if (checkCount >= maxChecks) {
                    // 达到最大查询次数，停止查询
                    clearInterval(this.orderStatusCheckInterval);
                    this.orderStatusCheckInterval = null;
                    console.log('⚠️ 订单状态查询超时，请手动刷新页面');
                    this.showMessage('⚠️ 订单状态查询超时，请手动刷新页面查看会员状态', 'warning');
                }
            } catch (error) {
                console.error('查询订单状态失败:', error);
                if (checkCount >= maxChecks) {
                    clearInterval(this.orderStatusCheckInterval);
                    this.orderStatusCheckInterval = null;
                }
            }
        }, 5000); // 5秒查询一次（更快响应）
    }

    processPayment(paymentInfo) {
        if (this.currentPaymentMethod === 'alipay') {
            this.processAlipayPayment(paymentInfo);
        } else if (this.currentPaymentMethod === 'wechat') {
            this.processWechatPayment(paymentInfo);
        }
    }

    processAlipayPayment(paymentInfo) {
        // 支付宝支付处理
        if (paymentInfo.pay_url) {
            // 跳转到支付宝支付页面
            window.open(paymentInfo.pay_url, '_blank');
            this.showPaymentStatus('waiting');
            this.startPaymentStatusCheck();
        } else if (paymentInfo.qr_code) {
            // 显示二维码支付
            this.showQRCode(paymentInfo.qr_code, 'alipay');
        }
    }

    processWechatPayment(paymentInfo) {
        // 微信支付处理
        if (paymentInfo.code_url) {
            // 显示二维码支付
            this.showQRCode(paymentInfo.code_url, 'wechat');
        } else if (paymentInfo.prepay_id) {
            // JSAPI支付（微信内浏览器）
            this.processWechatJSAPI(paymentInfo);
        }
    }

    showQRCode(codeUrl, paymentType) {
        const qrModal = document.getElementById('qrPaymentModal');
        const qrContainer = document.getElementById('qrCodeContainer');

        if (qrModal && qrContainer) {
            // 生成二维码
            qrContainer.innerHTML = '';
            const qrImage = document.createElement('img');
            qrImage.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(codeUrl)}`;
            qrImage.alt = `${paymentType === 'alipay' ? '支付宝' : '微信'}支付二维码`;
            qrContainer.appendChild(qrImage);

            // 显示支付说明
            const paymentInfo = document.getElementById('paymentInfo');
            if (paymentInfo) {
                paymentInfo.innerHTML = `
                    <p>请使用${paymentType === 'alipay' ? '支付宝' : '微信'}扫描二维码完成支付</p>
                    <p>订单号: ${this.orderData.order_no}</p>
                    <p>金额: ¥${(this.orderData.amount / 100).toFixed(2)}</p>
                `;
            }

            qrModal.style.display = 'block';
            this.startPaymentStatusCheck();
        }
    }

    processWechatJSAPI(paymentInfo) {
        // 微信JSAPI支付（需要在微信浏览器中使用）
        if (typeof WeixinJSBridge !== 'undefined') {
            WeixinJSBridge.invoke('getBrandWCPayRequest', {
                appId: paymentInfo.appId,
                timeStamp: paymentInfo.timeStamp,
                nonceStr: paymentInfo.nonceStr,
                package: `prepay_id=${paymentInfo.prepay_id}`,
                signType: paymentInfo.signType,
                paySign: paymentInfo.paySign
            }, (res) => {
                if (res.err_msg === 'get_brand_wcpay_request:ok') {
                    this.onPaymentSuccess();
                } else {
                    this.onPaymentFailed(res.err_msg);
                }
            });
        } else {
            this.showMessage('请在微信浏览器中使用此功能', 'error');
        }
    }

    startPaymentStatusCheck() {
        // 开始检查支付状态
        const checkInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBaseUrl}/api/payment/query-order/${this.orderData.order_no}`);
                const result = await response.json();

                if (result.success && result.order.status === 'paid') {
                    clearInterval(checkInterval);
                    this.onPaymentSuccess();
                }
            } catch (error) {
                console.error('检查支付状态失败:', error);
            }
        }, 3000); // 每3秒检查一次

        // 设置超时检查（5分钟）
        setTimeout(() => {
            clearInterval(checkInterval);
            this.showPaymentTimeout();
        }, 5 * 60 * 1000);
    }

    async onPaymentSuccess() {
        // 如果是模拟支付，需要手动激活会员
        if (this.orderData && this.orderData.status === 'pending') {
            try {
                // 获取用户token
                let token = null;
                if (window.authManager) {
                    token = window.authManager.getToken();
                } else {
                    // 使用auth_token作为key，与auth.js保持一致
                    token = localStorage.getItem('auth_token');
                }

                if (token) {
                    // 调用激活会员API
                    const response = await fetch(`${this.apiBaseUrl}/api/payment/activate-membership`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            order_no: this.orderData.order_no,
                            plan: this.orderData.plan,
                            billing_period: this.orderData.billing_period || 'monthly'
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        this.showMessage('支付成功！会员权益已激活', 'success');
                    } else {
                        this.showMessage('支付成功，但激活会员失败: ' + (result.error || '未知错误'), 'error');
                    }
                } else {
                    this.showMessage('支付成功，但需要登录才能激活会员', 'error');
                }
            } catch (error) {
                console.error('激活会员失败:', error);
                this.showMessage('支付成功，但激活会员失败: ' + error.message, 'error');
            }
        } else {
            this.showMessage('支付成功！会员权益已激活', 'success');
        }

        this.closePaymentModal();

        // 刷新用户信息
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }

    onPaymentFailed(error) {
        this.showMessage(`支付失败: ${error}`, 'error');
        this.showPaymentStatus('failed');
    }

    showPaymentTimeout() {
        this.showMessage('支付超时，请重试', 'error');
        this.showPaymentStatus('timeout');
    }

    showPaymentStatus(status) {
        const statusEl = document.getElementById('paymentStatus');
        if (statusEl) {
            const statusMessages = {
                'waiting': '等待支付中...',
                'success': '支付成功！',
                'failed': '支付失败',
                'timeout': '支付超时'
            };

            statusEl.textContent = statusMessages[status] || '';
            statusEl.className = `payment-status ${status}`;
        }
    }

    getUserIdFromToken(token) {
        // 从token中提取用户ID（我们的token格式是 mock_token_xxxxx）
        if (token && token.startsWith('mock_token_')) {
            // 从token中提取用户ID的前8位，然后需要从后端获取完整ID
            // 这里先返回null，让后端通过token验证来获取用户ID
            return null;
        }
        // 生产环境需要解析JWT
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub || payload.user_id || payload.id;
        } catch (error) {
            console.error('解析token失败:', error);
            return null;
        }
    }

    clearMessages() {
        // 清除所有消息
        const messageContainer = document.getElementById('messageContainer');
        if (messageContainer) {
            messageContainer.innerHTML = '';
        }
    }

    showMessage(message, type = 'info') {
        // 显示消息提示
        const messageContainer = document.getElementById('messageContainer');
        if (messageContainer) {
            // 如果是错误消息，先清除所有消息
            if (type === 'error') {
                this.clearMessages();
            }

            const messageEl = document.createElement('div');
            messageEl.className = `message ${type}`;
            messageEl.textContent = message;

            messageContainer.appendChild(messageEl);

            // 3秒后自动消失
            setTimeout(() => {
                messageEl.remove();
            }, 3000);
        } else {
            // 回退到alert
            alert(message);
        }
    }

    showBackToHomeButton() {
        // 移除之前的返回主页按钮（如果存在）
        const existingBtn = document.getElementById('back-to-home-btn');
        if (existingBtn) {
            existingBtn.remove();
        }

        // 创建返回主页按钮
        const backBtn = document.createElement('div');
        backBtn.id = 'back-to-home-btn';
        backBtn.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
            animation: slideUp 0.5s ease-out;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        backBtn.innerHTML = '<i class="fas fa-home"></i> 返回主页使用工具';
        backBtn.onclick = () => {
            window.location.href = '/';
        };
        backBtn.onmouseenter = () => {
            backBtn.style.transform = 'translateY(-3px)';
            backBtn.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
        };
        backBtn.onmouseleave = () => {
            backBtn.style.transform = 'translateY(0)';
            backBtn.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
        };

        // 添加动画样式
        if (!document.getElementById('back-to-home-style')) {
            const style = document.createElement('style');
            style.id = 'back-to-home-style';
            style.textContent = `
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // 添加到页面
        document.body.appendChild(backBtn);

        console.log('✅ 返回主页按钮已显示');
    }
}

// 初始化支付管理器
document.addEventListener('DOMContentLoaded', () => {
    window.paymentManager = new PaymentManager();
});