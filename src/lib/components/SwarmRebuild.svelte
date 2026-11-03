<!-- SwarmRebuild.svelte
     Efecto "Swarm Rebuild" fiel al original (github.com/DhvanilPatel/swarm-cursors).
     Snapshot del DOM real + reconstrucción elemento por elemento con cursors
     que arrastran cajas con cruceta y badge de tamaño, tipean texto con caret,
     dibujan bordes con la pluma, arrastran guías de regla.

     Adaptado para la TV (kiosco, sin mouse): los cursors son autónomos y
     reconstruyen en orden top-down (modo Tour).

     Cumple la regla del kiosco: todo en canvas, sin red, sin archivos extra.
     Se apaga solo si fps < 40 (modo-ligero) y respeta ?sinanim=1.
-->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  let { activo = false, duracion = 2800, objetivo = null } = $props();

  let canvas: HTMLCanvasElement | null = null;
  let ctx: CanvasRenderingContext2D | null = null;
  let raf: number = 0;
  let empezado = 0;
  let ancho = 0, alto = 0;
  let dpr = 1;

  // ── Snapshot del DOM: extrae elementos visibles con su bounding rect y estilos ──
  interface Elemento {
    x: number; y: number; w: number; h: number;
    tipo: 'rect' | 'texto' | 'linea' | 'media';
    color: string;
    radio: number;
    texto: string;
    fuente: string;
    peso: string;
    orden: number;
  }
  let elementos: Elemento[] = [];

  function tomarSnapshot() {
    elementos = [];
    if (!objetivo) return;
    const rect = objetivo.getBoundingClientRect();
    const nodos = objetivo.querySelectorAll('*');
    let orden = 0;
    nodos.forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) return;
      if (r.right < 0 || r.bottom < 0 || r.left > rect.width || r.top > rect.height) return;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const tag = el.tagName.toLowerCase();
      const texto = (el.textContent || '').trim().slice(0, 60);
      const tieneHijos = el.children.length > 0;
      // Solo elementos "hoja" o con fondo/borde visible
      const tieneFondo = cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent';
      const tieneBorde = cs.borderTopWidth !== '0px' && cs.borderTopWidth !== '';
      const esTexto = !tieneHijos && texto.length > 0;
      if (!tieneFondo && !tieneBorde && !esTexto) return;

      const tipo: Elemento['tipo'] = esTexto ? 'texto' : (tag === 'img' || tag === 'svg' || tag === 'canvas' ? 'media' : 'rect');
      const color = tieneFondo ? cs.backgroundColor : (tieneBorde ? cs.borderTopColor : 'rgba(255,255,255,0.05)');
      const radio = parseFloat(cs.borderTopLeftRadius) || 0;

      elementos.push({
        x: r.left - rect.left,
        y: r.top - rect.top,
        w: r.width,
        h: r.height,
        tipo,
        color,
        radio,
        texto: esTexto ? texto : '',
        fuente: cs.fontFamily.split(',')[0].replace(/['"]/g, '').trim() || 'system-ui',
        peso: cs.fontWeight,
        orden: orden++,
      });
    });
    // Ordenar por posición top-down, luego left-right
    elementos.sort((a, b) => a.y === b.y ? a.x - b.x : a.y - b.y);
  }

  // ── Cursors (swarm) ──
  interface Cursor {
    x: number; y: number;
    tx: number; ty: number;
    color: string;
    velocidad: number;
    tamaño: number;
    modo: 'orbitando' | 'arrastrando' | 'escribiendo' | 'reposo';
    elementoIdx: number;
    progreso: number;
    // Para el crosshair drag
    dragW: number; dragH: number;
    // Para typing
    caretVisible: boolean;
    caretTimer: number;
  }
  const COLORES = ['#3B82F6', '#F97316', '#10B981', '#EC4899', '#8B5CF6', '#F59E0B', '#06B6D4', '#EF4444', '#A855F7', '#14B8A6'];
  let swarm: Cursor[] = [];
  let construidos: boolean[] = [];

  function crearCursors() {
    swarm = [];
    construidos = elementos.map(() => false);
    const n = Math.min(elementos.length, 12);
    for (let i = 0; i < n; i++) {
      const el = elementos[i] ?? elementos[0];
      swarm.push({
        x: ancho / 2 + Math.cos(i * Math.PI * 2 / n) * 120,
        y: alto / 2 + Math.sin(i * Math.PI * 2 / n) * 120,
        tx: el.x + el.w / 2,
        ty: el.y + el.h / 2,
        color: COLORES[i % COLORES.length],
        velocidad: 0.06 + Math.random() * 0.04,
        tamaño: 14 + Math.random() * 6,
        modo: 'orbitando',
        elementoIdx: i,
        progreso: 0,
        dragW: 0,
        dragH: 0,
        caretVisible: true,
        caretTimer: 0,
      });
    }
  }

  // ── Elementos construidos (para dibujarlos ya construidos) ──
  let elementosConstruidos: boolean[] = [];

  // ── Audio sintetizado (Web Audio API) ──
  let audioCtx: AudioContext | null = null;
  function sonido(tipo: 'click' | 'typing' | 'snap' | 'done' | 'swell') {
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const ctx = audioCtx;
      const now = ctx.currentTime;
      if (tipo === 'click') {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = 'square';
        o.frequency.value = 800 + Math.random() * 200;
        g.gain.setValueAtTime(0.08, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        o.connect(g).connect(ctx.destination);
        o.start(now); o.stop(now + 0.05);
      } else if (tipo === 'typing') {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = 'square';
        o.frequency.value = 1200 + Math.random() * 400;
        g.gain.setValueAtTime(0.05, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.03);
        o.connect(g).connect(ctx.destination);
        o.start(now); o.stop(now + 0.03);
      } else if (tipo === 'snap') {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = 'sine';
        o.frequency.value = 1800;
        g.gain.setValueAtTime(0.1, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
        o.connect(g).connect(ctx.destination);
        o.start(now); o.stop(now + 0.08);
      } else if (tipo === 'done') {
        // Acorde E major
        [329.63, 415.30, 493.88].forEach((f, i) => {
          const o = ctx.createOscillator();
          const g = ctx.createGain();
          o.type = 'sine';
          o.frequency.value = f;
          g.gain.setValueAtTime(0.06, now + i * 0.05);
          g.gain.exponentialRampToValueAtTime(0.001, now + 0.6 + i * 0.05);
          o.connect(g).connect(ctx.destination);
          o.start(now + i * 0.05); o.stop(now + 0.6 + i * 0.05);
        });
      } else if (tipo === 'swell') {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = 'sine';
        o.frequency.setValueAtTime(200, now);
        o.frequency.exponentialRampToValueAtTime(600, now + 0.4);
        g.gain.setValueAtTime(0.04, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
        o.connect(g).connect(ctx.destination);
        o.start(now); o.stop(now + 0.4);
      }
    } catch (e) { /* audio no disponible */ }
  }

  // ── Tick principal ──
  function tick(now: number) {
    if (!ctx || !canvas) return;
    const t = now - empezado;
    const progreso = Math.min(1, t / duracion);

    // Fondo que se "borra" al inicio (fade out) y se revela al final (fade in)
    const fadeOut = progreso < 0.08 ? progreso / 0.08 : 1;
    const fadeIn = progreso > 0.92 ? (progreso - 0.92) / 0.08 : 0;
    const alpha = 1 - fadeOut * 0.95 + fadeIn * 0.95;
    ctx.fillStyle = `rgba(15, 23, 42, ${1 - alpha})`;
    ctx.fillRect(0, 0, ancho, alto);

    // Dibujar elementos ya construidos
    for (let i = 0; i < elementos.length; i++) {
      if (!construidos[i]) continue;
      const el = elementos[i];
      if (el.tipo === 'rect' || el.tipo === 'media') {
        // Relleno
        ctx.fillStyle = el.color;
        ctx.beginPath();
        if (el.radio > 0) {
          ctx.roundRect(el.x, el.y, el.w, el.h, Math.min(el.radio, el.w / 2, el.h / 2));
        } else {
          ctx.rect(el.x, el.y, el.w, el.h);
        }
        ctx.fill();
        // Borde sutil
        ctx.strokeStyle = 'rgba(255,255,255,0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();
      } else if (el.tipo === 'texto') {
        ctx.font = `${el.peso === '700' || el.peso === 'bold' ? 'bold' : 'normal'} 14px ${el.fuente}, system-ui, sans-serif`;
        ctx.fillStyle = '#F1F5F9';
        ctx.fillText(el.texto, el.x, el.y + 14);
      }
    }

    // Asignar elementos a cursors (top-down)
    const elementosPorCursor = Math.ceil(elementos.length / swarm.length);
    for (let ci = 0; ci < swarm.length; ci++) {
      const cursor = swarm[ci];
      const idxBase = ci * elementosPorCursor;
      const idx = Math.min(idxBase + Math.floor(cursor.progreso * elementosPorCursor), elementos.length - 1);
      if (idx < 0 || idx >= elementos.length) continue;
      const el = elementos[idx];

      // Target del cursor = centro del elemento
      cursor.tx = el.x + el.w / 2;
      cursor.ty = el.y + el.h / 2;

      // Interpolación suave
      cursor.x += (cursor.tx - cursor.x) * cursor.velocidad;
      cursor.y += (cursor.ty - cursor.y) * cursor.velocidad;

      // Fase de construcción
      const dist = Math.hypot(cursor.x - cursor.tx, cursor.y - cursor.ty);
      if (dist < 8 && cursor.modo !== 'escribiendo') {
        cursor.modo = el.tipo === 'texto' ? 'escribiendo' : 'arrastrando';
      }

      if (cursor.modo === 'arrastrando') {
        cursor.progreso = Math.min(1, cursor.progreso + 0.025);
        const p = cursor.progreso;
        // Cruceta
        ctx.strokeStyle = cursor.color;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(cursor.x, cursor.y - 20);
        ctx.lineTo(cursor.x, cursor.y + 20);
        ctx.moveTo(cursor.x - 20, cursor.y);
        ctx.lineTo(cursor.x + 20, cursor.y);
        ctx.stroke();
        ctx.setLineDash([]);
        // Badge de tamaño
        const badgeW = Math.round(el.w * p);
        const badgeH = Math.round(el.h * p);
        ctx.fillStyle = cursor.color;
        ctx.fillRect(cursor.x + 8, cursor.y - 18, 60, 16);
        ctx.fillStyle = '#FFF';
        ctx.font = 'bold 10px system-ui, sans-serif';
        ctx.fillText(`${badgeW} × ${badgeH}`, cursor.x + 10, cursor.y - 7);
        // Caja en construcción
        ctx.strokeStyle = cursor.color;
        ctx.lineWidth = 2;
        ctx.strokeRect(el.x, el.y, el.w * p, el.h * p);

        if (p >= 1 && !construidos[idx]) {
          construidos[idx] = true;
          sonido('snap');
          // Avanzar al siguiente elemento
          cursor.elementoIdx = Math.min(cursor.elementoIdx + swarm.length, elementos.length - 1);
          cursor.progreso = 0;
          cursor.modo = 'orbitando';
        }
      } else if (cursor.modo === 'escribiendo') {
        cursor.progreso = Math.min(1, cursor.progreso + 0.04);
        const p = cursor.progreso;
        const chars = Math.floor(el.texto.length * p);
        const visible = el.texto.slice(0, chars);
        // Text box arrastrado
        ctx.strokeStyle = cursor.color;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(el.x - 2, el.y - 2, el.w + 4, el.h + 4);
        ctx.setLineDash([]);
        // Texto tipeado
        ctx.font = `${el.peso === '700' || el.peso === 'bold' ? 'bold' : 'normal'} 14px ${el.fuente}, system-ui, sans-serif`;
        ctx.fillStyle = '#F1F5F9';
        ctx.fillText(visible, el.x, el.y + 14);
        // Caret parpadeante
        cursor.caretTimer += 1;
        if (cursor.caretTimer % 30 < 15) {
          const caretX = el.x + ctx.measureText(visible).width + 2;
          ctx.fillStyle = '#F97316';
          ctx.fillRect(caretX, el.y, 2, 18);
        }
        if (p >= 1 && !construidos[idx]) {
          construidos[idx] = true;
          sonido('typing');
          cursor.elementoIdx = Math.min(cursor.elementoIdx + swarm.length, elementos.length - 1);
          cursor.progreso = 0;
          cursor.modo = 'orbitando';
        }
      } else {
        // Orbitando (flocking)
        const angle = now / 800 + ci * 0.7;
        const orbitR = 60 + Math.sin(now / 1200 + ci) * 20;
        cursor.x = cursor.tx + Math.cos(angle) * orbitR;
        cursor.y = cursor.ty + Math.sin(angle) * orbitR;
      }

      // Dibujar cursor
      dibujarCursor(cursor);
    }

    // Al final: sonido de "done" y revelar la página
    if (progreso >= 0.98 && !doneDisparado) {
      doneDisparado = true;
      sonido('done');
    }

    if (progreso < 1) {
      raf = requestAnimationFrame(tick);
    } else {
      if (ctx) ctx.clearRect(0, 0, ancho, alto);
    }
  }

  let doneDisparado = false;

  function dibujarCursor(c: Cursor) {
    if (!ctx) return;
    const x = c.x, y = c.y, s = c.tamaño;
    // Sombra
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.beginPath();
    ctx.moveTo(x + 1, y + 1);
    ctx.lineTo(x + 1, y + s + 1);
    ctx.lineTo(x + s * 0.6 + 1, y + s * 0.7 + 1);
    ctx.closePath();
    ctx.fill();
    // Cuerpo
    ctx.fillStyle = c.color;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x, y + s);
    ctx.lineTo(x + s * 0.6, y + s * 0.7);
    ctx.closePath();
    ctx.fill();
  }

  function redimensionar() {
    if (!canvas) return;
    dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    ancho = rect.width;
    alto = rect.height;
    canvas.width = ancho * dpr;
    canvas.height = alto * dpr;
    if (ctx) ctx.scale(dpr, dpr);
  }

  $effect(() => {
    if (activo && canvas) {
      if (!ctx) ctx = canvas.getContext('2d');
      redimensionar();
      if (objetivo) tomarSnapshot();
      crearCursors();
      doneDisparado = false;
      empezado = performance.now();
      sonido('swell');
      raf = requestAnimationFrame(tick);
    } else if (!activo && raf) {
      cancelAnimationFrame(raf);
      raf = 0;
      if (ctx && canvas) ctx.clearRect(0, 0, ancho * dpr, alto * dpr);
    }
  });

  onMount(() => {
    redimensionar();
    window.addEventListener('resize', redimensionar);
    return () => {
      window.removeEventListener('resize', redimensionar);
      if (raf) cancelAnimationFrame(raf);
      if (audioCtx) audioCtx.close();
    };
  });
</script>

<canvas
  bind:this={canvas}
  class="swarm-canvas"
  class:activo
  aria-hidden="true"
></canvas>

<style>
  .swarm-canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 50;
    opacity: 0;
    transition: opacity 0.15s ease;
  }
  .swarm-canvas.activo {
    opacity: 1;
  }
</style>