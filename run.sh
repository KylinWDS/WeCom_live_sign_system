#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 设置日志文件
LOG_DIR="$HOME/.wecom_live_sign_system/logs"
LOG_FILE="$LOG_DIR/startup.log"
mkdir -p "$LOG_DIR"

# 打印带颜色的信息并记录到日志
print_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
    echo "[INFO] $1" >> "$LOG_FILE"
}

print_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
    echo "[WARN] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

# 错误处理函数
handle_error() {
    local exit_code=$?
    local line_number=$1
    local command=$2
    
    if [ $exit_code -ne 0 ]; then
        print_error "命令执行失败: $command"
        print_error "错误发生在第 $line_number 行"
        print_error "退出码: $exit_code"
        exit $exit_code
    fi
}

# 设置错误处理
set -e
trap 'handle_error ${LINENO} "$BASH_COMMAND"' ERR

# 检查必要的文件
check_required_files() {
    print_info "检查必要文件..."
    local files=("requirements.txt" "setup.py" "src/main.py")
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done
    print_info "所有必要文件检查通过"
}

# 比较版本号
compare_versions() {
    local version1=$1
    local version2=$2
    
    # 将版本号分割成数组
    IFS='.' read -ra ver1 <<< "$version1"
    IFS='.' read -ra ver2 <<< "$version2"
    
    # 比较主版本号
    if [ ${ver1[0]} -gt ${ver2[0]} ]; then
        return 0
    elif [ ${ver1[0]} -lt ${ver2[0]} ]; then
        return 1
    fi
    
    # 比较次版本号
    if [ ${ver1[1]} -ge ${ver2[1]} ]; then
        return 0
    fi
    
    return 1
}

# 检查Python版本
check_python_version() {
    local python_cmd=$1
    print_info "检查Python版本: $python_cmd"
    
    if ! command -v "$python_cmd" &> /dev/null; then
        print_error "命令不存在: $python_cmd"
        return 1
    fi
    
    local version_output
    version_output=$("$python_cmd" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>&1)
    if [ $? -ne 0 ]; then
        print_error "获取版本失败: $version_output"
        return 1
    fi
    
    print_info "检测到的Python版本: $version_output"
    
    if compare_versions "$version_output" "3.8"; then
        print_info "版本符合要求"
        echo "$version_output"
        return 0
    else
        print_error "版本过低: $version_output < 3.8"
        return 1
    fi
}

# 检查pip版本
check_pip_version() {
    local pip_cmd=$1
    print_info "检查pip版本: $pip_cmd"
    
    # 获取版本号
    local version_output
    version_output=$("$pip_cmd" --version | cut -d' ' -f2)
    if [ $? -ne 0 ]; then
        print_error "获取版本失败"
        return 1
    fi
    
    print_info "检测到的pip版本: $version_output"
    
    # 比较版本号
    if compare_versions "$version_output" "21.0"; then
        print_info "版本符合要求"
        echo "$version_output"
        return 0
    else
        print_error "版本过低: $version_output < 21.0"
        return 1
    fi
}

# 获取可用的Python命令
get_python_cmd() {
    print_info "开始检查Python命令..."
    
    # 先检查 python3 命令
    if command -v python3 &> /dev/null; then
        print_info "找到 python3 命令: $(command -v python3)"
        if check_python_version "python3"; then
            print_info "python3 命令版本符合要求"
            echo "python3"
            return 0
        else
            print_warn "python3 命令版本不符合要求"
        fi
    else
        print_warn "未找到 python3 命令"
    fi
    
    # 再检查 python 命令
    if command -v python &> /dev/null; then
        print_info "找到 python 命令: $(command -v python)"
        if check_python_version "python"; then
            print_info "python 命令版本符合要求"
            echo "python"
            return 0
        else
            print_warn "python 命令版本不符合要求"
        fi
    else
        print_warn "未找到 python 命令"
    fi
    
    print_error "未找到符合要求的Python版本（需要Python 3.8或更高版本）"
    return 1
}

# 获取可用的pip命令
get_pip_cmd() {
    local python_cmd=$1
    print_info "开始检查pip命令..."
    
    # 优先使用 python -m pip
    print_info "尝试使用 $python_cmd -m pip"
    if "$python_cmd" -m pip --version &> /dev/null; then
        if check_pip_version "$python_cmd -m pip"; then
            print_info "$python_cmd -m pip 命令版本符合要求"
            echo "$python_cmd -m pip"
            return 0
        fi
    fi
    
    # 再检查 pip3 命令
    if command -v pip3 &> /dev/null; then
        print_info "找到 pip3 命令"
        if check_pip_version "pip3"; then
            print_info "pip3 命令版本符合要求"
            echo "pip3"
            return 0
        fi
    fi
    
    # 最后检查 pip 命令
    if command -v pip &> /dev/null; then
        print_info "找到 pip 命令"
        if check_pip_version "pip"; then
            print_info "pip 命令版本符合要求"
            echo "pip"
            return 0
        fi
    fi
    
    print_error "未找到符合要求的pip版本（需要pip 21.0或更高版本）"
    return 1
}

# 检查并创建虚拟环境
setup_venv() {
    local python_cmd=$1
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        "$python_cmd" -m venv venv
        if [ $? -ne 0 ]; then
            print_error "创建虚拟环境失败"
            return 1
        fi
        print_info "虚拟环境创建成功"
    else
        print_info "虚拟环境已存在"
    fi
    return 0
}

# 激活虚拟环境
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        if [ $? -ne 0 ]; then
            print_error "激活虚拟环境失败"
            return 1
        fi
        print_info "虚拟环境已激活"
        return 0
    else
        print_error "虚拟环境激活脚本不存在"
        return 1
    fi
}

