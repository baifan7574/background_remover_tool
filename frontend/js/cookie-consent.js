/**
 * Cookie同意管理 - 支持Google Consent Mode v2
 * 符合GDPR和电子隐私法规要求
 */

class CookieConsent {
    constructor() {
        this.storageKey = 'cookie_consent';
        this.consentExpiryDays = 365; // Cookie同意有效期1年
        this.init();
    }

    init() {
        // 检查是否已经同意过
        const savedConsent = this.getSavedConsent();
        
        if (!savedConsent) {
            // 首次访问，显示同意横幅
            this.showConsentBanner();
        } else {
            // 已同意过，直接应用设置
            this.applyConsent(savedConsent);
        }

        // 初始化Google Consent Mode v2
        this.initGoogleConsentMode();
    }

    /**
     * 初始化Google Consent Mode v2
     */
    initGoogleConsentMode() {
        // 在页面加载时立即设置默认状态（拒绝所有）
        window.dataLayer = window.dataLayer || [];
        
        function gtag() {
            dataLayer.push(arguments);
        }

        // 设置默认状态为拒绝（符合GDPR要求）
        gtag('consent', 'default', {
            'ad_storage': 'denied',
            'ad_user_data': 'denied',
            'ad_personalization': 'denied',
            'analytics_storage': 'denied',
            'functionality_storage': 'denied',
            'personalization_storage': 'denied',
            'security_storage': 'granted', // 安全Cookie始终允许
            'wait_for_update': 500
        });

        // 如果有保存的同意设置，应用它
        const savedConsent = this.getSavedConsent();
        if (savedConsent) {
            this.updateGoogleConsent(savedConsent);
        }
    }

    /**
     * 更新Google Consent Mode设置
     */
    updateGoogleConsent(consent) {
        if (typeof gtag === 'undefined') {
            // 如果gtag未加载，先定义它
            window.dataLayer = window.dataLayer || [];
            function gtag() {
                dataLayer.push(arguments);
            }
            window.gtag = gtag;
        }

        gtag('consent', 'update', {
            'ad_storage': consent.advertising ? 'granted' : 'denied',
            'ad_user_data': consent.advertising ? 'granted' : 'denied',
            'ad_personalization': consent.advertising ? 'granted' : 'denied',
            'analytics_storage': consent.analytics ? 'granted' : 'denied',
            'functionality_storage': consent.functional ? 'granted' : 'denied',
            'personalization_storage': consent.functional ? 'granted' : 'denied',
            'security_storage': 'granted' // 安全Cookie始终允许
        });
    }

    /**
     * 显示Cookie同意横幅
     */
    showConsentBanner() {
        // 创建横幅HTML
        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-consent-content">
                <div class="cookie-consent-text">
                    <h3>🍪 Cookie使用说明</h3>
                    <p>我们使用Cookie来改善您的浏览体验、分析网站流量，并为您提供个性化内容。点击"接受全部"即表示您同意我们使用所有Cookie。您也可以选择"自定义"来管理您的偏好设置。</p>
                    <p class="cookie-consent-links">
                        <a href="cookie.html" target="_blank">了解更多</a> | 
                        <a href="privacy.html" target="_blank">隐私政策</a>
                    </p>
                </div>
                <div class="cookie-consent-buttons">
                    <button class="cookie-btn cookie-btn-accept-all" id="acceptAllBtn">接受全部</button>
                    <button class="cookie-btn cookie-btn-custom" id="customBtn">自定义</button>
                    <button class="cookie-btn cookie-btn-reject" id="rejectBtn">拒绝</button>
                </div>
            </div>
        `;
        document.body.appendChild(banner);

        // 绑定事件
        document.getElementById('acceptAllBtn').addEventListener('click', () => {
            this.acceptAll();
        });

        document.getElementById('rejectBtn').addEventListener('click', () => {
            this.rejectAll();
        });

        document.getElementById('customBtn').addEventListener('click', () => {
            this.showCustomSettings();
        });
    }

    /**
     * 显示自定义设置面板
     */
    showCustomSettings() {
        // 如果设置面板已存在，先移除
        const existingPanel = document.getElementById('cookie-settings-panel');
        if (existingPanel) {
            existingPanel.remove();
        }

        // 隐藏横幅
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.style.display = 'none';
        }

        // 获取当前保存的设置（如果有）
        const savedConsent = this.getSavedConsent();
        const currentConsent = savedConsent || {
            necessary: true,
            functional: false,
            analytics: false,
            advertising: false
        };

        // 创建自定义设置面板
        const settingsPanel = document.createElement('div');
        settingsPanel.id = 'cookie-settings-panel';
        settingsPanel.innerHTML = `
            <div class="cookie-settings-content">
                <div class="cookie-settings-header">
                    <h3>🍪 Cookie偏好设置</h3>
                    <button class="cookie-settings-close" id="closeSettingsBtn">&times;</button>
                </div>
                <div class="cookie-settings-body">
                    <p class="cookie-settings-description">
                        选择您希望允许的Cookie类型。严格必要的Cookie无法禁用，因为它们是网站正常运行所必需的。
                    </p>
                    
                    <div class="cookie-setting-item">
                        <div class="cookie-setting-info">
                            <h4>严格必要的Cookie</h4>
                            <p>这些Cookie对于网站的正常运行是必需的，无法禁用。</p>
                        </div>
                        <label class="cookie-toggle">
                            <input type="checkbox" checked disabled>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>

                    <div class="cookie-setting-item">
                        <div class="cookie-setting-info">
                            <h4>功能Cookie</h4>
                            <p>用于记住您的偏好设置，如语言选择、主题设置等。</p>
                        </div>
                        <label class="cookie-toggle">
                            <input type="checkbox" id="functionalCookie" ${currentConsent.functional ? 'checked' : ''}>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>

                    <div class="cookie-setting-item">
                        <div class="cookie-setting-info">
                            <h4>分析Cookie</h4>
                            <p>帮助我们了解访问者如何与网站互动，用于改进网站功能。</p>
                        </div>
                        <label class="cookie-toggle">
                            <input type="checkbox" id="analyticsCookie" ${currentConsent.analytics ? 'checked' : ''}>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>

                    <div class="cookie-setting-item">
                        <div class="cookie-setting-info">
                            <h4>广告Cookie</h4>
                            <p>用于向您展示相关广告，并衡量广告活动的有效性。</p>
                        </div>
                        <label class="cookie-toggle">
                            <input type="checkbox" id="advertisingCookie" ${currentConsent.advertising ? 'checked' : ''}>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>

                    <div class="cookie-settings-actions">
                        <button class="cookie-btn cookie-btn-save" id="saveSettingsBtn">保存设置</button>
                        <button class="cookie-btn cookie-btn-cancel" id="cancelSettingsBtn">取消</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(settingsPanel);

        // 绑定事件
        document.getElementById('saveSettingsBtn').addEventListener('click', () => {
            this.saveCustomSettings();
        });

        document.getElementById('cancelSettingsBtn').addEventListener('click', () => {
            this.closeSettingsPanel();
        });

        document.getElementById('closeSettingsBtn').addEventListener('click', () => {
            this.closeSettingsPanel();
        });
    }

