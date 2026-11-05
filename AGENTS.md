# AGENTS.md — Cino 节奏大师（网址 cino-beat）交接说明

> 给接手的 AI 助手（Codex 等）。先完整读完再动手。用户叫魏佳琪，**请用中文回复**。

## 1. 这是什么

- 一个**手机网页音游**，4 轨下落式（类似节奏大师 4K），纯静态网页：`index.html` 一个文件包含全部 HTML/CSS/JS，Canvas 画游戏画面，没有构建步骤、没有 npm 依赖。
- 最早是参考一个 Unity 项目「Guitar Star」改的（源码在上级目录 `../Guitar Star/`，只作参考，不要改），后来完全用网页重写。
- 游戏名：**Cino 节奏大师**；仓库名：**cino-beat**。属于用户的「肉肉宇宙」小游戏系列（同系列：菇菇跳一跳、肉了个肉、合成小瑞瑞 Cino Merge）。
- 玩家**主要用手机玩，且必须横屏**。

## 2. 文件结构

```
cino-beat/
  index.html              游戏本体（全部代码）
  sw.js                   离线缓存（Service Worker）：音频/封面缓存优先、页面/谱面网络优先；替换同名媒体文件必须把 sw.js 里 VERSION 加一
  img/bump.png            音符底图（目前只用于部分绘制）
  songs/                  10 首歌：<slug>.mp3、<slug>.jpg（600×600 封面）、<slug>_easy/_normal/_hard.txt（三档谱面）
  tools/auto_chart.py     自动打谱脚本（Python + librosa）
  tools/requirements.txt
  README.md               给人看的说明
  AGENTS.md               本文件
```

上级目录 `D:\桌面\肉肉宇宙\cino节奏大师\` 里还有：`歌曲素材/`（用户原始素材，每首一个文件夹，谱面也备份在里面）、`工具/`（打谱脚本备份）、`Guitar Star/`（原 Unity 工程，只读）。旧的 `cino-rhythm/` 文件夹和 `cino-rhythm.zip` 已作废。

**规则：所有改动直接写进 cino-beat 文件夹**（用户会直接从这里推 GitHub）。

## 3. 本地运行 / 测试

```bash
cd cino-beat
python -m http.server 8000     # 不能双击打开，fetch 读歌和谱需要 http
# 打开 http://localhost:8000 ；手机效果用浏览器开发者工具的设备模拟（竖屏 390×844 也要测）
```

每次改完至少检查：标题页 → 选歌（左右滑动/箭头）→ 选难度 → 游戏（点按/长按/滑键/折线都能判定）→ 结算 → 返回；以及**竖屏手机模拟下自动转横屏、触摸位置对得上车道**。

## 4. index.html 里的关键位置（搜这些名字）

| 名字 | 作用 |
|---|---|
| `SONGS` | 歌曲列表：`{audio, chart, cover, charts:[easy,normal,hard]}` |
| `LEVELS` | 三档难度：名字、颜色、`lead`（音符下落秒数：简单 2.1 / 普通 1.5 / 困难 1.0） |
| `JUDGE` / `WIN` / `PTS` | 判定文字、判定窗口（秒）、分数 |
| `parseChart` | 读谱面 txt |
| `applyOrient` / `toApp` / `ROT` | **横屏适配**：触屏设备竖着拿时把 `#app` 旋转 90°，CSS 里的 vw/vh/vmin 全部换成 JS 设置的 `--vw/--vh/--vmin`；所有触摸坐标必须经过 `toApp()` 换算。**所有界面元素（HUD、结算、暂停、各种弹窗）必须放在 `#app` 里面**——2026-11-05 踩过坑：#hud/#result/#pause 等原本在 #app 外面，竖屏时只有菜单和赛道旋转、它们不转，出现「画面横、文字竖」；删掉 #select 后一个多余的 `</div>` 让 #app 包住全部元素后修复 |
| `press` / `release` / `arrowFlick` / `completeFlick` | 输入判定（点按、长按、滑键） |
| `pathLane` | 折线长按当前所在车道 |
| `loop` / `draw` | 主循环、画面 |
| `drawNote` / `noteQuad` / `drawFlick` / `drawPath` | 音符绘制（音符按透视画成扁长梯形） |
| `buildStage` / `buildFxBase` / `fxLoop` | 舞台背景和菜单背景（只按分辨率生成一次再贴图，保证不卡） |
| `shutter` + `T.vinyl` | 界面转场（定稿为「唱片滚过」，`transKind='vinyl'`；代码里还留着 iris/tiles/stripes/zoom 备用） |
| `finish` | 结算；歌放完才结算，音符打完后右上角出现「跳过结尾」按钮 `#skipEnd` |
| `store` | localStorage 存最佳成绩、延迟校准（包了 try/catch） |
| `SFX` / `blip` | 按键音（WebAudio 合成的柔和「啵」声，不用音频文件） |

