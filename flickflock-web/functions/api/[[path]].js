const BACKEND = "https://w8coggc8kow8osw40wos4wkw.dumky.net";

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const target = new URL(url.pathname + url.search, BACKEND);

  const headers = new Headers(context.request.headers);
  headers.delete("host");

  const response = await fetch(target.toString(), {
    method: context.request.method,
    headers,
    body: context.request.method !== "GET" ? context.request.body : undefined,
  });

  return new Response(response.body, {
    status: response.status,
    headers: response.headers,
  });
}
