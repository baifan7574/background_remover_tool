-- ========================================
-- 跨境电商工具站 - Supabase数据库初始化脚本
-- 一次性执行，避免来回修改
-- ========================================

-- 1. 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. 创建用户表
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    phone VARCHAR(20),
    membership_type VARCHAR(50) DEFAULT 'free' CHECK (membership_type IN ('free', 'basic', 'professional', 'flagship')),
    membership_expires_at TIMESTAMP WITH TIME ZONE,
    points INTEGER DEFAULT 0,
    invitation_code VARCHAR(20) UNIQUE,
    invited_by VARCHAR(255),
    wechat_openid VARCHAR(100),
    alipay_user_id VARCHAR(100),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 创建工具使用记录表
CREATE TABLE IF NOT EXISTS tool_usage (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    tool_type VARCHAR(100) NOT NULL CHECK (tool_type IN ('background_remover', 'keyword_analyzer', 'image_optimizer', 'batch_processor')),
    usage_count INTEGER DEFAULT 0,
    daily_limit INTEGER DEFAULT 0,
    monthly_usage INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 创建支付记录表
CREATE TABLE IF NOT EXISTS payment_records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    order_no VARCHAR(100) UNIQUE NOT NULL,
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('wechat', 'alipay', 'bank_card')),
    amount DECIMAL(10,2) NOT NULL,
    membership_type VARCHAR(50) NOT NULL,
    membership_duration INTEGER NOT NULL, -- 月数
    original_price DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    discount_type VARCHAR(50), -- 'early_bird', 'group_buy', 'promotion'
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    payment_transaction_id VARCHAR(200),
    paid_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 创建邀请记录表