## 5. 谱面格式（songs/*.txt，每行一个音符，最后一行 `[歌名]`）

轨道是 4 位 0/1（`0100` = 第 2 轨），时间单位秒。

| 类型 | 格式 |
|---|---|
| 点按 | `0#轨道#时间#时间` |
| 长按 | `1#轨道#开始#结束` |
| 滑键 | `2#轨道#时间#时间#R`（或 `L`）— 按下后往箭头方向滑，0.3 秒内没滑算 BAD |
| 折线长按 | `3#起始轨道#开始#结束#t:车道;t:车道;...` — 按住跟着线换车道，换道有 0.2 秒宽限 |

## 6. 三档难度设计（用户确认过）

- **简单**：只跟人声主要的字，四分音符，一拍最多一个；换道最多一格；长按；少量滑键；无折线、无双押。
- **普通**：跟人声每个音，八分音符；长按、连唱的地方给折线、句尾给滑键。要「顺手、顺着节拍」。
- **困难**：人声 + 鼓点两层，鼓点放在人声另一侧（另一只手）；副歌重拍双押；更多滑键和折线；速度最快。
- 通用：所有音符卡节拍网格；避免同一车道 0.3 秒内连打；同一时刻最多 2 个音符；>160 BPM 的快歌整体放宽一档。

自动打谱：`pip install -r tools/requirements.txt`，然后
`python tools/auto_chart.py songs/x.mp3 songs/x "歌名"` → 生成 `x_easy/_normal/_hard.txt`。
加新歌流程：ffprobe 看是不是视频 → `ffmpeg -i 原文件 -vn -ac 2 -ar 44100 -b:a 128k songs/x.mp3` → 封面居中裁成 600×600 jpg → 打谱 → 在 `SONGS` 加一行。

### 10 首歌

| 歌 | slug | BPM | 备注 |
|---|---|---|---|
| Baby's Horizon | babys_horizon | 129 | |
| 09's Pimple | pimple09 | 117.5 | |
| 未命名 | weiming | 143.6 | 原文件是视频，已提音频 |
| 我不知道 | wobuzhidao | 143.6 | 原文件是视频，只有 21 秒（用户可能会给完整版） |
| 臆想 | yixiang | 152 | |
| BABE | babe | 152 | 原文件是视频 |
| baby step | babystep | 117.5 | |
| enemy | enemy | 107.7 | |
| melting sunny rain | meltingrain | 172 | 快歌，已放宽 |
| Tears | tears | 136 | 原文件 1:05 之后是说话，已截到 65 秒 + 淡出 |

## 7. 视觉风格（**固定，改东西时必须沿用**）

