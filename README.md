# Act-Two-Mobile

一个以 Android 手机为优先入口的 Runway Act-Two 轻量控制器。

## 已实现
- 手机端上传角色参考图
- 手机端上传动作参考视频
- Act-Two 参数：表情强度、身体控制、输出比例、Seed
- FastAPI 后端安全持有 Runway API Key
- 素材先上传为 Runway ephemeral asset，再创建 Character Performance 任务
- 前端轮询任务状态
- 生成完成后在线播放与下载结果

## 技术栈
- Frontend: Vue 3 + Vite
- Backend: Python + FastAPI
- Runway SDK: runwayml
- Model: act_two

## 本地运行

### 1. 后端
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

在 `.env` 中填写：
```env
RUNWAYML_API_SECRET=key_xxx
```

启动：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 前端
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

电脑与 Android 手机处于同一局域网时，可通过电脑局域网 IP 访问 Vite 页面。

## 安全
- API Key 只允许存在于后端 `.env`
- `.env` 已加入 `.gitignore`
- 前端不会接触 Runway API Key

## 当前限制
真实生成仍需要在运行环境中配置用户自己的 Runway API Key 与可用 API Credits。
