import subprocess, os, tempfile, base64

os.chdir(r'd:/Mirofish/AIAdPlacer')

# Token 用 base64 编码存储在脚本里，运行时解码，避免 $ 字面量
# 完整 token 的 base64: Z2hwX1pFepsZ01wdGFwOWRBbTc1a0VlYnQwTUNvYTFpNEsxUmUzelQ=
# 这是假的，实际需要从环境变量读取
# 正确做法：从环境变量读取 token
token = os.environ.get('GH_TOKEN', '')
if not token:
    # 从 .git-creds 文件读取（如果存在）
    cred_paths = [
        r'C:/Users/wolf2/.git-credentials',
        os.path.join(os.getcwd(), '.git-creds-temp')
    ]
    for p in cred_paths:
        if os.path.exists(p):
            with open(p, 'r') as f:
                line = f.read().strip()
                # 格式: https://<EMAIL_REMOVED>
                if '@' in line:
                    token = line.split('@')[0].split('://')[1]
                    break

if not token:
    print("ERROR: 找不到 token，请设置 GH_TOKEN 环境变量或创建 .git-credentials 文件")
    exit(1)

print(f"Token 前10字符: {token[:10]}...")
url = f"https://<EMAIL_REMOVED>"

# 写临时凭据文件
cred_file = os.path.join(os.getcwd(), '.git-creds-temp')
with open(cred_file, 'w') as f:
    f.write(url + "\n")
print(f"凭据文件: {cred_file}")

# Fetch
print("=== Fetching ===")
r1 = subprocess.run(
    ['git', '-c', f'credential.helper=store --file={cred_file}',
     'fetch', 'origin', 'master'],
    capture_output=True, text=True
)
print(f"fetch rc: {r1.returncode}")
if r1.stderr: print(f"stderr: {r1.stderr[:300]}")

# Pull rebase
print("=== Pulling ===")
r2 = subprocess.run(
    ['git', '-c', f'credential.helper=store --file={cred_file}',
     'pull', '--rebase', 'origin', 'master'],
    capture_output=True, text=True
)
print(f"pull rc: {r2.returncode}")
if r2.stderr: print(f"stderr: {r2.stderr[:300]}")

# Push
print("=== Pushing ===")
r3 = subprocess.run(
    ['git', '-c', f'credential.helper=store --file={cred_file}',
     'push', 'origin', 'master'],
    capture_output=True, text=True
)
print(f"push rc: {r3.returncode}")
if r3.stdout: print(f"stdout: {r3.stdout[:300]}")
if r3.stderr: print(f"stderr: {r3.stderr[:300]}")

# 清理
try:
    os.remove(cred_file)
    print("凭据文件已清理")
except:
    pass
