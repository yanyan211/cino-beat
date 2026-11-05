/* Cino 节奏大师 · 离线缓存
   - 音频/封面：缓存优先，存进独立的媒体缓存 MEDIA —— 代码版本升级时不清它，
     免得每次发新版玩家都要把所有歌重新下载一遍（曾经每升一版全清一次）。
   - 页面/谱面等：网络优先（保证谱面更新立刻生效），断网时回退缓存。
   - 升级时把旧版本缓存里的媒体文件迁移进 MEDIA，再删旧缓存：玩家已下好的歌不丢。
   注意：替换同名 mp3/jpg 的内容时，必须把 MEDIA 的名字加一（如 cino-media-v2），
   否则老玩家会一直读到旧缓存。 */
const VERSION = 'cino-beat-v12';
const MEDIA = 'cino-media-v1';
const MEDIA_HOST = 'cino-songs-1524353495.cos.ap-guangzhou.myqcloud.com';   // 歌曲/封面已迁腾讯云 COS（广州）
const CORE = ['./', 'index.html'];
const MEDIA_RE = /\.(mp3|jpg|jpeg|png|webp)$/i;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const media = await caches.open(MEDIA);
    for (const req of await media.keys()) {   // 媒体改走 COS 后，旧的本站地址缓存条目作废，清掉免得占空间
      if (!req.url.startsWith('https://' + MEDIA_HOST + '/')) await media.delete(req);
    }
    for (const k of await caches.keys()) {
      if (k === VERSION || k === MEDIA) continue;
      const old = await caches.open(k);
      for (const req of await old.keys()) {
        if (MEDIA_RE.test(new URL(req.url).pathname) && !(await media.match(req))) {
          const res = await old.match(req);
          if (res) await media.put(req, res);
        }
      }
      await caches.delete(k);
    }
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const isMediaHost = url.origin === location.origin || url.host === MEDIA_HOST;
  if (!isMediaHost) return; // 其他跨域请求（字体等）不接管
  if (MEDIA_RE.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        if (res.ok || res.type === 'opaque') { const copy = res.clone(); caches.open(MEDIA).then(c => c.put(req, copy)); }   // 只缓存成功响应：404/500 不落盘，否则一次失败会把重试也堵死；封面走 <img> 的是 opaque 响应，一并缓存
        return res;
      }))
    );
  } else {
    if (url.origin !== location.origin) return;
    e.respondWith(
      fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req))
    );
  }
});