CREATE TABLE IF NOT EXISTS invitation_records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    inviter_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    invitee_email VARCHAR(255) NOT NULL,
    invitation_code VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired')),
    reward_days INTEGER DEFAULT 7,
    accepted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 创建营销活动表
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('early_bird', 'group_buy', 'promotion', 'referral')),
    description TEXT,
    discount_percentage DECIMAL(5,2),
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 创建文件存储记录表
CREATE TABLE IF NOT EXISTS file_storage (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_result JSONB DEFAULT '{}',
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. 创建用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. 创建操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    operation_type VARCHAR(100) NOT NULL,
    operation_details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- 创建索引优化查询性能
-- ========================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_membership_type ON user_profiles(membership_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_invitation_code ON user_profiles(invitation_code);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- 工具使用记录表索引
CREATE INDEX IF NOT EXISTS idx_tool_usage_user_id ON tool_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_tool_type ON tool_usage(tool_type);
CREATE INDEX IF NOT EXISTS idx_tool_usage_last_used ON tool_usage(last_used);

-- 支付记录表索引
CREATE INDEX IF NOT EXISTS idx_payment_records_user_id ON payment_records(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_records_order_no ON payment_records(order_no);
CREATE INDEX IF NOT EXISTS idx_payment_records_status ON payment_records(status);
CREATE INDEX IF NOT EXISTS idx_payment_records_created_at ON payment_records(created_at);

-- 邀请记录表索引
CREATE INDEX IF NOT EXISTS idx_invitation_records_inviter_id ON invitation_records(inviter_id);
CREATE INDEX IF NOT EXISTS idx_invitation_records_code ON invitation_records(invitation_code);
CREATE INDEX IF NOT EXISTS idx_invitation_records_status ON invitation_records(status);

-- 文件存储表索引
CREATE INDEX IF NOT EXISTS idx_file_storage_user_id ON file_storage(user_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_processing_status ON file_storage(processing_status);
CREATE INDEX IF NOT EXISTS idx_file_storage_created_at ON file_storage(created_at);

-- 操作日志表索引
CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_operation_type ON operation_logs(operation_type);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs(created_at);

-- ========================================
-- 创建RLS (Row Level Security) 策略
-- ========================================

-- 启用RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitation_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_storage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE operation_logs ENABLE ROW LEVEL SECURITY;

-- 用户表RLS策略
CREATE POLICY "用户只能查看自己的信息" ON user_profiles FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY "用户只能更新自己的信息" ON user_profiles FOR UPDATE USING (auth.uid()::text = id::text);
CREATE POLICY "允许用户注册" ON user_profiles FOR INSERT WITH CHECK (true);

-- 工具使用记录表RLS策略
CREATE POLICY "用户只能查看自己的使用记录" ON tool_usage FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能插入自己的使用记录" ON tool_usage FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能更新自己的使用记录" ON tool_usage FOR UPDATE USING (auth.uid()::text = user_id::text);

-- 支付记录表RLS策略
CREATE POLICY "用户只能查看自己的支付记录" ON payment_records FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能插入自己的支付记录" ON payment_records FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- 邀请记录表RLS策略
CREATE POLICY "用户只能查看自己发起的邀请" ON invitation_records FOR SELECT USING (auth.uid()::text = inviter_id::text);
CREATE POLICY "用户只能创建自己的邀请" ON invitation_records FOR INSERT WITH CHECK (auth.uid()::text = inviter_id::text);

-- 文件存储表RLS策略
CREATE POLICY "用户只能查看自己的文件" ON file_storage FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能上传自己的文件" ON file_storage FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能删除自己的文件" ON file_storage FOR DELETE USING (auth.uid()::text = user_id::text);

-- 用户会话表RLS策略
CREATE POLICY "用户只能查看自己的会话" ON user_sessions FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能创建自己的会话" ON user_sessions FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能删除自己的会话" ON user_sessions FOR DELETE USING (auth.uid()::text = user_id::text);

-- 操作日志表RLS策略
CREATE POLICY "用户只能查看自己的操作日志" ON operation_logs FOR SELECT USING (auth.uid()::text = user_id::text);
CREATE POLICY "用户只能插入自己的操作日志" ON operation_logs FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- ========================================
-- 创建触发器函数
-- ========================================

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建触发器
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tool_usage_updated_at BEFORE UPDATE ON tool_usage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_records_updated_at BEFORE UPDATE ON payment_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_file_storage_updated_at BEFORE UPDATE ON file_storage FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 插入初始系统配置数据
-- ========================================

INSERT INTO system_config (config_key, config_value, description, is_public) VALUES
('site_name', '跨境电商工具站', '网站名称', true),
('site_description', '专业的跨境电商工具服务平台', '网站描述', true),
('membership_basic_price', '39.00', '基础版会员价格', false),
('membership_professional_price', '59.00', '专业版会员价格', false),
('membership_flagship_price', '99.00', '旗舰版会员价格', false),
('basic_daily_image_limit', '10', '基础版每日图片处理次数限制', false),
('basic_daily_analysis_limit', '5', '基础版每日关键词分析次数限制', false),
('professional_daily_image_limit', '100', '专业版每日图片处理次数限制', false),
('professional_daily_analysis_limit', '50', '专业版每日关键词分析次数限制', false),
('flagship_daily_image_limit', '-1', '旗舰版每日图片处理次数限制（-1表示无限制）', false),
('flagship_daily_analysis_limit', '-1', '旗舰版每日关键词分析次数限制（-1表示无限制）', false),
('invitation_reward_days', '7', '邀请奖励天数', false),
('file_storage_days', '30', '文件存储天数', false),
('max_file_size_mb', '50', '最大文件大小（MB）', false)
ON CONFLICT (config_key) DO NOTHING;

-- ========================================
-- 创建存储桶策略（需要在Supabase控制台手动创建存储桶后执行）
-- ========================================

-- 注意：以下SQL需要在Supabase控制台的Storage部分创建存储桶后执行
-- 存储桶名称：processed-images

-- 允许认证用户上传文件
CREATE POLICY "认证用户可以上传文件" ON storage.objects FOR INSERT WITH CHECK (
    bucket_id = 'processed-images' AND 
    auth.role() = 'authenticated'
);

-- 允许用户查看自己的文件
CREATE POLICY "用户只能查看自己的文件" ON storage.objects FOR SELECT USING (
    bucket_id = 'processed-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

-- 允许用户更新自己的文件
CREATE POLICY "用户只能更新自己的文件" ON storage.objects FOR UPDATE USING (
    bucket_id = 'processed-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

-- 允许用户删除自己的文件
CREATE POLICY "用户只能删除自己的文件" ON storage.objects FOR DELETE USING (
    bucket_id = 'processed-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

-- ========================================
-- 创建视图简化查询
-- ========================================

-- 用户统计视图
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    u.id,
    u.email,
    u.membership_type,
    u.membership_expires_at,
    u.points,
    COALESCE(tu.image_usage, 0) as image_usage_today,
    COALESCE(tu.analysis_usage, 0) as analysis_usage_today,
    COALESCE(pr.total_payments, 0) as total_payments,
    u.created_at
FROM user_profiles u
LEFT JOIN (
    SELECT 
        user_id,
        COUNT(CASE WHEN tool_type = 'background_remover' THEN 1 END) as image_usage,
        COUNT(CASE WHEN tool_type = 'keyword_analyzer' THEN 1 END) as analysis_usage
    FROM tool_usage 
    WHERE DATE(last_used) = CURRENT_DATE
    GROUP BY user_id
) tu ON u.id = tu.user_id
LEFT JOIN (
    SELECT 
        user_id,
        SUM(amount) as total_payments
    FROM payment_records 
    WHERE status = 'paid'
    GROUP BY user_id
) pr ON u.id = pr.user_id;

-- ========================================
-- 完成提示
-- ========================================

-- 创建完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '跨境电商工具站数据库初始化完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已创建的表：';
    RAISE NOTICE '- user_profiles (用户表)';
    RAISE NOTICE '- tool_usage (工具使用记录表)';
    RAISE NOTICE '- payment_records (支付记录表)';
    RAISE NOTICE '- invitation_records (邀请记录表)';
    RAISE NOTICE '- marketing_campaigns (营销活动表)';
    RAISE NOTICE '- file_storage (文件存储记录表)';
    RAISE NOTICE '- system_config (系统配置表)';
    RAISE NOTICE '- user_sessions (用户会话表)';
    RAISE NOTICE '- operation_logs (操作日志表)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '请记得在Supabase控制台创建存储桶：processed-images';
    RAISE NOTICE '========================================';
END $$;