# 巴黎与凡尔赛旅行计划

按日查看行程、地图、交通、景点介绍和参观专题。保留现有 14 天安排，同时提供可分发的完整单文件 HTML。

## 平时怎样更新

1. 修改 `data/plan.json` 中的行程内容；版式和交互分别在 `templates/` 与页面生成器中维护。
2. 在本地构建并检查，或向 `master` 提交 Pull Request，让 Actions 检查。
3. 修改推送或合并到 `master` 后，GitHub Actions 自动重新生成并保存私有构建产物。

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
python scripts/validate_site.py dist --check-js
```

`--check-js` 需要 Node.js 20 或更新版本，用于检查内嵌脚本语法；不运行这个选项时无需 Node.js。GitHub 托管的 Ubuntu runner 已提供 Node.js。

检查涵盖页面、景点锚点、本地资源、仓库子路径、完整单文件的内部导航，以及先前地图组件加载问题的回归检查。链接和脚本检查不能代替浏览器中的交互实测。

地图街道底图和外部官网需要联网；每日点位、路线、卢浮宫馆图和文字说明包含在构建结果中。待办勾选状态保存在各自浏览器中，不会同步到仓库或其他同行者。

## 私有仓库与访问范围

远程仓库：[aetherrootr/paris-trip-plan](https://github.com/aetherrootr/paris-trip-plan)，保持私有。**网站本身也必须私有**。

GitHub 仓库的私有状态不会自动保护 Pages 网站。GitHub 原生的私有 Pages 访问控制适用于 GitHub Enterprise Cloud 组织下的项目；当前个人账户仓库不按公开 Pages 方式发布。

因此，当前工作流只在私有仓库中构建和保存产物，**不调用 Pages 部署、不申请 Pages 写入权限、不开放网站地址**。带登录保护的在线网站托管需要另行配置。

### 获取自动更新的私有版本

1. 修改推送或合并到 `master`，或在 **Actions** 手动运行 **Build private trip site**。
2. 在成功的工作流运行页面下方找到 **Artifacts**。
3. 下载 `paris-trip-offline`：解压后用浏览器打开完整单文件 HTML。
4. 需要全部独立页面时，下载 `paris-trip-site`。

产物保留 30 天，下载需要登录并拥有此仓库的读取权限。只想转发行程时也可自行分发已下载的单文件；该文件本身没有额外的登录保护。

网站兼容 `https://用户名.github.io/仓库名/` 这类项目路径，所有站内页面及资源均使用相对链接；不需要为仓库名修改页面地址。

### 自动构建流程

配置文件：`.github/workflows/build.yml`。

| 触发方式 | 行为 |
| --- | --- |
| Push 到 `master` | 测试 → 构建 → 检查 → 保存私有网站和单文件产物 |
| 面向 `master` 的 Pull Request | 测试、构建和检查，不部署 |
| Actions 中手动运行 | 检查选定分支；只有 `master` 保存分发产物 |

工作流只有 `contents: read` 权限。没有网站部署任务；同一分支的新构建会取消尚未完成的旧构建。

发布目录只包含生成的网页及其资源，不包含本地备份、导出历史、源码目录或完整的行程数据快照。`revision.json` 记录相对入口、版本及可用的提交号，不包含构建机器的绝对目录。

遇到首次构建失败，先在工作流日志中查看失败的检查或构建步骤；检查不通过时不会上传分发产物。仓库需要启用 Actions。

官方参考：[Pages 私有访问控制](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)、[下载工作流产物的权限](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)。

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
