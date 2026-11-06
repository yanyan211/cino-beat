// Cino 节奏大师接口中转：把 /api/rhythm/* 转发到香港服务器 api.cino1018.com。
// 用途：玩家所在网络连不上香港（连接被重置等）时，游戏客户端自动改走这里，
// Cloudflare 边缘到香港源站这段走 CF 骨干网，一般不受玩家本地网络影响。
// 注意：后端按真实 IP 限流（交分 20 次/分钟、登录尝试），转发时把 CF 给的
// 真实访客 IP（CF-Connecting-IP）写进 x-forwarded-for，与直连时 Caddy 的行为一致，
// 避免所有中转玩家共用 CF 出口 IP 被一起限流。
const ORIGIN = 'https://api.cino1018.com';

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': request.headers.get('Access-Control-Request-Headers') || 'content-type',
        'Access-Control-Max-Age': '86400',
      },
    });
  }

  const headers = new Headers(request.headers);
  headers.delete('host');
  const ip = request.headers.get('CF-Connecting-IP');
  if (ip) headers.set('x-forwarded-for', ip);

  const init = { method: request.method, headers, redirect: 'manual' };
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body;
    init.duplex = 'half';
  }

  const resp = await fetch(ORIGIN + url.pathname + url.search, init);
  const out = new Headers(resp.headers);
  out.set('Access-Control-Allow-Origin', '*');
  return new Response(resp.body, { status: resp.status, headers: out });
}
