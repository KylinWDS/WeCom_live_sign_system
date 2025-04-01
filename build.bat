@echo off
:: 企业微信直播签到系统 - Windows打包脚本
:: 作者: Kylin
:: 邮箱: kylin_wds@163.com

setlocal enabledelayedexpansion

:: 获取脚本目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 颜色定义
set "RED=[91m"
set "GREEN=[92m"
set "BLUE=[94m"
set "YELLOW=[93m"
set "NC=[0m"

:: 打印带颜色的消息
:print_info
echo %BLUE%[信息] %~1%NC%
exit /b

:print_success
echo %GREEN%[成功] %~1%NC%
exit /b

:print_warning
echo %YELLOW%[警告] %~1%NC%
exit /b

:print_error
echo %RED%[错误] %~1%NC%
exit /b

:: 带倒计时的选择函数
:read_with_timeout
set "prompt=%~1"
set "default=%~2"
set "timeout=5"

:: 显示提示信息
echo %prompt% (%timeout%秒后自动选择默认值: %default%): 

:: 使用choice命令进行倒计时
choice /c 123456789 /n /t %timeout% /d %default% /m ""
if %errorlevel% leq 9 (
    echo %errorlevel%
    exit /b %errorlevel%
) else (
    echo %default%
    exit /b %default%
)

:: 检测系统类型
set "SYSTEM=Windows"
set "ARCH=%PROCESSOR_ARCHITECTURE%"

:: 检测Python版本
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py"
    ) else (
        call :print_error "未找到Python，请先安装Python 3.7+"
        exit /b 1
    )
)

for /f "tokens=*" %%a in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"') do set "PYTHON_VERSION=%%a"

:: 显示欢迎信息
echo =============================================
echo     企业微信直播签到系统打包工具
echo =============================================
echo 系统: %SYSTEM% %ARCH%
echo Python: %PYTHON_VERSION%
echo 工作目录: %SCRIPT_DIR%
echo 时间: %date% %time%
echo =============================================
echo.

:: 检查依赖项
call :check_dependencies
if %errorlevel% neq 0 exit /b 1

:: 选择打包选项
call :select_package_mode
call :select_memory_level
call :select_debug_mode

:: 显示摘要并确认
call :show_summary
if %errorlevel% neq 0 exit /b 0

:: 执行打包
call :do_packaging

:: 打包完成，给出提示
if %errorlevel% equ 0 (
    echo.
    call :print_success "打包已完成!"
    echo.
    echo 输出位置: %SCRIPT_DIR%dist\
    
    echo 您可以通过以下方式运行应用:
    echo 1. 直接运行 dist\企业微信直播签到系统.exe ^(单文件模式^)
    echo 2. 运行脚本 dist\启动企业微信直播签到系统.bat ^(目录模式^)
    
    :: 询问是否进行打包后清理
    call :post_packaging_cleanup
)

exit /b 0

:: 函数：检查依赖项
:check_dependencies
call :print_info "检查依赖项..."

:: 检查PyInstaller
%PYTHON_CMD% -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    call :print_warning "未安装PyInstaller，将尝试安装..."
    %PYTHON_CMD% -m pip install pyinstaller
    if %errorlevel% neq 0 (
        call :print_error "PyInstaller安装失败!"
        exit /b 1
    )
)

:: 检查psutil
%PYTHON_CMD% -c "import psutil" >nul 2>nul
if %errorlevel% neq 0 (
    call :print_warning "未安装psutil，将尝试安装..."
    %PYTHON_CMD% -m pip install psutil
    if %errorlevel% neq 0 (
        call :print_error "psutil安装失败!"
        exit /b 1
    )
)

:: 检查图像处理库(可选)
%PYTHON_CMD% -c "import PIL" >nul 2>nul
if %errorlevel% neq 0 (
    call :print_warning "未安装PIL/Pillow，某些图标生成功能可能不可用"
    call :print_warning "如需完整功能，请执行: pip install pillow"
)

exit /b 0

:: 函数：选择打包模式
:select_package_mode
echo 请选择打包模式:
echo 1) 目录模式 (快速启动，但分发时需要整个目录)
echo 2) 单文件模式 (启动较慢，但分发更简便)

:: 使用倒计时，默认选择1
call :read_with_timeout "请选择 [1-2]" 1
set "mode_choice=%errorlevel%"

if "%mode_choice%"=="2" (
    set "ONEFILE=--onefile"
    set "PACKAGE_MODE=单文件模式"
) else (
    set "ONEFILE="
    set "PACKAGE_MODE=目录模式"
)

