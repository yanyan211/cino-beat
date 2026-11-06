# 交接与同步说明（HANDOVER）

> 给在另一台电脑上继续开发本项目的 Claude / 协作者。
> 阅读顺序：先读本文件，再读同目录 `AGENTS.md`（项目全部现行约定），最后看 `git log`（逐次变更说明）。

## 同步方式（唯一事实来源 = 本仓库 main 分支）

- 2026-11-05 起，本项目的迭代主要在另一台机器上进行，所有改动都已 commit + push 到本仓库。**不要在仓库之外的副本上改代码。**
- 已有本仓库克隆：在克隆目录里 `git pull origin main` 即可拿到最新代码 + 本文件。
- 不确定本地文件夹是不是克隆（或改乱了）：把旧文件夹改名留作备份，重新 `git clone https://github.com/yanyan211/cino-beat`，今后只在克隆里工作。
- 部署不等同于 push：前端部署是把 `index.html` / `sw.js` 单独 scp 到香港服务器（见下），push 只同步代码与歌曲分发（Pages）。改完前端记得两件都做，或向用户确认由谁部署。

## 当前线上状态（2026-11-06 实查）

- 正式站：https://api.cino1018.com/cino-beat/ （香港轻量服务器，目录 `/opt/gugu-server/cino-beat`；部署 = scp 覆盖 + `chmod 644`；旧地址 `/cino/` 是 308 跳转，别再引用）
- `SCORE_VER = 5`：谱面音符数量变化时才 +1，客户端 `index.html` 与后端 `rhythm.js` 必须同步改
- `sw.js`：VERSION = `cino-beat-v14`，媒体缓存 = `cino-media-v2`（换同名媒体内容必须 bump 媒体缓存名）
- 歌曲/封面主源：**Cloudflare Pages** `https://cino-songs.pages.dev/`，连本仓库自动部署——push 后仓库根目录 `songs/` 即自动发布，**加歌/换歌只改仓库 songs/ 并 push，不再往 COS 上传**
- 回退链：Pages 拉不到时游戏自动回退本站同名文件，所以**服务器上的 songs/ 原文件是兜底、绝不能删**
- 腾讯云 COS 桶 `cino-songs-1524353495`：`game/` 前缀是整站镜像作备用入口（主站更新后要手动重传才同步）。**2026-11-07 起镜像为「全国内版」**：镜像版 index 的 MEDIA_BASE 指回桶根目录（桶根 `songs/` 的歌曲原文件不要删）、sw 的 MEDIA_HOST 同步、VERSION 比正式版 +1（现 v15）；与正式版只差这 3 处，同步规程见 `~/workspace/cino-mirror/README.md`。**镜像对外链接必须用静态网站域名** `https://cino-songs-1524353495.cos-website.ap-guangzhou.myqcloud.com/game/index.html`（桶已开静态网站）；默认域名 cos.ap-guangzhou.myqcloud.com 因腾讯对 2024 年后新桶的强制下载规则打不开网页（元数据改不动），只供页面内部取歌曲。主站歌曲流量仍走 Pages（COS 按量曾达 ¥30+/天，别让主站指回 COS；EdgeOne 已否决，别再提议）
- **接口中转（2026-11-06 上线）**：仓库 `functions/api/rhythm/[[path]].js` 是 Pages Function，把 cino-songs.pages.dev 上的 `/api/rhythm/*` 转发回香港后端，并把 CF-Connecting-IP 写进 x-forwarded-for（后端按 XFF 首地址限流，别删这行）。客户端 `api()/apiJ()` 共用 `apiFetch()`：直连在网络层被拒才改走中转，服务器正常应答不触发。效果：玩家开 Pages 副本（https://cino-songs.pages.dev/ 本身就是一份可玩的游戏）或 COS 镜像时，即使其网络连不上香港，排行榜/账号/交分仍可用。已用「直连指向死端口」的临时页在真实浏览器验证（榜单经中转正常加载）。
- 后端**不在本仓库**：服务器 `/opt/gugu-server/rhythm.js`（Node 22 + `node:sqlite`，数据库 `/opt/gugu-server/data/rhythm/rhythm.db`）。改后端前先从服务器拉最新版比对，不要凭任何旧副本改。接口：player / score / name / board / health / settings（设置跟账号走）
- 数据快照（2026-11-06）：注册账号 4,017、提交成绩玩家 3,675、排行榜成绩 9,913 条、近两日对局 16,553 局、地狱模式通关玩家 51 人

## 2026-11-05 以来的主要变更（细节见 git log）

- 地狱模式上线：独立谱面（生成口径见 AGENTS.md）、生命条、练习分段（按真实音乐结构命名：主歌一/副歌一…）、通关才交分
- 谱面规则定版：折线扫过的车道禁夹其他音符（只限扫过车道）；滑键的源轨与目标轨在滑键时刻必须干净；`validate_hell` 已按此硬校验
- 交分可靠性：每局 playId + 服务端去重、失败先落盘待补交、403 身份失效自动重建重试
- 账号系统：用户名密码（PBKDF2、无邮箱找回）、设置跟账号走（校准/速度/双音量/特效）
- 跟拍校准：2026-11-06 修复「识别不到点击」（采集窗放宽到半拍 300ms 等，commit 9b370d1）
- 全平台不再请求全屏；多指 pointercancel 只松被抢走的手指、不再整局暂停
- 判定文字在轨道远端 P(.78)，连击数在屏幕左侧（不挡下落音符）
- 歌曲分发：香港服务器 → COS（2026-11-05）→ Cloudflare Pages（2026-11-06），游戏地址始终没变
- 接口中转上线（2026-11-06）：Pages Function 转发 /api/rhythm/* + 客户端 apiFetch 自动 fallback，备用入口从此全功能

## 未决事项（不要擅自推进）

- **打击音效选型未定**：内测站 https://api.cino1018.com/cino-beat-beta/ 里试过「鼓边击」打击音 + 安卓震动，用户不满意；前后 7 个候选音色均未被选中，等用户给出参考游戏再定。**不要把任何打击音效带进正式版**；内测站与正式版隔离（独立本地存储、不交分），别去动它
- 一批真机手感项待用户实机反馈（校准修复效果、地狱难度手感、三指修复、判定布局观感）——反馈前不要再改手感参数
- 版面固定规则与「改一处、查同类」是用户明示的长期规则（AGENTS.md 有全文），改 UI 前必读、声称完成前必须多尺寸渲染检查
