# 安装指引

嘴替.skill 是标准 Agent Skills 格式，整个仓库就是一个 skill 目录。

## Claude Code

```bash
# 安装到当前项目
mkdir -p .claude/skills
git clone https://github.com/SilentFleetKK/zuiti-skill .claude/skills/zuiti

# 或安装到全局（所有项目可用）
git clone https://github.com/SilentFleetKK/zuiti-skill ~/.claude/skills/zuiti
```

然后在 Claude Code 里，把难回的消息贴给它，或直接说"嘴替，[消息]"。

生成的专属嘴替默认写入 `./zuiti-personas/` 目录。

## OpenClaw

```bash
git clone https://github.com/SilentFleetKK/zuiti-skill ~/.openclaw/workspace/skills/zuiti
```

重启 session 即可使用。

## Codex / Cursor / 其他

用通用安装器自动识别 runtime：

```bash
npx skills add SilentFleetKK/zuiti-skill -a codex
# 或 -a cursor / -a claude-code 等
```

## 不想装？

懒得装就把 `SKILL.md` 全文复制、贴进对话框——纯文本 prompt，哪个模型都读得懂。

## 目录结构

```
zuiti-skill/
├── SKILL.md            # 嘴替本体，可直接安装使用
├── README.md
├── INSTALL.md
├── assets/             # README 视觉资产
├── promo/              # 传播卡片
├── tools/              # 传播素材生成脚本
├── personas/           # 专属嘴替模板
├── references/
│   ├── 分寸与边界.md
│   ├── 潜台词判断框架.md
│   ├── 风险评分卡.md
│   └── 个人口吻蒸馏模板.md
├── examples/           # 真实对话示例
│   ├── 职场.md
│   ├── 亲密关系.md
│   └── 对外沟通.md
├── COMMUNITY.md
├── CONTRIBUTING.md
├── ROADMAP.md
└── zuiti-personas/     # 生成的专属嘴替存放处（用户自己的）
```
