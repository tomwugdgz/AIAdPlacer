# GitHub 上传指南 — AIAdPlacer pDOOH 项目

> 一步一步教你把代码推到 GitHub

---

## 方法一：本机手动推送（最简单，推荐）

### 第一步：打开本机终端

**PowerShell（推荐）：**
```powershell
cd D:\Mirofish\AIAdPlacer
git status
```

**或者 CMD：**
```cmd
cd /d D:\Mirofish\AIAdPlacer
git status
```

### 第二步：查看待推送的提交

```bash
git log --oneline -5
```

你应该能看到类似这样的输出：
```
be62005 feat: pDOOH 真实数据对接 + 详细 README
d48ac3a fix: 修复Windows GBK编码问题
...
```

### 第三步：推送（会自动弹窗输入账号）

```bash
git push origin master
```

**如果弹窗要求输入账号密码：**
- **用户名**：你的 GitHub 用户名
- **密码**：填写 **GitHub Personal Access Token**（⚠️ 不是GitHub登录密码）

### 如何获取 GitHub Token？

1. 打开：https://github.com/settings/tokens
2. 点右上角 **"Generate new token (classic)"**
3. 填写：
   - **Note**：`AIAdPlacer push`
   - **Expiration**：选 `90 days`
   - **勾选权限**：只勾 `repo` 就够了
4. 拉到最下面点 **"Generate token"**
5. **复制生成的Token**（形如 `ghp_xxxxxxxxxxxx`）→ 这就是"密码"

### 第四步：验证推送成功

```bash
git log --oneline origin/master..master
# 如果没有输出，说明已经同步
```

打开：https://github.com/tomwugdgz/AIAdPlacer — 应该能看到最新提交。

---

## 方法二：提供 Token，让 AI 帮你推送

如果你不想自己弄，把 **GitHub Token** 告诉我，我来执行：

```bash
git push https://<你的用户名>:<EMAIL_REMOVED> master
```

⚠️ **安全提示**：Token 有推送权限，只通过私聊发给我，不要公开。

---

## 方法三：先验证后端，再推送（稳妥派）

### 第一步：启动后端

```bash
cd D:\Mirofish\AIAdPlacer\backend
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 5002
```

如果看到类似这样的输出，说明启动成功：
```
INFO:     Uvicorn running on http://0.0.0.0:5002 (Press CTRL+C to quit)
🚀 AIAdPlacer API 启动成功！
📊 数据库: ai_adplacer @ 127.0.0.1:5432
🔗 文档: http://127.0.0.1:5002/docs
📊 pDOOH API: http://127.0.0.1:5002/api/v2/pdooh/screens
```

### 第二步：测试 API

**浏览器打开：**
```
http://127.0.0.1:5002/api/v2/pdooh/screens?limit=5
```

应该能看到 JSON 格式的屏数据。

**或者命令行测试：**
```bash
curl http://127.0.0.1:5002/api/v2/pdooh/screens?limit=5
```

### 第三步：如果 API 正常，再推送

```bash
cd ..
git push origin master
```

---

## 常见问题

### Q1: `git push` 没反应，卡住了？

**原因**：凭据管理器在等输入，但沙箱环境无法显示弹窗。

**解决**：
- 在本机终端运行（不在 WorkBuddy 里运行）
- 或者提供 Token，让 AI 用 `git push https://<token>@github.com/...` 方式推送

### Q2: `fatal: could not read Username`

**原因**：没有存储 GitHub 凭据。

**解决**：按方法一的步骤获取 Token，然后运行：
```bash
git config --global credential.helper wincred
git push origin master
# 输入用户名 + Token（当作密码）
```

### Q3: 我想推送到新的仓库，不是 `tomwugdgz/AIAdPlacer`？

```bash
# 查看当前远程
git remote -v

# 修改为新仓库
git remote set-url origin https://github.com/<你的用户名>/<新仓库名>.git

# 推送
git push -u origin master
```

### Q4: 我想先建一个 `.gitignore`，再推送？

```bash
# 创建 .gitignore
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
.env
*.log
chroma_db/
*.db-shm
*.db-wal
node_modules/
dist/
build/
EOF

# 提交
git add .gitignore
git commit -m "chore: 添加 .gitignore"
git push origin master
```

---

## 推送完成后，检查清单

- [ ] GitHub 仓库能看到最新提交
- [ ] `README.md` 正确显示
- [ ] `docs/schema.sql` 能打开
- [ ] `demo.html` 能在本地运行（需要启动后端）
- [ ] 后端 API 文档能访问：http://127.0.0.1:5002/docs

---

**现在选择一种方法，开始推送吧！** 🚀
