# Act-Two-Mobile

手机端调用 Runway Act-Two 的轻量工具。

## 当前阶段
第一阶段仅验证并跑通：
角色参考图 + 动作参考视频 → Runway Act-Two → 任务轮询 → 结果视频。

## 开发原则
- Android 手机优先
- 手机端只负责上传、参数、提交、状态、预览与下载
- Runway API Key 仅保存在后端环境变量
- 第一版不做账号、会员、支付、多模型、ComfyUI 控制、视频剪辑
- 每完成一个阶段同步更新开发日志与工作交接

## 当前技术方向
- Frontend: Vue 3 + Vite（后续）
- Backend: Python + FastAPI
- Database: SQLite（后续）
- Cloud generation: Runway API / Act-Two

## 当前任务
先完成最小 Act-Two API 调用验证，再进入完整 App 开发。
