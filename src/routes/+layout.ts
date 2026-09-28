// El kiosco es una SPA de una sola pantalla: todo se pinta en el navegador.
// `ssr = false` evita que el build intente renderizar en el servidor (que
// además no existe: el build es estático y lo sirve nginx).
export const ssr = false;
export const prerender = false;
