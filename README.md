# 巴黎与凡尔赛旅行计划

按日查看行程、地图、交通、景点介绍和参观专题。保留现有 14 天安排，同时提供可分发的完整单文件 HTML。

## 平时怎样更新

1. 修改 `data/plan.json` 中的行程内容；版式和交互分别在 `templates/` 与页面生成器中维护。
2. 在本地构建并检查，或向 `master` 提交 Pull Request，让 Actions 检查。
3. 修改推送或合并到 `master` 后，GitHub Actions 自动重新生成网站并部署 GitHub Pages。

自动更新指根据已提交的行程和路线缓存重新生成网页，不会自行改动景点、票务、营业时间或在线原稿。需要调整这些资料时，先更新并核实源数据。

## 本地构建

使用 Python 3.13 或更新版本；构建只用 Python 标准库，不需要安装第三方 Python 包，也不需要联网抓取路线。

```sh
python scripts/build_pages.py
```

生成两个入口：

| 位置 | 用途 |
| --- | --- |
| `web/current/index.html` | 原有本地入口，继续保留 |
| `dist/index.html` | GitHub Pages 发布入口，部署时直接作为网站根目录 |
| `dist/review-plan.html` | 同行计划总表 |
| `dist/paris-companion-plan.html` | 完整单文件，可下载转发，包含每日详情和专题 |

完整检查：

```sh
python -m unittest discover -s tests -v
python scripts/validate_site.py dist --check-js
```

`--check-js` 需要 Node.js 20 或更新版本，用于检查内嵌脚本语法；不运行这个选项时无需 Node.js。GitHub 托管的 Ubuntu runner 已提供 Node.js。

检查涵盖页面、景点锚点、本地资源、仓库子路径、完整单文件的内部导航，以及先前地图组件加载问题的回归检查。链接和脚本检查不能代替浏览器中的交互实测。

地图街道底图和外部官网需要联网；每日点位、路线、卢浮宫馆图和文字说明包含在构建结果中。待办勾选状态保存在各自浏览器中，不会同步到仓库或其他同行者。

## GitHub Pages 首次设置

项目尚未绑定远程仓库。选择目标 GitHub 仓库后：

1. 将此项目推送到该仓库的 `master` 分支，建议同时将 `master` 设为默认分支。
2. 打开仓库 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
3. 在 **Actions** 中运行 **Build and deploy GitHub Pages**，或向 `master` 再推送一次修改。
4. 成功后，在工作流的部署记录或仓库 Pages 设置中打开网站地址。

不需要手工提交生成的 HTML，也不需要维护 `gh-pages` 分支或另外保存部署 token。工作流使用 GitHub 提供的 `GITHUB_TOKEN` 和 Pages OIDC 权限。

网站兼容 `https://用户名.github.io/仓库名/` 这类项目路径，所有站内页面及资源均使用相对链接；不需要为仓库名修改页面地址。

### 自动部署流程

配置文件：`.github/workflows/pages.yml`。

| 触发方式 | 行为 |
| --- | --- |
| Push 到 `master` | 测试 → 构建 → 检查 → 上传 `dist/` → 部署 |
| 面向 `master` 的 Pull Request | 测试、构建和检查，不部署 |
| Actions 中手动运行 | 检查选定分支；只有 `master` 可以部署 |

构建任务只有代码读取权限；仅部署任务获得 `pages: write` 和 `id-token: write`。部署使用 `github-pages` 环境。同一分支的发布串行执行，避免同时覆盖线上内容。

发布目录只包含生成的网页及其资源，不包含本地备份、导出历史、源码目录或完整的行程数据快照。`revision.json` 记录相对入口、版本及可用的提交号，不包含构建机器的绝对目录。

遇到首次部署失败，先确认 Pages 的 Source 已选择 GitHub Actions、Actions 已启用，且 `github-pages` 环境允许 `master` 部署。其余构建或链接错误可在工作流日志中查看；检查不通过时不会开始部署。

官方参考：[使用自定义工作流部署 GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 项目结构

```text
data/                    当前行程、路线缓存、核对资料
assets/                  卢浮宫官方馆图、原稿图片与 PDF
templates/               版式、地图、待办和馆内交互
vendor/                  已保存的固定版本地图组件
build_daily.py           当前网站生成器
portable_bundle.py       完整单文件生成器
louvre_indoor.py         卢浮宫馆内路线
marais_shops.py          玛黑区商铺介绍
exhibition_review.py     展览讨论内容
scripts/                 发布构建与检查入口
tests/                   发布检查的回归测试
.github/workflows/       GitHub Actions 自动部署
docs/history/            早期讨论稿与原更新日志
review/                  已保存的页面核对截图
archive/                 本地备份（不提交）
exports/                 本地分发副本（不提交）
web/current/             本地生成网站（不提交）
dist/                    GitHub Pages 发布产物（不提交）
```

`prepare_plan.py`、`density_v2.py`、`render_review.py` 和 `render_review_v2.py` 是早期草稿流程，保留供追溯。日常更新和自动部署只运行当前构建入口；**不要运行 `prepare_plan.py`**，它可能用旧稿覆盖已经确认的 `data/plan.json`。

现有资料中的场馆底图、图片和外部资源保留各自的版权和来源说明。
