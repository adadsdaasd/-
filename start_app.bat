@echo off
REM Digital Twin 启动脚本（Windows）
REM 使用方法：修改下面的共享路径，然后双击运行

REM ============================================
REM 配置：设置共享数据路径
REM ============================================
REM 方式1：使用网络驱动器路径
set DIGITAL_TWIN_SHARED_DIR=\\server\shared\digital_twin

REM 方式2：使用本地共享文件夹路径
REM set DIGITAL_TWIN_SHARED_DIR=C:\SharedData\DigitalTwin

REM ============================================
REM 可选配置：设置本地配置路径（默认用户目录）
REM ============================================
REM set DIGITAL_TWIN_LOCAL_DIR=%USERPROFILE%\DigitalTwin

REM ============================================
REM 启动应用
REM ============================================
echo 正在启动 Digital Twin...
echo 共享数据路径: %DIGITAL_TWIN_SHARED_DIR%
echo.

streamlit run app.py

pause
