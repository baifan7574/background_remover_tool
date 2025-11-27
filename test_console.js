// 测试脚本：验证背景移除工具按钮多次点击
console.log('=== 开始测试背景移除工具按钮 ===');

// 等待页面加载完成
setTimeout(() => {
    // 查找背景移除工具按钮
    const bgRemoverBtn = document.querySelector('button[data-tool="background-remover"]');
    
    if (!bgRemoverBtn) {
        console.error('未找到背景移除工具按钮');
        return;
    }
    
    console.log('找到背景移除工具按钮:', bgRemoverBtn);
    
    // 测试第一次点击
    console.log('第一次点击...');
    bgRemoverBtn.click();
    
    // 等待模态框打开
    setTimeout(() => {
        const modal = document.getElementById('toolModal');
        if (modal && modal.style.display === 'flex') {
            console.log('✓ 第一次点击成功，模态框已打开');
            
            // 关闭模态框
            const closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.click();
                console.log('关闭模态框');
            }
            
            // 等待关闭后测试第二次点击
            setTimeout(() => {
                console.log('第二次点击...');
                bgRemoverBtn.click();
                
                setTimeout(() => {
                    if (modal && modal.style.display === 'flex') {
                        console.log('✓ 第二次点击成功，模态框已打开');
                        console.log('✅ 测试通过：背景移除工具可以多次使用');
                        
                        // 关闭模态框
                        const closeBtn2 = modal.querySelector('.modal-close');
                        if (closeBtn2) {
                            closeBtn2.click();
                        }
                    } else {
                        console.error('✗ 第二次点击失败，模态框未打开');
                    }
                }, 500);
            }, 500);
        } else {
            console.error('✗ 第一次点击失败，模态框未打开');
        }
    }, 500);
    
}, 2000);

// 监听模态框状态变化
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
            const modal = mutation.target;
            if (modal.id === 'toolModal') {
                console.log('模态框状态变化:', modal.style.display);
            }
        }
    });
});

// 开始观察模态框
const modal = document.getElementById('toolModal');
if (modal) {
    observer.observe(modal, { attributes: true });
}