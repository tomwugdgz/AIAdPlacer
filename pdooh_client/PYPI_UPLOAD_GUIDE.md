# PyPI 上传指南

## 方式一：交互式上传（推荐）

### 步骤：

1. **打开命令行**（Win + R → 输入 `cmd` → 回车）

2. **进入项目目录**：
   ```bash
   cd D:\Mirofish\AIAdPlacer\pdooh_client
   ```

3. **执行上传命令**：
   ```bash
   python -m twine upload dist/*
   ```

4. **输入凭据**：
   - Username: `dukcowlf`
   - Password: `Karen2tom` ← 输入时不会显示，直接输入后回车

5. **等待上传完成**（通常 10-30 秒）

6. **验证上传成功**：
   - 访问：https://pypi.org/project/pdooh-client/
   - 安装测试：`pip install pdooh-client`

---

## 方式二：使用 .pypirc 配置文件

### 步骤：

1. **创建配置文件** `%APPDATA%\pip\pypirc`：
   ```ini
   [distutils]
   index-servers =
       pypi
   
   [pypi]
   username = dukcowlf
   password = Karen2tom
   ```

2. **上传**：
   ```bash
   python -m twine upload --repository pypi dist/*
   ```

---

## 方式三：使用环境变量

### 步骤：

1. **设置环境变量**：
   ```bash
   set TWINE_USERNAME=dukcowlf
   set TWINE_PASSWORD=Karen2tom
   ```

2. **上传**：
   ```bash
   python -m twine upload dist/*
   ```

---

## 常见问题

### Q1: 上传失败 - 401 Unauthorized
**原因**：用户名或密码错误
**解决**：
1. 访问 https://pypi.org/account/login/ 验证用户名密码
2. 如果忘记密码，点击 "Forgot password?" 重置

### Q2: 上传失败 - 403 Forbidden
**原因**：包名已被占用，或者没有上传权限
**解决**：
1. 访问 https://pypi.org/project/pdooh-client/ 检查包名是否存在
2. 如果存在但不是你的，需要改包名（修改 `pyproject.toml` 中的 `name` 字段）

### Q3: 上传失败 - 400 Bad Request
**原因**：包版本已存在
**解决**：
1. 修改版本号（修改 `pdooh_client/__init__.py` 中的 `__version__`）
2. 重新构建：`python -m build`
3. 重新上传：`python -m twine upload dist/*`

---

## 验证安装

上传成功后，任何人都可以安装：

```bash
# 安装最新版本
pip install pdooh-client

# 安装指定版本
pip install pdooh-client==1.0.0

# 升级到最新版本
pip install --upgrade pdooh-client
```

---

## 使用示例

```python
from pdooh_client import PDOOHClient

# 创建客户端
client = PDOOHClient(base_url="http://47.253.159.62")

# 查询点位
points = client.mcp.query_access_points(city="广州", media_type="门禁")

# 计算 ROI
roi = client.roi.calculate_roi(
    brand_name="黑人牙膏",
    product_name="牙膏",
    city="广州",
    placement_count=10
)
```

---

## 下一步

上传成功后：
1. ✅ 更新 GitHub/码云/GitCode 的 README.md，添加 PyPI 安装说明
2. ✅ 写一篇使用教程或博客
3. ✅ 分享给社区（Reddit, Twitter, 技术论坛）

---

## 需要帮助？

如果遇到问题，可以：
1. 查看 twine 错误日志
2. 访问 PyPI 帮助文档：https://twine.readthedocs.io/
3. 向我求助（截图错误信息）
