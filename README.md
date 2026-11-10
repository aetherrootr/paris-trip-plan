# 巴黎与凡尔赛旅行计划

按日查看行程、地图、交通、景点介绍和参观专题。保留现有 14 天安排，同时提供可分发的完整单文件 HTML。

## 平时怎样更新

1. 修改 `data/plan.json` 中的行程内容；版式和交互分别在 `templates/` 与页面生成器中维护。
2. 在本地构建并检查，或向 `master` 提交 Pull Request，让 Actions 检查。
3. 修改推送或合并到 `master` 后，GitHub Actions 自动重新生成网站；启用 Pages 后自动发布。

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
| `dist/index.html` | 静态站点入口，后续可交给带访问控制的托管服务 |
| `dist/review-plan.html` | 同行计划总表 |
| `dist/paris-companion-plan.html` | 完整单文件，可下载转发，包含每日详情和专题 |

完整检查：

```sh
python -m unittest discover -s tests -v
node --test tests/site-ui.test.cjs
python scripts/validate_site.py dist --check-js
```

`--check-js` 需要 Node.js 20 或更新版本，用于检查内嵌脚本语法；不运行这个选项时无需 Node.js。GitHub 托管的 Ubuntu runner 已提供 Node.js。

检查涵盖页面、景点锚点、本地资源、仓库子路径、完整单文件的内部导航、手机导航展开收起，以及先前地图组件加载问题的回归检查。链接和脚本检查不能代替浏览器中的交互实测。

地图街道底图和外部官网需要联网；每日点位、路线、卢浮宫馆图和文字说明包含在构建结果中。待办勾选状态保存在各自浏览器中，不会同步到仓库或其他同行者。

## 原生 GitHub Pages

远程仓库：[aetherrootr/paris-trip-plan](https://github.com/aetherrootr/paris-trip-plan)。**源码和网站均为公开**，使用原生 GitHub Pages，不启用 Cloudflare Access 登录。票券、二维码、密码和其他私有凭证在其他地方管理，不提交到仓库，也不加入 `data/`、`assets/` 或页面内容。

默认站点地址为 [aetherrootr.github.io/paris-trip-plan](https://aetherrootr.github.io/paris-trip-plan/)。

### 首次启用

公开仓库可以使用 GitHub Free 的 Pages，不需要为此升级套餐。首次设置：

1. 在仓库 **Settings → Pages → Source** 选择 **GitHub Actions**。
2. 在 **Settings → Secrets and variables → Actions → Variables** 添加 `PAGES_DEPLOY_ENABLED`，值为 `true`。
3. 在 **Actions** 手动运行 **Build and deploy GitHub Pages**，或向 `master` 推送修改。
4. 部署成功后，之后每次更新 `master` 都会自动发布。

发布开关未启用时，构建与下载产物照常生成，部署任务跳过。不需要手工提交生成的 HTML，也不需要 `gh-pages` 分支。

### 获取自动更新的下载版本

1. 修改推送或合并到 `master`，或在 **Actions** 手动运行 **Build and deploy GitHub Pages**。
2. 在成功的工作流运行页面下方找到 **Artifacts**。
3. 下载 `paris-trip-offline`：解压后用浏览器打开完整单文件 HTML。
4. 需要全部独立页面时，下载 `paris-trip-site`。

产物保留 30 天，GitHub 的产物下载需要登录并拥有仓库读取权限；也可以直接从公开网站下载完整单文件并转发。

网站兼容 `https://用户名.github.io/仓库名/` 这类项目路径，所有站内页面及资源均使用相对链接；不需要为仓库名修改页面地址。

### 自动构建流程

配置文件：`.github/workflows/pages.yml`。

| 触发方式 | 行为 |
| --- | --- |
| Push 到 `master` | 测试 → 构建 → 检查 → 保存产物 → 开关启用后发布 Pages |
| 面向 `master` 的 Pull Request | 测试、构建和检查，不部署 |
| Actions 中手动运行 | 检查选定分支；只有 `master` 可保存产物及发布 |

构建任务只有 `contents: read` 权限；部署任务才获得 `pages: write` 和 `id-token: write`，使用 `github-pages` 环境。同一分支的发布串行执行，避免中断已经开始的部署。

发布目录只包含生成的网页及其资源，不包含本地备份、导出历史、源码目录或完整的行程数据快照。`revision.json` 记录相对入口、版本及可用的提交号，不包含构建机器的绝对目录。

遇到首次构建失败，先在工作流日志中查看失败的检查或构建步骤；检查不通过时不会发布。若部署跳过，确认当前分支为 `master`、Pages 已启用且 `PAGES_DEPLOY_ENABLED=true`。

### 手机阅读与操作

窄屏下总表按天变为纵向卡片，保留上午、下午、晚上、步行与强度等标签；桌面仍使用原表格。行程导航在手机上默认折叠，点击展开，选中日程后收起，避免每次打开页面先经过很长的目录。

导航、馆图控制和主要操作按钮提供至少 44px 的触控高度；保留 Leaflet 地图缩放及拖动、卢浮宫路线交互、专题和待办。使用移动浏览器打开下载文件即可使用内嵌导航，网络底图仍需联网。

### 可选：自行绑定 goparis.z2f.dev

DNS、Cloudflare 和自定义域名绑定由用户操作；自动构建不会修改这些设置。

1. Pages 部署成功后，在仓库 **Settings → Pages → Custom domain** 填入 `goparis.z2f.dev` 并保存。
2. 在管理 `z2f.dev` 的 DNS 面板添加记录：

| 项目 | 值 |
| --- | --- |
| 类型 | `CNAME` |
| 名称 | `goparis` |
| 目标 | `aetherrootr.github.io` |
| TTL | 自动 |
| Cloudflare 代理 | 初次配置建议选 **DNS only／仅 DNS**（灰云） |

目标不要填写协议、仓库名或路径。先保存 GitHub 的自定义域名，再修改 DNS；不要建立通配记录。已有同名记录时，先确认用途，再自行调整。

3. 等 GitHub 的 DNS 检查及证书签发完成后，勾选 **Enforce HTTPS**。未准备绑定时继续使用默认 `github.io` 地址即可。

官方参考：[Pages 套餐支持](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)、[自定义发布工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[自定义域名配置顺序](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)、[下载产物权限](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)。

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
