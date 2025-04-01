#!/bin/bash
# 企业微信直播签到系统 - macOS/Linux打包脚本
# 作者: Kylin
# 邮箱: kylin_wds@163.com

# 获取脚本目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # 无颜色

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[信息] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[成功] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[警告] $1${NC}"
}

print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

# 超时选择函数
read_with_timeout() {
    prompt="$1"
    default="$2"
    timeout=5
    
    # 显示提示和倒计时
    for i in $(seq $timeout -1 1); do
        echo -ne "\r${prompt} (${i}秒后自动选择默认值: ${default}): "
        read -t 1 -n 1 answer
        if [ $? -eq 0 ]; then
            echo ""  # 换行
            # 返回用户输入
            echo "$answer"
            return 0
        fi
    done
    
    echo ""  # 倒计时结束后换行
    # 返回默认值，并确保没有额外的空格或换行符
    echo -n "$default"
    return 0
}

# 检测系统类型
if [[ "$(uname)" == "Darwin" ]]; then
    SYSTEM="macOS"
    if [[ "$(uname -m)" == "arm64" ]]; then
        ARCH="Apple Silicon"
    else
        ARCH="Intel"
    fi
elif [[ "$(uname)" == "Linux" ]]; then
    SYSTEM="Linux"
    ARCH="$(uname -m)"
else
    SYSTEM="Unknown"
    ARCH="Unknown"
fi

# 检测Python版本
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    print_error "未找到Python，请先安装Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")

# 显示欢迎信息
echo "============================================="
echo "    企业微信直播签到系统打包工具"
echo "============================================="
echo "系统: $SYSTEM $ARCH"
echo "Python: $PYTHON_VERSION"
echo "工作目录: $SCRIPT_DIR"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================="
echo ""

# 函数：检查依赖项
check_dependencies() {
    print_info "检查依赖项..."
    
    # 检查PyInstaller
    if ! $PYTHON_CMD -c "import PyInstaller" &>/dev/null; then
        print_warning "未安装PyInstaller，将尝试安装..."
        $PYTHON_CMD -m pip install pyinstaller
        if [ $? -ne 0 ]; then
            print_error "PyInstaller安装失败!"
            return 1
        fi
    fi
    
    # 检查psutil
    if ! $PYTHON_CMD -c "import psutil" &>/dev/null; then
        print_warning "未安装psutil，将尝试安装..."
        $PYTHON_CMD -m pip install psutil
        if [ $? -ne 0 ]; then
            print_error "psutil安装失败!"
            return 1
        fi
    fi
    
    # 检查图像处理库(可选)
    if ! $PYTHON_CMD -c "import PIL" &>/dev/null; then
        print_warning "未安装PIL/Pillow，某些图标生成功能可能不可用"
        print_warning "如需完整功能，请执行: pip install pillow"
    fi
    
    return 0
}

# 函数：选择打包架构
select_architecture() {
    echo "请选择打包架构:"
    
    if [[ "$SYSTEM" == "macOS" ]]; then
        echo "1) 当前架构 ($ARCH)"
        echo "2) Intel (x86_64)"
        echo "3) Apple Silicon (arm64)"
        echo "4) 通用二进制 (Universal Binary)"
        
        # 使用倒计时选择，默认为1
        arch_choice=$(read_with_timeout "请选择 [1-4]" "1")
        
        case $arch_choice in
            2) TARGET_ARCH="intel" ;;
            3) TARGET_ARCH="arm" ;;
            4) TARGET_ARCH="universal" ;;
            *) TARGET_ARCH="auto" ;;
        esac
    else
        # 非macOS系统不提供架构选择
        TARGET_ARCH="auto"
    fi
    
    print_info "已选择打包架构: $TARGET_ARCH"
    return 0
}

# 函数：选择打包模式
select_package_mode() {
    echo "请选择打包模式:"
    echo "1) 目录模式 (快速启动，但分发时需要整个目录)"
    echo "2) 单文件模式 (启动较慢，但分发更简便)"
    
    # 使用倒计时选择，默认为1
    mode_choice=$(read_with_timeout "请选择 [1-2]" "1")
    
    if [[ "$mode_choice" == "2" ]]; then
        ONEFILE="--onefile"
        PACKAGE_MODE="单文件模式"
    else
        ONEFILE=""
        PACKAGE_MODE="目录模式"
    fi
    
    print_info "已选择打包模式: $PACKAGE_MODE"
    return 0
}

# 函数：选择内存优化级别
select_memory_level() {
    echo "请选择内存优化级别:"
    echo "1) 低 (最小内存要求: 1024MB)"
    echo "2) 中 (最小内存要求: 2048MB)"
    echo "3) 高 (最小内存要求: 4096MB)"
    
    # 使用倒计时选择，默认为2
    memory_choice=$(read_with_timeout "请选择 [1-3]" "2")
    
    case $memory_choice in
        1) MEMORY_LEVEL="low" ;;
        3) MEMORY_LEVEL="high" ;;
        *) MEMORY_LEVEL="medium" ;;
    esac
    
    print_info "已选择内存优化级别: $MEMORY_LEVEL"
    return 0
}

