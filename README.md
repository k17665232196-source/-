# 枙柚 · 知友AI 🌸

> 你专属的AI好朋友，有记忆、有情绪、有温度。

## 项目结构

```
zhiyou-ai/
├── api/
│   ├── chat.py          # 主聊天接口（Vercel Serverless）
│   ├── image.py         # 未来：AI图片接口
│   └── voice.py         # 未来：语音接口
├── data/
│   ├── role.md          # 枙柚的角色圣经（灵魂）
│   ├── memory.json      # 长期记忆
│   ├── relationship.json# 关系系统
│   ├── emotion.json     # 情绪状态
│   └── chat_history.json# 聊天记录（可选）
├── public/
│   ├── avatar.jpg       # 枙柚头像
│   └── background.jpg   # 聊天背景
├── css/style.css        # 全部样式
├── js/app.js            # 主交互逻辑
├── index.html           # 唯一主页面
├── vercel.json          # Vercel 配置
├── requirements.txt     # Python 依赖
└── .env.example         # 环境变量示例
```

## 部署步骤

### 1. 克隆项目
```bash
git clone https://github.com/你的用户名/zhiyou-ai.git
cd zhiyou-ai
```

### 2. 添加你的头像和背景图
把图片放到 `public/` 文件夹：
- `avatar.jpg` — 枙柚的头像
- `background.jpg` — 聊天背景（可选）

### 3. 推送到 GitHub
```bash
git add .
git commit -m "初始化知友AI"
git push origin main
```

### 4. 部署到 Vercel
1. 去 [vercel.com](https://vercel.com) 导入你的 GitHub 仓库
2. 在 Vercel 项目设置 → Environment Variables 里添加：
   - `ANTHROPIC_API_KEY` = 你的 API 密钥
3. 点击 Deploy ✅

### 5. 获取 API Key
去 [console.anthropic.com](https://console.anthropic.com/) 创建账号并获取密钥。

## 本地测试

```bash
pip install anthropic
cp .env.example .env
# 编辑 .env 填入真实密钥
vercel dev
```

## 自定义枙柚

编辑 `data/role.md` 来改变枙柚的性格、说话方式和价值观。
这是她的"灵魂"，可以完全按你的喜好定制 💕
