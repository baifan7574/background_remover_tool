"""
Supabase数据库完整初始化脚本
包含用户管理、工具使用记录、系统配置等所有必要的表和存储桶
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class SupabaseInitializer:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # 使用服务密钥进行初始化
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("请设置SUPABASE_URL和SUPABASE_SERVICE_KEY环境变量")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
    
    def execute_sql(self, sql):
        """执行SQL语句"""
        try:
            # 注意：这里需要使用RPC调用或者直接在Supabase控制台执行
            # 由于Supabase Python客户端的限制，某些DDL操作可能需要在控制台执行
            print(f"执行SQL: {sql}")
            # response = self.client.rpc('exec_sql', {'sql': sql}).execute()
            print("⚠️  请在Supabase控制台的SQL编辑器中执行以下SQL语句：")
            print("-" * 60)
            print(sql)
            print("-" * 60)
            return True
        except Exception as e:
            print(f"SQL执行失败: {e}")
            return False
    
    def create_tables(self):
        """创建所有必要的表"""
        print("🗄️  创建数据库表...")
        
        # 用户扩展信息表
        user_profiles_sql = """
-- 用户扩展信息表
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    name TEXT,
    plan TEXT DEFAULT 'free',
    credits INTEGER DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
"""
        
        # 工具使用记录表
        tool_usage_sql = """
-- 工具使用记录表
CREATE TABLE IF NOT EXISTS tool_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    credits_used INTEGER NOT NULL DEFAULT 1,
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tool_usage_user_id ON tool_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_tool_name ON tool_usage(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_usage_created_at ON tool_usage(created_at);
"""
        
        # 系统配置表
        system_config_sql = """
-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 插入默认配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('app_version', '2.1.0', '应用版本'),
('maintenance_mode', 'false', '维护模式'),
('max_file_size', '16777216', '最大文件大小（字节）'),
('free_user_credits', '10', '免费用户初始积分'),
('background_remover_credits', '2', '背景移除工具积分消耗'),
('converter_credits', '1', '转换工具积分消耗')
ON CONFLICT (config_key) DO NOTHING;
"""
        
        # 用户积分记录表
        credit_transactions_sql = """
-- 用户积分交易记录表
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    transaction_type TEXT NOT NULL, -- 'usage', 'purchase', 'refund', 'bonus'
    amount INTEGER NOT NULL,
    description TEXT,
    reference_id UUID, -- 关联的工具使用ID或其他引用
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);
"""
        
        # 支付记录表
        payments_sql = """
-- 支付记录表
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    payment_method TEXT, -- 'wechat', 'alipay', 'credit_card'
    amount DECIMAL(10,2) NOT NULL,
    credits INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'refunded'
    transaction_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
"""
        
        # 执行所有SQL
        tables = [
            ("用户扩展信息表", user_profiles_sql),
            ("工具使用记录表", tool_usage_sql),
            ("系统配置表", system_config_sql),
            ("用户积分交易记录表", credit_transactions_sql),
            ("支付记录表", payments_sql)
        ]
        
        for table_name, sql in tables:
            print(f"\n📝 创建{table_name}...")
            self.execute_sql(sql)
    
    def create_storage_buckets(self):
        """创建存储桶"""
        print("\n📁 创建存储桶...")
        
        # 处理后的图片存储桶
        processed_images_sql = """
-- 创建处理后的图片存储桶
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'processed-images', 
    'processed-images', 
    true, 
    10485760, -- 10MB
    ARRAY['image/png', 'image/jpeg', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- 设置存储桶策略
CREATE POLICY "用户可以上传自己的处理图片" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'processed-images' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);

CREATE POLICY "用户可以查看自己的处理图片" ON storage.objects
FOR SELECT USING (
    bucket_id = 'processed-images' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);

CREATE POLICY "用户可以更新自己的处理图片" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'processed-images' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);

CREATE POLICY "用户可以删除自己的处理图片" ON storage.objects
FOR DELETE USING (
    bucket_id = 'processed-images' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);
"""
        
        # 原始上传文件存储桶
        uploads_sql = """
-- 创建原始上传文件存储桶
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'uploads', 
    'uploads', 
    false, -- 私有存储桶
    16777216, -- 16MB
    ARRAY['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/bmp']
)
ON CONFLICT (id) DO NOTHING;

-- 设置存储桶策略
CREATE POLICY "用户可以上传自己的文件" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'uploads' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);

CREATE POLICY "用户可以查看自己的文件" ON storage.objects
FOR SELECT USING (
    bucket_id = 'uploads' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);

CREATE POLICY "用户可以删除自己的文件" ON storage.objects
FOR DELETE USING (
    bucket_id = 'uploads' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()
);
"""
        
        buckets = [
            ("处理后的图片存储桶", processed_images_sql),
            ("原始上传文件存储桶", uploads_sql)
        ]
        
        for bucket_name, sql in buckets:
            print(f"\n📦 创建{bucket_name}...")
            self.execute_sql(sql)
    
    def create_functions(self):
        """创建数据库函数"""
        print("\n⚙️  创建数据库函数...")
        
        # 获取用户积分函数
        get_user_credits_sql = """
