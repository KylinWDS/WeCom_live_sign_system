import unittest
from datetime import datetime, timedelta
from src.models.user import User, UserRole
from src.models.sign_record import SignRecord, SignStatus
from src.models.live_booking import LiveBooking, LiveStatus, LiveType

class TestModels(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试用户
        self.test_user = User(
            userid="test_user",
            name="测试用户",
            role=UserRole.NORMAL,
            corpname="测试企业",
            corpid="test_corpid",
            corpsecret="test_secret",
            agentid="test_agent"
        )
        
        # 创建测试直播
        self.test_live = LiveBooking(
            livingid="test_living_id",
            theme="测试直播",
            living_start=datetime.now(),
            living_duration=3600,
            anchor_userid="test_anchor",
            description="测试描述",
            type=LiveType.GENERAL,
            status=LiveStatus.RESERVING,
            corpname="测试企业",
            agentid="test_agent"
        )
        
        # 创建测试签到记录
        self.test_sign = SignRecord(
            userid="test_user",
            name="测试用户",
            department="测试部门",
            sign_time=datetime.now(),
            sign_count=0,
            live_booking_id=1
        )
    
    def test_user_model(self):
        """测试用户模型"""
        # 测试用户角色判断
        self.assertFalse(self.test_user.is_super_admin())
        self.assertFalse(self.test_user.is_wecom_admin())
        self.assertTrue(self.test_user.is_normal_user())
        
        # 测试用户信息转换
        user_dict = self.test_user.to_dict()
        self.assertEqual(user_dict["userid"], "test_user")
        self.assertEqual(user_dict["name"], "测试用户")
        self.assertEqual(user_dict["role"], UserRole.NORMAL)
        
        # 测试从字典创建用户
        new_user = User.from_dict(user_dict)
        self.assertEqual(new_user.userid, "test_user")
        self.assertEqual(new_user.name, "测试用户")
        self.assertEqual(new_user.role, UserRole.NORMAL)
    
    def test_sign_record_model(self):
        """测试签到记录模型"""
        # 测试微信用户名称处理
        test_name = "测试用户@微信"
        processed_name = SignRecord.process_wechat_name(test_name)
        self.assertEqual(processed_name, "测试用户")
        
        # 测试签到次数增加
        initial_count = self.test_sign.sign_count
        self.test_sign.increment_sign_count()
        self.assertEqual(self.test_sign.sign_count, initial_count + 1)
        
        # 测试签到状态更新
        self.test_sign.update_status()
        self.assertEqual(self.test_sign.status, SignStatus.NORMAL)
        
        # 测试签到记录转换
        sign_dict = self.test_sign.to_dict()
        self.assertEqual(sign_dict["userid"], "test_user")
        self.assertEqual(sign_dict["name"], "测试用户")
        self.assertEqual(sign_dict["department"], "测试部门")
        
        # 测试从字典创建签到记录
        new_sign = SignRecord.from_dict(sign_dict)
        self.assertEqual(new_sign.userid, "test_user")
        self.assertEqual(new_sign.name, "测试用户")
        self.assertEqual(new_sign.department, "测试部门")

if __name__ == "__main__":
    unittest.main() 