# Cino 节奏大师

4 轨下落式手机网页音游。界面沿用 Guitar Star 原版结构，动效参考 Arcaea，配色是肉肉宇宙系列的绿色。

- 10 首歌，每首都有 **简单 / 普通 / 困难** 三份谱面
- 音符：点按、长按、滑键（按下后往箭头方向滑）、折线长按（按住跟着线换车道）
- 手机上始终横屏：竖着拿时整个游戏会自动转成横屏显示；安卓浏览器还会尝试全屏并锁定横屏
- 纯静态网页（HTML + JS + Canvas），没有任何构建步骤和依赖

## 目录

```
index.html          游戏本体（所有代码都在这一个文件里）
img/bump.png        音符贴图
songs/              歌曲：xxx.mp3、xxx.jpg（封面）、xxx_easy / _normal / _hard.txt（谱面）
tools/auto_chart.py 自动打谱脚本（Python + librosa）
```

## 本地运行

游戏要用 fetch 读取歌曲和谱面，不能直接双击打开 index.html，需要起一个本地服务器：

```bash
cd cino-beat
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 发布到 GitHub Pages

1. 把整个文件夹推到 GitHub 仓库
2. 仓库 Settings → Pages → Source 选 `Deploy from a branch`，分支选 `main`，目录选 `/ (root)`
3. 等一两分钟，访问 `https://<你的用户名>.github.io/<仓库名>/`

## 加一首新歌

1. 把音频转成 128k mp3（如果原文件其实是视频，也用这条命令提取音频）：
   ```bash
   ffmpeg -i 原文件 -vn -ac 2 -ar 44100 -b:a 128k songs/newsong.mp3
   ```
2. 封面裁成正方形，存成 `songs/newsong.jpg`（600×600 就够）
3. 自动打谱，生成三份谱面：
   ```bash
   pip install librosa
   python tools/auto_chart.py songs/newsong.mp3 songs/newsong "歌名"
   ```
4. 在 `index.html` 顶部的 `SONGS` 列表里加一行：
   ```js
   {audio:'songs/newsong.mp3', chart:'songs/newsong_normal.txt', cover:'songs/newsong.jpg',
    charts:['songs/newsong_easy.txt','songs/newsong_normal.txt','songs/newsong_hard.txt']},
   ```

## 谱面格式

每行一个音符，最后一行是 `[歌名]`。轨道是 4 位 0/1，例如 `0100` 表示第 2 条轨。时间单位是秒。

| 类型 | 格式 | 例子 |
|---|---|---|
| 点按 | `0#轨道#时间#时间` | `0#0100#12.5#12.5` |
| 长按 | `1#轨道#开始#结束` | `1#0010#20.3#22.2` |
| 滑键 | `2#轨道#时间#时间#方向`（R 右 / L 左） | `2#1000#19.3#19.3#R` |
| 折线长按 | `3#起始轨道#开始#结束#时间:车道;时间:车道;…` | `3#0001#11.7#15.4#11.7:3;12.6:2;13.5:1` |

## 自动打谱的规则（tools/auto_chart.py）

- 先分离人声，用 pyin 跟踪音高，把人声切成一个个音；同时测节拍和鼓点强度，所有音符都对齐节拍
- **简单**：只跟人声主要的字，一拍最多一个；长音给长按；没有折线和双押
- **普通**：跟人声每个音，最密半拍一个；连唱的地方给折线，句尾给滑键
- **困难**：人声 + 鼓点两层，鼓点放在另一只手那一侧；副歌重拍双押；滑键、折线更多
- 超过 160 BPM 的快歌整体放宽一档
- 自动避免同一条轨 0.3 秒内连打两下