-- 获取用户积分函数
CREATE OR REPLACE FUNCTION get_user_credits(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    user_credits INTEGER;
BEGIN
    SELECT credits INTO user_credits 
    FROM user_profiles 
    WHERE user_id = user_uuid;
    
    RETURN COALESCE(user_credits, 0);
END;
$$ LANGUAGE plpgsql;
"""
        
        # 更新用户积分函数
        update_user_credits_sql = """
-- 更新用户积分函数
CREATE OR REPLACE FUNCTION update_user_credits(user_uuid UUID, credit_change INTEGER)
RETURNS INTEGER AS $$
DECLARE
    current_credits INTEGER;
    new_credits INTEGER;
BEGIN
    -- 获取当前积分
    SELECT credits INTO current_credits 
    FROM user_profiles 
    WHERE user_id = user_uuid;
    
    -- 如果用户不存在，创建新记录
    IF current_credits IS NULL THEN
        INSERT INTO user_profiles (user_id, credits)
        VALUES (user_uuid, GREATEST(0, credit_change))
        RETURNING credits INTO new_credits;
    ELSE
        -- 更新积分
        UPDATE user_profiles 
        SET credits = GREATEST(0, credits + credit_change),
            updated_at = NOW()
        WHERE user_id = user_uuid
        RETURNING credits INTO new_credits;
    END IF;
    
    RETURN new_credits;
END;
$$ LANGUAGE plpgsql;
"""
        
        # 记录积分交易函数
        record_credit_transaction_sql = """
-- 记录积分交易函数
CREATE OR REPLACE FUNCTION record_credit_transaction(
    user_uuid UUID,
    transaction_type_param TEXT,
    amount_param INTEGER,
    description_param TEXT DEFAULT NULL,
    reference_id_param UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    transaction_id UUID;
BEGIN
    INSERT INTO credit_transactions (
        user_id, 
        transaction_type, 
        amount, 
        description, 
        reference_id
    )
    VALUES (
        user_uuid,
        transaction_type_param,
        amount_param,
        description_param,
        reference_id_param
    )
    RETURNING id INTO transaction_id;
    
    RETURN transaction_id;
END;
$$ LANGUAGE plpgsql;
"""
        
        functions = [
            ("获取用户积分函数", get_user_credits_sql),
            ("更新用户积分函数", update_user_credits_sql),
            ("记录积分交易函数", record_credit_transaction_sql)
        ]
        
        for function_name, sql in functions:
            print(f"\n🔧 创建{function_name}...")
            self.execute_sql(sql)
    
    def create_triggers(self):
        """创建触发器"""
        print("\n🔨 创建触发器...")
        
        # 用户积分交易触发器
        credit_transaction_trigger_sql = """
-- 创建积分交易触发器函数
CREATE OR REPLACE FUNCTION handle_credit_transaction()
RETURNS TRIGGER AS $$
BEGIN
    -- 根据交易类型更新用户积分
    IF NEW.transaction_type = 'usage' THEN
        PERFORM update_user_credits(NEW.user_id, -NEW.amount);
    ELSIF NEW.transaction_type = 'purchase' THEN
        PERFORM update_user_credits(NEW.user_id, NEW.amount);
    ELSIF NEW.transaction_type = 'refund' THEN
        PERFORM update_user_credits(NEW.user_id, NEW.amount);
    ELSIF NEW.transaction_type = 'bonus' THEN
        PERFORM update_user_credits(NEW.user_id, NEW.amount);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS on_credit_transaction_insert ON credit_transactions;
CREATE TRIGGER on_credit_transaction_insert
AFTER INSERT ON credit_transactions
FOR EACH ROW
EXECUTE FUNCTION handle_credit_transaction();
"""
        
        # 工具使用记录触发器
        tool_usage_trigger_sql = """
-- 创建工具使用记录触发器函数
CREATE OR REPLACE FUNCTION handle_tool_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- 记录积分交易
    PERFORM record_credit_transaction(
        NEW.user_id,
        'usage',
        NEW.credits_used,
        CONCAT('使用工具: ', NEW.tool_name),
        NEW.id
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS on_tool_usage_insert ON tool_usage;
CREATE TRIGGER on_tool_usage_insert
AFTER INSERT ON tool_usage
FOR EACH ROW
EXECUTE FUNCTION handle_tool_usage();
"""
        
        triggers = [
            ("积分交易触发器", credit_transaction_trigger_sql),
            ("工具使用记录触发器", tool_usage_trigger_sql)
        ]
        
        for trigger_name, sql in triggers:
            print(f"\n⚡ 创建{trigger_name}...")
            self.execute_sql(sql)
    
    def run_initialization(self):
        """运行完整初始化"""
        print("🚀 开始Supabase数据库完整初始化")
        print("=" * 60)
        
        try:
            # 1. 创建表
            self.create_tables()
            
            # 2. 创建存储桶
            self.create_storage_buckets()
            
            # 3. 创建函数
            self.create_functions()
            
            # 4. 创建触发器
            self.create_triggers()
            
            print("\n" + "=" * 60)
            print("✅ Supabase数据库初始化完成！")
            print("=" * 60)
            print("\n📋 后续步骤：")
            print("1. 在Supabase控制台的SQL编辑器中执行上述所有SQL语句")
            print("2. 检查存储桶是否正确创建")
            print("3. 验证RLS（行级安全）策略是否生效")
            print("4. 测试用户注册和工具使用功能")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 初始化失败: {e}")
            return False

def main():
    """主函数"""
    print("🗄️  Supabase数据库初始化工具")
    print("请确保已正确配置.env文件中的SUPABASE_URL和SUPABASE_SERVICE_KEY")
    print()
    
    input("按回车键开始初始化...")
    
    try:
        initializer = SupabaseInitializer()
        success = initializer.run_initialization()
        
        if success:
            print("\n✅ 初始化脚本执行完成")
            print("请在Supabase控制台执行生成的SQL语句")
        else:
            print("\n❌ 初始化失败，请检查配置")
    
    except Exception as e:
        print(f"\n❌ 初始化异常: {e}")

if __name__ == "__main__":
    main()