- 结构沿用 Guitar Star 原版：条纹标题面板、三档难度按钮、结算三栏（成绩总评 / 本次得分 / 最高分）。动效参考 Arcaea（轨道铺开、曲名进场条、菱形打击波、按键光柱、EARLY/LATE）。
- **全部是 CSS/矢量/Canvas 重画的，不要再引入原版位图**（原图分辨率低、带英文）。
- 配色是肉肉宇宙系列的低饱和绿（用户多次要求**不要太艳、不要太绿**）：
  - 菜单：浅薄荷底 `#eef5e7` + 格子布纹 + 浅绿网格地面；描边深绿 `#21402f`；主绿 `#3c8c55`
  - 面板：玉绿/鼠尾草绿 `#8cc9a3 → #5f9f7b → #467f61`，标题条斜纹 `#7dbb95 / #b4dcc0`
  - 游戏舞台：森林夜色 `#0e2216`；普通音符偏白 `#e9f3ec / #f7faf6`；滑键 `#6cbf8c`；折线 `#8fd3aa`；轨道边线 `#a9dcbd`
  - **黄色元素一律换成白色**
- 字体：中文全部**站酷快乐体 ZCOOL KuaiLe**，英文和数字 **Fredoka**（都从 Google Fonts 加载）；白字 + 深绿描边用 `paint-order:stroke fill`，**描边要细**（粗了会糊字）。
- 界面文字全中文；**游戏中的判定字用英文** PERFECT / GREAT / COOL / BAD / MISS，EARLY / LATE。
- 难度按钮：白底胶囊 + 彩色字 + 星级（简单 `#3c9c5c` ★ / 普通 `#21928a` ★★ / 困难 `#1b4a2e` ★★★）。
- 转场：「唱片滚过」，深森林绿黑胶 + 淡薄荷高光 + 细薄荷光边，奶白标签印 Cino。
- 手机上不显示 D F J K 键位提示，玩法提示里不写键盘操作（键盘操作代码保留）。
- 图标：统一 24 网格手绘 SVG、圆头线条（描边约 2.2）、用 currentColor，不用 ★ 等 Unicode 字符当图标；面板底纹是右下角细唱片纹（不再用星星/音符剪贴画）。弹窗不要加英文小标签（如 TUTORIAL）。
- 按钮（.gbtn、#touch）：全部统一成难度按钮那种白底立体胶囊——白→浅绿渐变底、深绿细边、底部 0.18em 深绿厚边、顶部柔光，字不描边（主按钮 #3c8c55 字，次按钮 #21402f 字）。小圆按钮（左右箭头/关闭/暂停）是细线图标 + 半透明底。选中封面用奶白细圈，不用亮薄荷绿。
- 新手教学加载时不弹窗，只把「点击开始」/「重玩教学」按钮文字改成「加载中…」；加载失败才弹窗。

## 8. 待办 / 下一步