# 函数：选择是否创建调试版本
select_debug_mode() {
    echo "是否创建调试版本?"
    echo "1) 否 (正常版本)"
    echo "2) 是 (包含调试信息，文件更大)"
    
    # 使用倒计时选择，默认为1
    debug_choice=$(read_with_timeout "请选择 [1-2]" "1")
    
    if [[ "$debug_choice" == "2" ]]; then
        DEBUG="--debug"
        DEBUG_MODE="是"
    else
        DEBUG=""
        DEBUG_MODE="否"
    fi
    
    print_info "是否包含调试信息: $DEBUG_MODE"
    return 0
}

# 函数：执行打包
do_packaging() {
    print_info "开始打包程序..."
    
    # 构建参数
    BUILD_ARGS=""
    
    # 打包模式
    if [[ -n "$ONEFILE" ]]; then
        BUILD_ARGS="$BUILD_ARGS $ONEFILE"
    fi
    
    # 调试模式
    if [[ -n "$DEBUG" ]]; then
        BUILD_ARGS="$BUILD_ARGS $DEBUG"
    fi
    
    # 内存级别
    if [[ -n "$MEMORY_LEVEL" ]]; then
        BUILD_ARGS="$BUILD_ARGS --memory-level $MEMORY_LEVEL"
    fi
    
    # 架构选项 (仅macOS)
    if [[ "$SYSTEM" == "macOS" && -n "$TARGET_ARCH" ]]; then
        BUILD_ARGS="$BUILD_ARGS --target-arch $TARGET_ARCH"
    fi
    
    # 执行打包命令
    print_info "执行: $PYTHON_CMD build.py $BUILD_ARGS"
    $PYTHON_CMD build.py $BUILD_ARGS
    
    if [ $? -ne 0 ]; then
        print_error "打包失败!"
        return 1
    fi
    
    print_success "打包成功!"
    return 0
}

# 函数：显示打包摘要
show_summary() {
    echo ""
    echo "============================================="
    echo "              打包参数摘要"
    echo "============================================="
    echo "系统: $SYSTEM $ARCH"
    echo "打包模式: $PACKAGE_MODE"
    echo "内存优化级别: $MEMORY_LEVEL"
    echo "调试版本: $DEBUG_MODE"
    if [[ "$SYSTEM" == "macOS" ]]; then
        echo "目标架构: $TARGET_ARCH"
    fi
    echo "============================================="
    echo ""
    
    # 使用倒计时确认，默认为Y
    confirm=$(read_with_timeout "确认开始打包? [Y/n]" "Y")
    
    if [[ "$confirm" == "n" || "$confirm" == "N" ]]; then
        print_info "已取消打包"
        return 1
    fi
    
    return 0
}

# 函数：打包后清理
post_packaging_cleanup() {
    echo ""
    echo "============================================="
    echo "              打包后清理"
    echo "============================================="
    echo "是否清理临时构建文件?"
    echo "1) 是 (清理临时文件，但保留可执行程序)"
    echo "2) 否 (保留所有文件)"
    
    # 直接使用read命令和超时
    echo -n "请选择 [1-2] (5秒后自动选择1): "
    read -t 5 -n 1 cleanup_choice
    echo ""
    
    # 如果没有输入或输入为1，则执行清理
    if [[ -z "$cleanup_choice" || "$cleanup_choice" == "1" ]]; then
        print_info "正在清理临时文件..."
        
        # 清理构建目录
        if [[ -d "build" ]]; then
            rm -rf "build"
            print_info "已删除: build目录"
        fi
        
        # 清理spec文件
        if [[ -f "企业微信直播签到系统.spec" ]]; then
            rm -f "企业微信直播签到系统.spec"
            print_info "已删除: 企业微信直播签到系统.spec"
        fi
        
        # 清理临时钩子文件
        for file in memory_hook*.py fast_start_hook.py fix_macos_crash.py; do
            if [[ -f "$file" ]]; then
                rm -f "$file"
                print_info "已删除: $file"
            fi
        done
        
        print_success "清理完成! 可执行文件保留在 dist 目录中"
    else
        print_info "已取消清理"
    fi
    
    return 0
}

# 主函数
main() {
    # 检查依赖项
    check_dependencies || exit 1
    
    # 选择打包选项
    select_architecture
    select_package_mode
    select_memory_level
    select_debug_mode
    
    # 显示摘要并确认
    show_summary || exit 0
    
    # 执行打包
    do_packaging
    
    # 打包完成，给出提示
    if [ $? -eq 0 ]; then
        echo ""
        print_success "打包已完成!"
        echo ""
        echo "输出位置: $SCRIPT_DIR/dist/"
        
        if [[ "$SYSTEM" == "macOS" ]]; then
            echo "您可以通过以下方式运行应用:"
            echo "1. 直接打开 dist/企业微信直播签到系统.app"
            echo "2. 运行脚本 dist/启动企业微信直播签到系统.command"
            
            # 如果是通用二进制，给出提示
            if [[ "$TARGET_ARCH" == "universal" ]]; then
                echo ""
                echo "注意: 您创建了通用二进制应用，可以同时在Intel和Apple Silicon Mac上运行"
            fi
        elif [[ "$SYSTEM" == "Linux" ]]; then
            echo "您可以通过以下方式运行应用:"
            echo "1. 运行脚本 dist/启动企业微信直播签到系统.sh"
        fi
        
        # 询问是否进行打包后清理
        post_packaging_cleanup
    fi
}

# 执行主函数
main 