    /**
     * 保存自定义设置
     */
    saveCustomSettings() {
        const consent = {
            necessary: true, // 始终为true
            functional: document.getElementById('functionalCookie').checked,
            analytics: document.getElementById('analyticsCookie').checked,
            advertising: document.getElementById('advertisingCookie').checked,
            timestamp: new Date().toISOString()
        };

        this.saveConsent(consent);
        this.applyConsent(consent);
        this.closeSettingsPanel();
    }

    /**
     * 关闭设置面板
     */
    closeSettingsPanel() {
        const panel = document.getElementById('cookie-settings-panel');
        if (panel) {
            panel.remove();
        }
        
        // 如果用户还没有同意过，重新显示横幅
        const savedConsent = this.getSavedConsent();
        if (!savedConsent) {
            const banner = document.getElementById('cookie-consent-banner');
            if (banner) {
                banner.style.display = 'block';
            }
        }
    }

    /**
     * 接受所有Cookie
     */
    acceptAll() {
        const consent = {
            necessary: true,
            functional: true,
            analytics: true,
            advertising: true,
            timestamp: new Date().toISOString()
        };

        this.saveConsent(consent);
        this.applyConsent(consent);
        this.hideBanner();
    }

    /**
     * 拒绝所有非必要Cookie
     */
    rejectAll() {
        const consent = {
            necessary: true, // 严格必要的Cookie始终允许
            functional: false,
            analytics: false,
            advertising: false,
            timestamp: new Date().toISOString()
        };

        this.saveConsent(consent);
        this.applyConsent(consent);
        this.hideBanner();
    }

    /**
     * 应用Cookie同意设置
     */
    applyConsent(consent) {
        // 更新Google Consent Mode
        this.updateGoogleConsent(consent);

        // 根据设置启用/禁用相应的功能
        if (consent.analytics) {
            // 如果用户同意分析Cookie，可以在这里初始化Google Analytics
            // 注意：需要确保gtag已加载
            console.log('✅ 分析Cookie已启用');
        }

        if (consent.advertising) {
            // 如果用户同意广告Cookie，可以在这里初始化广告相关功能
            console.log('✅ 广告Cookie已启用');
        }

        if (consent.functional) {
            // 如果用户同意功能Cookie，可以在这里启用相关功能
            console.log('✅ 功能Cookie已启用');
        }
    }

    /**
     * 隐藏横幅
     */
    hideBanner() {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }

    /**
     * 保存同意设置到localStorage
     */
    saveConsent(consent) {
        const expiryDate = new Date();
        expiryDate.setDate(expiryDate.getDate() + this.consentExpiryDays);
        
        const data = {
            consent: consent,
            expiry: expiryDate.toISOString()
        };

        try {
            localStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (e) {
            console.error('保存Cookie同意设置失败:', e);
        }
    }

    /**
     * 获取保存的同意设置
     */
    getSavedConsent() {
        try {
            const data = localStorage.getItem(this.storageKey);
            if (!data) {
                return null;
            }

            const parsed = JSON.parse(data);
            const expiryDate = new Date(parsed.expiry);

            // 检查是否过期
            if (new Date() > expiryDate) {
                localStorage.removeItem(this.storageKey);
                return null;
            }

            return parsed.consent;
        } catch (e) {
            console.error('读取Cookie同意设置失败:', e);
            return null;
        }
    }

    /**
     * 清除保存的同意设置（用于测试或重新显示横幅）
     */
    clearConsent() {
        localStorage.removeItem(this.storageKey);
    }

    /**
     * 显示Cookie设置按钮（用于页脚或设置页面）
     */
    showCookieSettingsButton() {
        // 这个方法可以在页脚或其他地方调用，显示一个"Cookie设置"按钮
        // 用户可以随时修改Cookie偏好
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.cookieConsent = new CookieConsent();
    });
} else {
    window.cookieConsent = new CookieConsent();
}

// 导出供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CookieConsent;
}