1. 用户试玩后按反馈微调谱面或手感（问清是哪首歌、哪一档、第几秒）。
2. **上线到用户自己的服务器**（静态站已上线 2026-11-05：`https://api.cino1018.com/cino-beat/`（原地址 `/cino/` 已于 2026-11-05 改名，Caddy 对旧路径做 308 跳转到新地址、含子路径；游戏内全是相对路径所以搬地址零改动），Caddy 静态托管、与老游戏接口隔离，GitHub Pages 保留作备份；**排行榜与分数后端已上线 2026-11-05**，剩字体自托管未做）：
   - **排行榜（已上线）**：独立模块 `/opt/gugu-server/rhythm.js`（server.js 入口仅加分流、备份 `server.js.bak-20261105-pre-rhythm`），数据独立 SQLite `/opt/gugu-server/data/rhythm/rhythm.db`（players + scores 两表）。接口：`POST /api/rhythm/player`（建身份，返回 id+secret）、`POST /api/rhythm/score`、`POST /api/rhythm/name`、`GET /api/rhythm/board?song=<slug>&lv=0|1|2`（前 10 + 我的名次）、`GET /api/rhythm/health`。交分校验：counts 五档之和须等于谱面音符数、acc 按 counts 重算对账、分数须落在 counts 推出的上下界内（长按 tick 按谱面实算）。前端：身份存 localStorage `rr2-rhythm-player`、交分失败存 `rr2-rhythm-pending` 下次打开难度弹窗自动补交；本地导入歌曲不参与排行榜。**名字全局唯一（2026-11-05）**：`/player` 建号时名字已被占用会自动加 4 位随机后缀避让；`/name` 改名查重，占用返回 409 `name taken`（自己改回原名放行）。
   - **账号系统（已上线 2026-11-05）**：同一 rhythm.db 加 `accounts` 表（ukey=账号名小写主键、PBKDF2-HMAC-SHA256 密码哈希、player 唯一绑定玩家身份）。接口：`POST /api/rhythm/register`（需现身份 id+secret，把账号绑到当前匿名身份——名字与成绩全部保留；账号名 2–16 字、仅汉字/字母/数字/下划线、大小写不敏感唯一；密码 6–32 位；无邮箱找回）、`POST /api/rhythm/login`（校验后返回所绑身份的 id+secret+name+username，前端直接换成本地身份，成绩跟随账号跨设备；同 IP 登录限 15 次/分钟）、`POST /api/rhythm/password`（验旧改新）、`GET /api/rhythm/me?id&secret`（name、username、全部战绩含每项名次）。前端：**开始界面（标题页）**右上角胶囊按钮 `#acctBtn`（未登录显示「登录 / 注册」、登录后显示「个人中心」；按钮在 `#title` 内，点击必须 stopPropagation 防误触开始游戏）；登录/注册弹窗 `#acctDim` 与个人中心 `#meDim` 挂在 `#app` 层级（不在任何 section 里），共用 `.acctFrame` 横向宽框（宽公式同 `#lvFrame`，内部两栏布局、字号约 3.2cqw——用户否决过竖长窄卡，弹窗一律横宽）；面板规则、hd 字号都要单独给 `.acctFrame` 写一份，cqw 相对框宽；登录时把原匿名身份存 `rr2-rhythm-anon`，退出登录时恢复；个人中心可改名（复用 `/name`）、改密、看战绩列表。**结算引导（2026-11-05）**：打完一首歌若未登录，结算页出现 1 秒后自动弹出注册页（`finish()` 里 `openAcct('reg')`），已登录不弹。
   - **难度弹窗（已改版 2026-11-05）**：宽框三栏——左栏封面+歌名+时长/音符数+延迟滑块，中栏三档难度按钮（含本地最高分），右栏排行榜（难度选项卡切换、自己一行高亮、底部状态行：已登录显示我的名次+名字+「账号 xxx」、未登录显示「登录 / 注册」按钮——点击关难度弹窗并打开登录页；改名已从排行榜移除，统一去个人中心）。`#lvFrame` 设了 `container-type:inline-size`，框内 cqw 按框宽计、矮屏自动等比缩，改尺寸时注意这一点；框宽现为 `min(163*var(--vw),170*var(--vh),950px)`、宽高比 1.96。中栏是网格等高三行（按钮在行内伸缩、不会互相穿）；封面就是单张 `#lvCover` 正方形图（圆角+细白边、无包装层/阴影/放大——套包装层在 iOS 上会从上角和底边露白，用户明确否决过）；flex 子元素慎用 `overflow:hidden`（会被压成 0 高/0 宽，歌名与榜单名字都中过招，须 `flex:none`/给 min-width）。
   - 服务器：腾讯云轻量 香港 2核2G Ubuntu 24.04，域名 `https://api.cino1018.com`（Caddy 反代，自动 HTTPS），一个纯 Node 标准库服务 `/opt/gugu-server/server.js`（systemd 管理）。
   - 上面**正在正式运营**两个游戏，**绝对不能改动或删除它们的接口和数据**：
     - 菇菇跳一跳：`/api/health`、`/api/board`、`/api/rank`、`/api/rpc/*`、`/api/avatar/*`、`/api/upload/*`、`/api/realtime/*`（数据在 Supabase）
     - 肉了个肉：`/api/stats`、`/api/clear`（SQLite `/opt/gugu-server/data/rou.db`）
   - 计划：静态页面放 `https://api.cino1018.com/<新游戏名>/`；新接口放 `/api/rhythm/...`（player / score / board / me / health），数据用**独立** SQLite（如 `/opt/gugu-server/data/rhythm/rhythm.db`）；新代码写成独立文件，`server.js` 只在请求入口加几行分流；改前备份 `server.js`；保持纯 Node 标准库、不加依赖。
   - 改完重启后**必须验证**：`/api/health` 正常、老游戏的 `/api/board` 和 `/api/stats` 都还能正常返回，才算交付。
   - 服务器是密钥登录 root，**需要 SSH 方式时直接问用户，不要猜密码或暴力尝试**。
   - 加载优化（已做）：选歌停留 0.5 秒预加载居中歌曲（`getBuffer` 流式下载带进度，加载文案显示百分比）；`sw.js` 缓存音频/封面实现重复游玩秒开。换同名 mp3/jpg 内容时必须同步把 `sw.js` 的 `VERSION` 加一。
   - 上服务器时顺便把字体改成自托管（Google Fonts 在国内打不开），按用到的字裁剪。
   - 前端接口统一指向 `https://api.cino1018.com`，不要用任何旧的 Cloudflare 地址。
