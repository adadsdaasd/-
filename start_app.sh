#!/bin/bash
# Digital Twin 启动脚本（Linux/Mac）
# 使用方法：修改下面的共享路径，然后运行 ./start_app.sh

# ============================================
# 配置：设置共享数据路径
# ============================================
# 方式1：使用网络挂载路径
export DIGITAL_TWIN_SHARED_DIR="/mnt/shared/digital_twin"

# 方式2：使用本地共享文件夹路径
# export DIGITAL_TWIN_SHARED_DIR="/opt/shared/DigitalTwin"

# ============================================
# 可选配置：设置本地配置路径（默认用户目录）
# ============================================
# export DIGITAL_TWIN_LOCAL_DIR="$HOME/DigitalTwin"

# ============================================
# 启动应用
# ============================================
echo "正在启动 Digital Twin..."
echo "共享数据路径: $DIGITAL_TWIN_SHARED_DIR"
echo ""

streamlit run app.py