# 检查并安装依赖
install_dependencies() {
    local pip_cmd=$1
    print_info "检查并安装依赖..."
    if [[ "$pip_cmd" == *"python"* ]]; then
        eval "$pip_cmd install -r requirements.txt"
    else
        "$pip_cmd" install -r requirements.txt
    fi
    if [ $? -ne 0 ]; then
        print_error "安装依赖失败"
        return 1
    fi
    print_info "依赖安装完成"
    return 0
}

# 检查并安装项目包
install_package() {
    local pip_cmd=$1
    print_info "安装项目包..."
    if [[ "$pip_cmd" == *"python"* ]]; then
        eval "$pip_cmd install -e ."
    else
        "$pip_cmd" install -e .
    fi
    if [ $? -ne 0 ]; then
        print_error "安装项目包失败"
        return 1
    fi
    print_info "项目包安装完成"
    return 0
}

# 检查是否在虚拟环境中
check_venv() {
    if [ -n "$VIRTUAL_ENV" ]; then
        print_warn "检测到当前在虚拟环境中: $VIRTUAL_ENV"
        print_info "正在退出虚拟环境..."
        deactivate
        if [ $? -eq 0 ]; then
            print_info "已成功退出虚拟环境"
            return 0
        else
            print_error "退出虚拟环境失败"
            return 1
        fi
    else
        print_info "当前不在虚拟环境中"
        return 0
    fi
}

# 主函数
main() {
    print_info "开始启动流程..."
    print_info "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # 检查是否在虚拟环境中
    check_venv
    if [ $? -ne 0 ]; then
        print_error "虚拟环境检查失败"
        exit 1
    fi
    
    # 检查必要文件
    check_required_files
    if [ $? -ne 0 ]; then
        print_error "必要文件检查失败"
        exit 1
    fi
    
    # 获取系统Python命令
    PYTHON_CMD=$(get_python_cmd)
    if [ $? -ne 0 ]; then
        print_error "未找到合适的Python命令"
        exit 1
    fi
    
    # 设置虚拟环境
    setup_venv "$PYTHON_CMD"
    if [ $? -ne 0 ]; then
        print_error "虚拟环境设置失败"
        exit 1
    fi
    
    # 激活虚拟环境
    activate_venv
    if [ $? -ne 0 ]; then
        print_error "虚拟环境激活失败"
        exit 1
    fi
    
    # 在虚拟环境中重新获取Python命令
    VENV_PYTHON="python"
    
    # 在虚拟环境中使用python -m pip
    VENV_PIP="$VENV_PYTHON -m pip"
    
    # 安装依赖
    install_dependencies "$VENV_PIP"
    if [ $? -ne 0 ]; then
        print_error "依赖安装失败"
        exit 1
    fi
    
    # 安装项目包
    install_package "$VENV_PIP"
    if [ $? -ne 0 ]; then
        print_error "项目包安装失败"
        exit 1
    fi
    
    # 运行环境检查
    print_info "运行环境检查..."
    "$VENV_PYTHON" -m tools.env_checker
    if [ $? -ne 0 ]; then
        print_error "环境检查失败"
        exit 1
    fi
    
    # 处理命令行参数
    if [ $# -eq 0 ]; then
         # 如果没有参数，启动主程序
        print_info "启动主程序..."
        wecom-live-sign
    else
        # 根据参数执行不同的命令
        case "$1" in
            "help"|"-h"|"--help")
                show_help
                exit 0
                ;;
            "start")
                print_info "启动主程序..."
                wecom-live-sign
                ;;
            "check")
                print_info "运行环境检查..."
                wecom-live-sign-check
                ;;
            "reset")
                print_info "运行管理员重置工具..."
                wecom-admin-reset
                ;;
            "test")
                print_info "运行测试..."
                wecom-live-sign-test
                ;;
            "clean")
                print_info "清理环境..."
                wecom-live-sign-clean
                ;;
            "db")
                print_info "运行数据库管理工具..."
                wecom-live-sign-db
                ;;
            "log")
                print_info "查看日志..."
                wecom-live-sign-log
                ;;
            "backup")
                print_info "运行备份工具..."
                wecom-live-sign-backup
                ;;
            "update")
                print_info "运行更新工具..."
                wecom-live-sign-update
                ;;
            "check-db")
                print_info "检查数据库..."
                wecom-live-sign-check-db
                ;;
            *)
                print_error "未知的命令: $1"
                show_help
                exit 1
                ;;
        esac
    fi
    
    print_info "启动成功！"
    print_info "日志文件位置: $LOG_FILE"
}

# 显示帮助信息
show_help() {
    print_info "企业微信直播签到系统启动脚本"
    print_info "用法: ./run.sh [命令]"
    print_info ""
    print_info "可用命令:"
    print_info "  start     - 启动主程序"
    print_info "  check     - 检查环境"
    print_info "  reset     - 重置管理员"
    print_info "  test      - 运行测试"
    print_info "  clean     - 清理环境"
    print_info "  db        - 数据库管理"
    print_info "  log       - 查看日志"
    print_info "  backup    - 备份数据"
    print_info "  update    - 更新系统"
    print_info "  check-db  - 检查数据库"
    print_info "  help      - 显示帮助信息"
    print_info ""
    print_info "示例:"
    print_info "  ./run.sh [start]    # 启动主程序"
    print_info "  ./run.sh check    # 检查环境"
    print_info "  ./run.sh help     # 显示帮助信息"
}

# 执行主函数，并传递所有命令行参数
main "$@"

# 如果所有步骤都成功完成
print_info "所有步骤执行完成"
exit 0 