3. 「我不知道」如果用户给了完整版音频，重新打谱。

## 9. 新手教学（已实现）

- 首次点击开始 → `beginTutorial()` → 《我不知道》独立教学谱 `songs/wobuzhidao_tutorial.txt`。只教点按、长按、滑键；原三档谱面不变。
- `G.tutorial` 保存步骤、暂停的歌曲时间和三个首次示范音符。`tutorialFreeze` 停止音频源并固定歌曲时钟；操作成功由 `tutorialContinue` 按音频位置恢复，不依赖整段 AudioContext 挂起来等待手势。
- 通过 `tutorialPress` / `tutorialPassed` / `tutorialGate` 接入原判定。长按提前松手、滑键未完成会原地重试；暂停/重来保留教学语义。
- `finishTutorial` 独立完成页不写正式最佳成绩。完成或主动跳过写入 `rr2-tutorial-v1`；选歌页 `#tutorialReplay` 可重玩。加载令牌 `tutorialToken` 防止跳过后异步加载重开游戏。
- `mobileDevice()` 区分主要使用鼠标的触屏电脑和手机；电脑窄窗口保持正向，手机竖屏旋转。

## 谱面格式（血泪教训，2026-11-05）
- 第二字段是**四位字符串掩码**：第 i 位字符为 '1' 表示该行在第 i 车道有一个音符（parseChart 逐字符读）。**绝不能写整数位掩码**（1/2/4/8）——那样除车道 0 外全部音符会被解析丢弃（babystep 开头曾因此丢 13/17 个音符）。
- 服务端 rhythm.js 按**行数**计音符数校验交分：必须保证「文件行数 == parseChart 解析出的音符数」，任何生成/改谱工具交付前都要用 parseChart 本身验一遍。
- **起音 ≠ 能量峰值**：钢琴等人声/乐器起音比 RMS 包络或谱通量的能量峰值早约 40ms。谱面对拍必须以起音为准（10ms RMS 包络上升沿 + 谱通量双重确认），绝不能用峰值时间。PERFECT 窗只有 ±45ms，40ms 的系统性误差会把整个 PERFECT 窗吃光——babystep 开头 0.30/0.56/0.80/1.03 就是峰值时间，真起音是 0.26/0.51/0.76/1.00（2026-11-05 已按起音重对并补齐缺音）。