call :print_info "已选择打包模式: %PACKAGE_MODE%"
exit /b 0

:: 函数：选择内存优化级别
:select_memory_level
echo 请选择内存优化级别:
echo 1) 低 (最小内存要求: 1024MB)
echo 2) 中 (最小内存要求: 2048MB)
echo 3) 高 (最小内存要求: 4096MB)

:: 使用倒计时，默认选择2
call :read_with_timeout "请选择 [1-3]" 2
set "memory_choice=%errorlevel%"

if "%memory_choice%"=="1" (
    set "MEMORY_LEVEL=low"
) else if "%memory_choice%"=="3" (
    set "MEMORY_LEVEL=high"
) else (
    set "MEMORY_LEVEL=medium"
)

call :print_info "已选择内存优化级别: %MEMORY_LEVEL%"
exit /b 0

:: 函数：选择是否创建调试版本
:select_debug_mode
echo 是否创建调试版本?
echo 1) 否 (正常版本)
echo 2) 是 (包含调试信息，文件更大)

:: D使用倒计时，默认选择1
call :read_with_timeout "请选择 [1-2]" 1
set "debug_choice=%errorlevel%"

if "%debug_choice%"=="2" (
    set "DEBUG=--debug"
    set "DEBUG_MODE=是"
) else (
    set "DEBUG="
    set "DEBUG_MODE=否"
)

call :print_info "是否包含调试信息: %DEBUG_MODE%"
exit /b 0

:: 函数：执行打包
:do_packaging
call :print_info "开始打包程序..."

:: 构建参数
set "BUILD_ARGS="

:: 打包模式
if defined ONEFILE set "BUILD_ARGS=%BUILD_ARGS% %ONEFILE%"

:: 调试模式
if defined DEBUG set "BUILD_ARGS=%BUILD_ARGS% %DEBUG%"

:: 内存级别
if defined MEMORY_LEVEL set "BUILD_ARGS=%BUILD_ARGS% --memory-level %MEMORY_LEVEL%"

:: 执行打包命令
call :print_info "执行: %PYTHON_CMD% build.py %BUILD_ARGS%"
%PYTHON_CMD% build.py %BUILD_ARGS%

if %errorlevel% neq 0 (
    call :print_error "打包失败!"
    exit /b 1
)

call :print_success "打包成功!"
exit /b 0

:: 函数：显示打包摘要
:show_summary
echo.
echo =============================================
echo               打包参数摘要
echo =============================================
echo 系统: %SYSTEM% %ARCH%
echo 打包模式: %PACKAGE_MODE%
echo 内存优化级别: %MEMORY_LEVEL%
echo 调试版本: %DEBUG_MODE%
echo =============================================
echo.

:: 使用choice命令进行倒计时确认，Y为默认
echo 确认开始打包? [Y/n] (5秒后自动选择默认值: Y): 
choice /c YN /t 5 /d Y /n /m ""
if %errorlevel% equ 2 (
    call :print_info "已取消打包"
    exit /b 1
)

exit /b 0

:: 函数：打包后清理
:post_packaging_cleanup
echo.
echo =============================================
echo               打包后清理
echo =============================================
echo 是否清理临时构建文件?
echo 1) 是 (清理临时文件，但保留可执行程序)
echo 2) 否 (保留所有文件)

:: 使用choice命令的超时功能，默认选择1
echo 请选择 [1-2] (5秒后自动选择1): 
choice /c 12 /t 5 /d 1 /n
set "cleanup_choice=%errorlevel%"

:: choice返回1表示选择了"1"选项
if "%cleanup_choice%"=="1" (
    call :print_info "正在清理临时文件..."
    
    :: 清理构建目录
    if exist "build" (
        rmdir /s /q "build"
        call :print_info "已删除: build目录"
    )
    
    :: 清理spec文件
    if exist "企业微信直播签到系统.spec" (
        del /f /q "企业微信直播签到系统.spec"
        call :print_info "已删除: 企业微信直播签到系统.spec"
    )
    
    :: 清理临时钩子文件
    for %%i in (memory_hook*.py fast_start_hook.py fix_macos_crash.py) do (
        if exist "%%i" (
            del /f /q "%%i"
            call :print_info "已删除: %%i"
        )
    )
    
    call :print_success "清理完成! 可执行文件保留在 dist 目录中"
) else (
    call :print_info "已取消清理"
)

exit /b 0 