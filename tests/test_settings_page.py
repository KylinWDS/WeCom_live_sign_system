import pytest
import os
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from src.ui.pages.settings_page import SettingsPage
from src.core.database import DatabaseManager
from src.core.config_manager import ConfigManager
from src.models.user import User

@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例"""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def settings_page(qapp, tmp_path):
    """创建 SettingsPage 实例"""
    page = None
    try:
        # 创建临时数据库文件
        db_path = str(tmp_path / "test.db")
        
        # 初始化数据库和配置管理器
        db_manager = DatabaseManager(db_path)
        config_manager = ConfigManager()
        
        # 创建设置页面
        page = SettingsPage(db_manager, config_manager)
        yield page
    finally:
        if page:
            page.close()
            page.deleteLater()

def test_theme_settings(settings_page, qtbot):
    """测试主题设置"""
    try:
        # 测试主题切换
        assert settings_page.theme_combo is not None
        assert settings_page.theme_combo.count() == 3  # 系统、浅色、深色
        
        # 测试保存主题设置
        settings_page.theme_combo.setCurrentText("暗色主题")
        assert settings_page.save_btn is not None
        qtbot.mouseClick(settings_page.save_btn, Qt.MouseButton.LeftButton)
    except Exception as e:
        pytest.fail(f"测试主题设置失败: {str(e)}")

def test_data_cleanup(settings_page, qtbot):
    """测试数据清理设置"""
    try:
        # 测试数据清理设置
        assert settings_page.auto_cleanup_check is not None
        qtbot.mouseClick(settings_page.auto_cleanup_check, Qt.MouseButton.LeftButton)
        assert settings_page.auto_cleanup_check.isChecked()
        
        # 测试清理天数设置
        assert settings_page.cleanup_days is not None
        settings_page.cleanup_days.setValue(60)
        assert settings_page.cleanup_days.value() == 60
    except Exception as e:
        pytest.fail(f"测试数据清理设置失败: {str(e)}")

def test_system_config(settings_page, qtbot):
    """测试系统配置"""
    try:
        # 测试系统配置保存
        assert settings_page.corp_id is not None
        assert settings_page.app_id is not None
        assert settings_page.app_secret is not None
        
        settings_page.corp_id.setText("test_corp_id")
        settings_page.app_id.setText("test_app_id")
        settings_page.app_secret.setText("test_app_secret")
        
        assert settings_page.save_btn is not None
        qtbot.mouseClick(settings_page.save_btn, Qt.MouseButton.LeftButton)
    except Exception as e:
        pytest.fail(f"测试系统配置失败: {str(e)}")

def test_user_management(settings_page, qtbot):
    """测试用户管理"""
    try:
        # 测试用户表格
        assert settings_page.user_table is not None
        
        # 测试添加用户
        assert settings_page.add_btn is not None
        qtbot.mouseClick(settings_page.add_btn, Qt.MouseButton.LeftButton)
        
        # 测试编辑用户
        settings_page.user_table.setRowCount(1)
        settings_page.user_table.setItem(0, 0, QTableWidgetItem("test_user"))
        settings_page.user_table.selectRow(0)
        
        assert settings_page.edit_btn is not None
        qtbot.mouseClick(settings_page.edit_btn, Qt.MouseButton.LeftButton)
        
        # 测试删除用户
        assert settings_page.delete_btn is not None
        qtbot.mouseClick(settings_page.delete_btn, Qt.MouseButton.LeftButton)
    except Exception as e:
        pytest.fail(f"测试用户管理失败: {str(e)}")

def test_log_management(settings_page, qtbot):
    """测试日志管理"""
    try:
        # 测试日志查看
        assert settings_page.view_btn is not None
        qtbot.mouseClick(settings_page.view_btn, Qt.MouseButton.LeftButton)
        
        # 测试日志导出
        assert settings_page.start_date is not None
        assert settings_page.end_date is not None
        assert settings_page.log_type is not None
        assert settings_page.export_btn is not None
        
        settings_page.start_date.setDate(QDate.currentDate().addDays(-7))
        settings_page.end_date.setDate(QDate.currentDate())
        settings_page.log_type.setCurrentText("操作日志")
        qtbot.mouseClick(settings_page.export_btn, Qt.MouseButton.LeftButton)
    except Exception as e:
        pytest.fail(f"测试日志管理失败: {str(e)}")

def test_permission_control(settings_page, qtbot):
    """测试权限控制"""
    try:
        # 创建测试用户
        user = User()
        user.username = "admin"
        user.set_password("admin123")
        user.role = 2  # 超级管理员
        
        # 测试权限
        assert user.has_permission("manage_users")
        assert "manage_users" in user.get_permissions()
    except Exception as e:
        pytest.fail(f"测试权限控制失败: {str(e)}") 