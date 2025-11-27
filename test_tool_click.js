// 工具按钮测试脚本
console.log('开始测试工具按钮...');

// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        testToolButtons();
    }, 1000);
});

function testToolButtons() {
    console.log('查找工具按钮...');
    
    // 查找所有工具按钮
    const toolButtons = document.querySelectorAll('.tool-btn');
    console.log(`找到 ${toolButtons.length} 个工具按钮`);
    
    // 测试每个按钮
    toolButtons.forEach((btn, index) => {
        const onclickAttr = btn.getAttribute('onclick');
        console.log(`按钮 ${index + 1}: ${onclickAttr}`);
        
        // 模拟点击
        setTimeout(() => {
            console.log(`点击按钮 ${index + 1}`);
            btn.click();
            
            // 检查是否有模态框出现
            setTimeout(() => {
                const modal = document.getElementById('toolModal');
                if (modal && modal.style.display === 'flex') {
                    console.log(`✅ 按钮 ${index + 1} 点击成功，模态框已打开`);
                    
                    // 关闭模态框
                    modal.style.display = 'none';
                } else {
                    console.log(`❌ 按钮 ${index + 1} 点击失败`);
                }
            }, 500);
        }, (index + 1) * 1000);
    });
    
    // 测试重复点击
    setTimeout(() => {
        console.log('开始重复点击测试...');
        const firstBtn = toolButtons[0];
        if (firstBtn) {
            for (let i = 0; i < 3; i++) {
                setTimeout(() => {
                    console.log(`重复点击第 ${i + 1} 次`);
                    firstBtn.click();
                }, i * 300);
            }
        }
    }, (toolButtons.length + 2) * 1000);
}