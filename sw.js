/* Cino 节奏大师 · 离线缓存
   - 音频/封面：缓存优先（下过一次存本地，再玩秒开，不再受 Pages 10 分钟缓存限制）
   - 页面/谱面等：网络优先（保证谱面更新立刻生效），断网时回退缓存
   注意：替换同名 mp3/jpg 的内容时，必须把 VERSION 加一，否则老玩家会一直读到旧缓存。 */
const VERSION = 'cino-beat-v2';   // v2：修复把 404 也写进缓存导致失败重试永远命中坏缓存的问题，顺带清掉旧坏条目
const CORE = ['./', 'index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return; // 字体等跨域请求不接管
  if (/\.(mp3|jpg|jpeg|png|webp)$/i.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }   // 只缓存成功响应：404/500 不落盘，否则一次失败会把重试也堵死
        return res;
      }))
    );
  } else {
    e.respondWith(
      fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req))
    );
  }
});
