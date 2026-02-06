# 🌐 公网部署快速参考

## 问题：为什么其他设备无法访问 localhost？

**原因**：
- `localhost` 只能在本机访问
- 其他设备无法访问您的 `localhost`
- 需要公网 IP 或内网穿透

**解决方案**：使用免费的公网部署服务

---

## 🚀 推荐方案：Streamlit Cloud（完全免费）

### 5分钟快速部署

1. **上传代码到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/digital-twin-app.git
   git push -u origin main
   ```

2. **部署到 Streamlit Cloud**
   - 访问：https://streamlit.io/cloud
   - 使用 GitHub 登录
   - 选择仓库 → Deploy
   - 获取公网链接：`https://your-app.streamlit.app`

3. **完成！**
   - ✅ 公网链接可以分享给任何人
   - ✅ 随时随地访问
   - ✅ 完全免费

---

## 🔧 临时方案：ngrok（快速测试）

1. **注册并下载 ngrok**
   - https://ngrok.com/

2. **启动应用和 ngrok**
   ```bash
   # 窗口1：启动应用
   streamlit run app.py
   
   # 窗口2：启动 ngrok
   ngrok http 8501
   ```

3. **获取公网链接**
   - ngrok 会显示：`https://abc123.ngrok-free.app`
   - 这个链接可以分享

---

## 📚 详细文档

- **完整指南**：`免费公网部署指南.md`
- **Streamlit Cloud 步骤**：`setup_streamlit_cloud.md`
- **快速部署**：`快速部署.md`

---

## ✅ 部署后

**您将获得**：
- 公网链接（如：`https://your-app.streamlit.app`）
- 任何人都可以通过链接访问
- 不需要在同一局域网

**不再需要**：
- ❌ localhost（只能本机访问）
- ❌ 同一 Wi-Fi
- ❌ 端口转发配置

---

**立即开始**：查看 `快速部署.md` 获取详细步骤！
