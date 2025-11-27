// 最终验证脚本：确认背景移除工具修复效果
// 在浏览器控制台中运行此脚本

console.log('🔍 开始验证背景移除工具修复效果...');

// 1. 检查HTML中的按钮配置
function checkButtonConfiguration() {
    console.log('\n=== 1. 检查按钮配置 ===');
    
    const bgRemoverBtn = document.querySelector('button[data-tool="background-remover"]');
    
    if (!bgRemoverBtn) {
        console.error('❌ 未找到背景移除工具按钮');
        return false;
    }
    
    console.log('✅ 找到背景移除工具按钮');
    console.log('   - data-tool:', bgRemoverBtn.dataset.tool);
    console.log('   - onclick属性:', bgRemoverBtn.getAttribute('onclick'));
    console.log('   - class:', bgRemoverBtn.className);
    
    // 检查是否移除了onclick属性
    const hasOnclick = bgRemoverBtn.hasAttribute('onclick');
    if (hasOnclick) {
        console.warn('⚠️ 按钮仍然有onclick属性，可能存在双重触发风险');
    } else {
        console.log('✅ 按钮已移除onclick属性，避免双重触发');
    }
    
    return true;
}

// 2. 检查事件监听器
function checkEventListeners() {
    console.log('\n=== 2. 检查事件监听器 ===');
    
    const bgRemoverBtn = document.querySelector('button[data-tool="background-remover"]');
    if (!bgRemoverBtn) return false;
    
    // 检查是否有事件监听器
    const eventListeners = getEventListeners ? getEventListeners(bgRemoverBtn) : null;
    
    if (eventListeners && eventListeners.click) {
        console.log('✅ 按钮有click事件监听器');
        console.log('   - 监听器数量:', eventListeners.click.length);
    } else {
        console.log('ℹ️ 无法检测事件监听器（需要浏览器开发者工具）');
    }
    
    return true;
}

// 3. 测试多次点击功能
async function testMultipleClicks() {
    console.log('\n=== 3. 测试多次点击功能 ===');
    
    const bgRemoverBtn = document.querySelector('button[data-tool="background-remover"]');
    if (!bgRemoverBtn) return false;
    
    let successCount = 0;
    const testCount = 3;
    
    console.log(`开始${testCount}次点击测试...`);
    
    for (let i = 1; i <= testCount; i++) {
        console.log(`\n--- 第${i}次点击 ---`);
        
        try {
            // 点击按钮
            bgRemoverBtn.click();
            
            // 等待模态框响应
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 检查模态框是否打开
            const modal = document.getElementById('toolModal');
            if (modal && modal.style.display === 'flex') {
                console.log(`✅ 第${i}次点击成功，模态框已打开`);
                successCount++;
                
                // 关闭模态框
                const closeBtn = modal.querySelector('.modal-close');
                if (closeBtn) {
                    closeBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 300));
                    console.log(`   模态框已关闭`);
                }
            } else {
                console.error(`❌ 第${i}次点击失败，模态框未打开`);
            }
            
        } catch (error) {
            console.error(`❌ 第${i}次点击出错:`, error.message);
        }
    }
    
    console.log(`\n--- 测试结果 ---`);
    console.log(`成功次数: ${successCount}/${testCount}`);
    
    if (successCount === testCount) {
        console.log('🎉 多次点击测试通过！');
        return true;
    } else {
        console.log('❌ 多次点击测试失败');
        return false;
    }
}

// 4. 检查appManager状态
function checkAppManagerStatus() {
    console.log('\n=== 4. 检查appManager状态 ===');
    
    if (typeof window.appManager === 'undefined') {
        console.error('❌ appManager未定义');
        return false;
    }
    
    console.log('✅ appManager已定义');
    console.log('   - currentTool:', window.appManager.currentTool);
    console.log('   - openTool方法:', typeof window.appManager.openTool);
    
    return true;
}

// 5. 主验证函数
async function runVerification() {
    console.log('🚀 开始完整验证...\n');
    
    const results = {
        buttonConfig: checkButtonConfiguration(),
        eventListeners: checkEventListeners(),
        appManager: checkAppManagerStatus(),
        multipleClicks: await testMultipleClicks()
    };
    
    console.log('\n=== 最终验证结果 ===');
    
    const allPassed = Object.values(results).every(result => result === true);
    
    if (allPassed) {
        console.log('🎉 所有测试通过！背景移除工具修复成功！');
        console.log('✅ 工具现在可以正常多次使用');
    } else {
        console.log('❌ 部分测试失败，需要进一步检查');
        console.log('测试结果:', results);
    }
    
    return allPassed;
}

// 自动运行验证
setTimeout(() => {
    runVerification();
}, 2000);

console.log('⏳ 验证脚本已加载，2秒后自动开始...');