## 地狱模式（2026-11-05 上线）
- 标题页「点击开始」下方有独立「地狱模式」按钮（#hellBtn，必须 stopPropagation）；全局 MODE 区分入口，选歌共用同一 SONGS，地狱面板复用难度弹窗（#level.hell 隐藏三档行与榜单选项卡，显示「开始挑战」#lvHellGo + best3）。
- 地狱 = lv 3：谱面 `songs/<slug>_hell.txt`（pickLevel/confirmSong 按 slug 拼路径，不进 SONGS.charts）；LEVELS[3] lead 与困难相同 1.0（难度来自谱面密度，不靠缩短预读）；判定窗口不变。
- 生命条仅地狱：满 100，PERFECT +0.8 / GREAT +0.4 / COOL 0 / BAD −5 / MISS −9（HELL.gain 集中配置）；award() 是唯一结算点，断长按在 breakHold 里按差值补扣，保证一个音符只结算一次生命；主循环帧末 hp<=0 → failFinish()（先结算当帧整组漏键再判失败）。失败不交服务器，只存本地 `hellrec-<key>` 挑战记录（最佳进度）；通关才按 lv=3 交分，榜单与三档独立。
- 后端 rhythm.js 的 DIFFS 已含 'hell'（lv=3 的 chartInfo 读 <slug>_hell.txt 按行数校验，与三档同规则）；个人中心 LV_NAMES 已加「地狱」。
- 地狱谱面由 ~/workspace/cino-beat-audit/gen_hell.py 生成：以困难谱面为骨架（时间已验证），新增音符全部取自该曲实际音频的起音事件池，并按四指占用/同轨间隔/密度上限约束，validate_hell.py 独立校验（行数==解析数、同轨间隔、长按/折线占用、同时手指≤4、0.5s 密度、滑键不越界；与困难谱面原样一致的骨架冲突只警告）。

## 2026-11-05 体验升级（地狱 v2 / 设置 / 校准 / 纪录）
- 地狱谱面 v2 由 `~/workspace/cino-beat-audit/gen_hell2.py` 生成：困难骨架不删、按 10 秒窗密度分恢复/铺垫/爆发三档塑形（恢复段不加密）、新增音符取真实起音池（距已有音符 ≥48ms）、爆发段强起音配双押/三押、孤立点按转长按、乐句尾转滑键；手指/密度口径与 validate_hell.py 完全一致（折线按整段全车道近似占用）。改谱后必跑 validate_hell.py 全首 ALL OK。旧 v1 的均匀加密谱已被 v2 取代，不要回滚到 v1。
- 练习分段在 index.html 的 SONG_SEGS（2026-11-05 由音频能量/密度分析烘焙，起点已逐个核对不切断地狱谱长按——落进长按的起点一律挪到长按头）；audit 里的 gen_segments.py 是重算工具，其阈值口径与烘焙版不完全一致，重算结果必须人工核对（尤其是分段数量与长按切断）后才能替换 SONG_SEGS。没有数据的歌只给「从头」，不要再用四等分编造分段。tears/教学歌只有「从头」是分析结论，不是漏做。
- 延迟校准 = 跟拍测试（#calDim）：节拍用 WebAudio 音频时钟预调度、点击在 pointerdown 用同一时钟记录、中位数（MAD 过滤）出推荐值。offset 语义：判定误差 = 总延迟 − offset，推荐值直接替换不叠加；补偿只在 songTime 一处生效，不要在别处再加。手动滑杆方向：总显示 LATE 调大、EARLY 调小。
- 音频走两条增益总线：歌曲音源必须 connect(musicBus())、界面音效/校准音走 sfxBus()；新增音源别直连 destination。
- 个人纪录分开存（键名 best-/acc-/fc-/clear- + 歌曲 key + 难度）：最高分、最佳准确率、全连、地狱通关可能来自不同场次，界面别合并表述。全连看 G.fcFail（MISS、长按/折线断开、滑键未滑到都置位；滑键失败只记 BAD 不记 MISS，只看 counts[0] 会误判）。结算差值必须与本局开始前的纪录比（finish 里先读 prev 再写）。
- 演奏设置（速度/延迟/音乐音量/音效音量/特效 std|low）都存 localStorage（rr2- 前缀），设置弹窗与确认面板滑杆共用同一状态、互相 sync；恢复默认不碰成绩/账号/纪录键。
