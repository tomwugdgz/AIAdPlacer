"""
pDOOH 服务端安装验证脚本
用于验证安装是否成功、依赖是否完整、服务是否能正常启动

使用方式：
    python test_installation.py
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

# 颜色代码（Windows 需要 colorama，这里用简单版本）
class Color:
    GREEN = "\033[92m" if sys.platform != "win32" else ""
    RED = "\033[91m" if sys.platform != "win32" else ""
    YELLOW = "\033[93m" if sys.platform != "win32" else ""
    RESET = "\033[0m" if sys.platform != "win32" else ""

def print_success(msg: str):
    print(f"{Color.GREEN}[✓] {msg}{Color.RESET}")

def print_error(msg: str):
    print(f"{Color.RED}[✗] {msg}{Color.RESET}")

def print_warning(msg: str):
    print(f"{Color.YELLOW}[!] {msg}{Color.RESET}")

def print_info(msg: str):
    print(f"    {msg}")

def check_python_version():
    """检查 Python 版本"""
    print("\n[1/6] 检查 Python 版本...")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print_error(f"Python 版本过低: {major}.{minor}")
        print_info("需要 Python 3.8 或更高版本")
        return False
    print_success(f"Python 版本检查通过: {major}.{minor}")
    return True

def check_virtual_env():
    """检查是否在虚拟环境中"""
    print("\n[2/6] 检查虚拟环境...")
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        print_success("已在虚拟环境中")
        return True
    else:
        print_warning("未在虚拟环境中（建议使用虚拟环境）")
        return False

def check_dependencies():
    """检查依赖包是否安装"""
    print("\n[3/6] 检查 Python 依赖包...")
    
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("httpx", "httpx"),
        ("pydantic_settings", "pydantic-settings"),
        ("python_dotenv", "python-dotenv"),
    ]
    
    optional_packages = [
        ("langchain", "langchain"),
        ("langgraph", "langgraph"),
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
        ("openai", "openai"),
        ("redis", "redis"),
    ]
    
    all_ok = True
    
    # 检查必需包
    print_info("检查必需包...")
    for package_name, import_name in required_packages:
        if importlib.util.find_spec(import_name) is not None:
            print_success(f"  {package_name:25s} - 已安装")
        else:
            print_error(f"  {package_name:25s} - 未安装")
            all_ok = False
    
    # 检查可选包
    print_info("检查可选包...")
    for package_name, import_name in optional_packages:
        if importlib.util.find_spec(import_name) is not None:
            print_success(f"  {package_name:25s} - 已安装")
        else:
            print_warning(f"  {package_name:25s} - 未安装（可选）")
    
    return all_ok

def check_env_file():
    """检查 .env 文件是否存在"""
    print("\n[4/6] 检查环境配置文件...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_success(".env 文件已存在")
        return True
    else:
        print_warning(".env 文件不存在")
        if env_example.exists():
            print_info("提示: 运行以下命令创建 .env 文件:")
            print_info("  copy .env.example .env  (Windows)")
            print_info("  cp .env.example .env      (Linux/Mac)")
        return False

def check_database_files():
    """检查数据库文件是否存在"""
    print("\n[5/6] 检查媒体资源数据库文件...")
    
    db_files = [
        "亲邻单元门智能框架.db",
        "亲邻门禁全国点位.db",
        "亲邻广州道闸.db",
        "亲邻商场LED.db",
    ]
    
    found = 0
    for db_file in db_files:
        if Path(db_file).exists():
            print_success(f"  {db_file} - 已找到")
            found += 1
        else:
            print_warning(f"  {db_file} - 未找到")
    
    if found == 0:
        print_info("提示: 请将数据库文件放到 backend/ 目录")
        return False
    else:
        print_info(f"找到 {found}/{len(db_files)} 个数据库文件")
        return True

def check_scripts():
    """检查启动脚本是否存在"""
    print("\n[6/6] 检查启动脚本...")
    
    scripts = [
        ("install.bat", "Windows 安装脚本"),
        ("start_all.bat", "Windows 启动脚本"),
        ("run_all_agents.py", "主启动脚本"),
        ("requirements.txt", "依赖清单"),
        (".env.example", "环境变量示例"),
    ]
    
    all_ok = True
    for script, desc in scripts:
        if Path(script).exists():
            print_success(f"  {script:25s} - 已存在 ({desc})")
        else:
            print_error(f"  {script:25s} - 不存在")
            all_ok = False
    
    return all_ok

def main():
    """主函数"""
    print("=" * 60)
    print("  pDOOH 服务端安装验证")
    print("=" * 60)
    
    results = []
    
    # 1. 检查 Python 版本
    results.append(("Python 版本", check_python_version()))
    
    # 2. 检查虚拟环境
    results.append(("虚拟环境", check_virtual_env()))
    
    # 3. 检查依赖包
    results.append(("依赖包", check_dependencies()))
    
    # 4. 检查 .env 文件
    results.append(("环境配置", check_env_file()))
    
    # 5. 检查数据库文件
    results.append(("数据库文件", check_database_files()))
    
    # 6. 检查脚本
    results.append(("启动脚本", check_scripts()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("  验证总结")
    print("=" * 60)
    
    for name, ok in results:
        if ok:
            print_success(f"{name:20s} - 通过")
        else:
            print_error(f"{name:20s} - 有问题")
    
    print("\n" + "=" * 60)
    
    all_passed = all(ok for _, ok in results)
    if all_passed:
        print_success("所有检查通过！可以运行 start_all.bat 启动服务")
    else:
        print_warning("部分检查未通过，请根据上述提示进行修复")
        print_info("详细安装说明请查看 README.md")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
