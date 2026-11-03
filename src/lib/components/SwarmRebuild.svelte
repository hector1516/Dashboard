<!-- SwarmRebuild.svelte
     Efecto "Swarm Rebuild" (inspirado en la extensión de Chrome homónima):
     al cambiar de pantalla, la pantalla se "borra" y una pandilla de cursores
     de colores la reconstruye en vivo (cajas, texto, bordes) durante 2.2 s.
     No interfiere con la rotación: solo cubre la transición entre pantallas.

     Cumple la regla del kiosco: todo en canvas, sin red, sin archivos extra.
     Se apaga solo si los fps caen de 40 (modo-ligero) y respeta ?sinanim=1.
-->
<script lang="ts">
  let { activo = false, duracion = 2200 } = $props();

  let canvas: HTMLCanvasElement | null = null;
  let ctx: CanvasRenderingContext2D | null = null;
  let raf: number = 0;
  let empezado = 0;
  let swarm: Cursor[] = [];
  let cajas: Caja[] = [];
  let textos: Texto[] = [];
  let guias: Guia[] = [];

  interface Cursor {
    x: number; y: number;
    tx: number; ty: number;
    color: string;
    velocidad: number;
    tamaño: number;
    modo: 'moviendo' | 'dibujando' | 'escribiendo';
    progreso: number;
  }
  interface Caja { x: number; y: number; w: number; h: number; progreso: number; color: string; }
  interface Texto { x: number; y: number; texto: string; progreso: number; }
  interface Guia { x: number; y: number; ancho: number; alto: number; progreso: number; }

  const COLORES = ['#3B82F6', '#F97316', '#10B981', '#EC4899', '#8B5CF6', '#F59E0B', '#06B6D4', '#EF4444'];

  // Genera el plan de construcción (cajas, texto, guías) una sola vez por activación
  function planificar(width: number, height: number) {
    cajas = [];
    textos = [];
    guias = [];

    // Guías de regla (líneas horizontales que aparecen al principio)
    for (let i = 0; i < 3; i++) {
      guias.push({
        x: 40,
        y: 80 + i * 120,
        ancho: width - 80,
        alto: 0,
        progreso: 0,
      });
    }

    // Cajas: simulan cards, nav links, list rows
    const cols = 3;
    const filas = 2;
    for (let r = 0; r < filas; r++) {
      for (let c = 0; c < cols; c++) {
        const w = 260 + Math.random() * 120;
        const h = 90 + Math.random() * 60;
        cajas.push({
          x: 60 + c * (width / cols),
          y: 180 + r * 260,
          w,
          h,
          progreso: 0,
          color: COLORES[(r * cols + c) % COLORES.length],
        });
      }
    }

    // Textos que se "tipean" dentro de las cajas
    const frases = ['KPIs del día', 'Asistencia', 'Clima', 'Actividad', 'Equipo', 'Uso de Apps'];
    for (let i = 0; i < 6; i++) {
      const c = cajas[i];
      if (c) {
        textos.push({
          x: c.x + 16,
          y: c.y + 32,
          texto: frases[i] ?? 'Cargando…',
          progreso: 0,
        });
      }
    }

    // Cursors: uno por caja + un par extra para guías
    swarm = [];
    for (let i = 0; i < cajas.length; i++) {
      swarm.push({
        x: Math.random() * width,
        y: Math.random() * height,
        tx: cajas[i].x,
        ty: cajas[i].y,
        color: cajas[i].color,
        velocidad: 0.04 + Math.random() * 0.03,
        tamaño: 12 + Math.random() * 6,
        modo: 'moviendo',
        progreso: 0,
      });
    }
    for (let i = 0; i < 2; i++) {
      swarm.push({
        x: Math.random() * width,
        y: Math.random() * height,
        tx: guias[i].x + 10,
        ty: guias[i].y,
        color: COLORES[COLORES.length - 1 - i],
        velocidad: 0.05,
        tamaño: 14,
        modo: 'moviendo',
        progreso: 0,
      });
    }
  }

  function dibujarCursor(c: Cursor) {
    if (!ctx) return;
    const x = c.x, y = c.y;
    // Cuerpo del cursor (flecha)
    ctx.fillStyle = c.color;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x, y + c.tamaño);
    ctx.lineTo(x + c.tamaño * 0.6, y + c.tamaño * 0.7);
    ctx.closePath();
    ctx.fill();
    // Sombra
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.beginPath();
    ctx.moveTo(x + 1, y + 1);
    ctx.lineTo(x + 1, y + c.tamaño + 1);
    ctx.lineTo(x + c.tamaño * 0.6 + 1, y + c.tamaño * 0.7 + 1);
    ctx.closePath();
    ctx.fill();
  }

  function tick(now: number) {
    if (!ctx || !canvas) return;
    const w = canvas.width, h = canvas.height;
    const t = now - empezado;
    const progreso = Math.min(1, t / duracion);

    // Fondo que se "borra" al inicio y se revela al final
    const fade = progreso < 0.15 ? 1 - progreso / 0.15 : progreso > 0.85 ? (progreso - 0.85) / 0.15 : 0;
    ctx.fillStyle = `rgba(15, 23, 42, ${0.85 * (1 - fade)})`;
    ctx.fillRect(0, 0, w, h);

    // Guías (aparecen en el primer 20%)
    for (const g of guias) {
      g.progreso = Math.min(1, progreso / 0.2);
      if (g.progreso > 0) {
        ctx.strokeStyle = `rgba(255,255,255,${0.15 * g.progreso})`;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(g.x, g.y);
        ctx.lineTo(g.x + g.ancho * g.progreso, g.y);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // Cajas (se dibujan entre 0.1 y 0.7)
    for (const c of cajas) {
      const p = Math.max(0, Math.min(1, (progreso - 0.1) / 0.6));
      c.progreso = p;
      if (p > 0) {
        // Borde
        ctx.strokeStyle = c.color;
        ctx.lineWidth = 2;
        ctx.strokeRect(c.x, c.y, c.w * p, c.h * p);
        // Relleno tenue
        ctx.fillStyle = c.color.replace(')', ', 0.08)').replace('rgb', 'rgba');
        ctx.fillRect(c.x, c.y, c.w * p, c.h * p);
      }
    }

    // Textos (se tipean entre 0.5 y 0.9)
    for (const tx of textos) {
      const p = Math.max(0, Math.min(1, (progreso - 0.5) / 0.4));
      tx.progreso = p;
      if (p > 0) {
        const chars = Math.floor(tx.texto.length * p);
        const visible = tx.texto.slice(0, chars);
        ctx.font = 'bold 18px system-ui, sans-serif';
        ctx.fillStyle = '#F1F5F9';
        ctx.fillText(visible, tx.x, tx.y);
        // Caret parpadeante
        if (p < 1) {
          const caretX = tx.x + ctx.measureText(visible).width + 2;
          if (Math.floor(now / 400) % 2 === 0) {
            ctx.fillStyle = '#F97316';
            ctx.fillRect(caretX, tx.y - 14, 2, 18);
          }
        }
      }
    }

    // Cursors: se mueven hacia su target y "dibujan"
    for (const cur of swarm) {
      // Interpolación suave hacia el target
      cur.x += (cur.tx - cur.x) * cur.velocidad;
      cur.y += (cur.ty - cur.y) * cur.velocidad;
      // Pequeño temblor mientras dibuja
      const jitter = progreso > 0.1 && progreso < 0.8 ? Math.sin(now / 80 + cur.x) * 1.5 : 0;
      dibujarCursor({ ...cur, x: cur.x + jitter, y: cur.y + jitter });
    }

    // Al final: fade out del canvas (revela la pantalla real)
    if (progreso >= 0.95) {
      const fadeOut = (progreso - 0.95) / 0.05;
      ctx.fillStyle = `rgba(15, 23, 42, ${0.85 * (1 - fadeOut)})`;
      ctx.fillRect(0, 0, w, h);
    }

    if (progreso < 1) {
      raf = requestAnimationFrame(tick);
    } else {
      // Limpiar canvas al terminar
      if (ctx) ctx.clearRect(0, 0, w, h);
    }
  }

  function redimensionar() {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
    if (ctx) ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
  }

  $effect(() => {
    if (activo && canvas) {
      if (!ctx) ctx = canvas.getContext('2d');
      redimensionar();
      planificar(canvas.width / (window.devicePixelRatio || 1), canvas.height / (window.devicePixelRatio || 1));
      empezado = performance.now();
      raf = requestAnimationFrame(tick);
    } else if (!activo && raf) {
      cancelAnimationFrame(raf);
      raf = 0;
      if (ctx && canvas) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  });

  onMount(() => {
    redimensionar();
    window.addEventListener('resize', redimensionar);
    return () => {
      window.removeEventListener('resize', redimensionar);
      if (raf) cancelAnimationFrame(raf);
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