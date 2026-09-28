/**
 * Contrato de datos del kiosco.
 *
 * El backend (worker/snapshotter.py) produce EXACTAMENTE estas formas y las
 * guarda en /data/snapshot.json; la pantalla no consulta la BD nunca. Si se
 * toca un campo, se toca en los dos lados: este archivo y el SELECT que lo
 * llena. `schema_version` sube cuando el cambio sea incompatible, para que una
 * pantalla vieja con un snapshot nuevo sepa que no confiar.
 */

export type NivelEvento = 'info' | 'exito' | 'destaque' | 'alerta';

/** Sonido del aviso. Por defecto es el del nivel; algunos lo pisan. */
export type TonoEvento = NivelEvento | 'hola' | 'adios' | 'click';

/** Evento en vivo para el ticker / toast / toma de pantalla. */
export interface EventoKiosko {
	/** Estable y único: "km:51231", "rep:4471". Es lo que deduplica. */
	id: string;
	nivel: NivelEvento;
	/** Tono propio; si no viene, suena el del nivel. */
	tono?: TonoEvento;
	icono: string;
	titulo: string;
	texto: string;
	meta: string;
	ts: string;
	/** Thumb local, p. ej. /media/thumbs/tk_123_w480.jpg */
	imagen?: string;
	/** Si viene, el evento toma la pantalla completa este tiempo. */
	segundos?: number;
}

export interface VehiculoKm {
	Id: number;
	MarcaModelo: string;
	Placas: string;
	km_esta_semana: number | null;
	km_semana_pasada: number | null;
	registrado_semana: number;
	consumo_semana: number;
	/** Consumo en la ventana MÓVIL de 7 días: es la que se dibuja. */
	consumo_7d: number;
	/** 1 = no hay lectura anterior contra la cual restar (no se inventa). */
	sin_referencia: number;
	/** Último registro de la tabla (no solo de esta semana): para el radar. */
	ultimo_registro: string | null;
}

export interface Reporte {
	Folio: string;
	Cliente: string;
	ingeniero: string;
	fecha: string;
	Estatus: string;
}

export interface Ticket {
	folio: string;
	vehiculo: string;
	Placas: string;
	usuario: string;
	fecha: string;
	cliente: string;
	descripcion: string;
}

export interface Nota {
	Id: number;
	Titulo: string;
	Contenido: string;
	Color: string;
	Autor: string;
	Fija: number;
	fecha_creacion: string;
	fecha_modificado: string;
}

/**
 * Cumpleañero: la EDAD sale del RFC/CURP (posiciones 5-6 año, 7-8 mes, 9-10
 * día) o de `FechaNacimiento` si existe. El backend ya la calcula.
 */
export interface Cumpleanero {
	Nombre: string;
	dia: number | null;
	mes: number | null;
	edad: number | null;
	avatar: string | null;
}

/** Aniversario: años de antigüedad en ECCSA, desde `FechaIngreso`. */
export interface Aniversariero {
	Nombre: string;
	dia: number | null;
	anos: number | null;
	avatar: string | null;
}

export interface LegendRow {
	nombre: string;
	nickname: string;
	puntos: number;
	nivel: string;
	avatar: string | null;
	/** Puesto en el snapshot anterior, para dibujar la flecha ↑↓. */
	puesto_anterior: number | null;
}

export interface Snapshot {
	schema_version: number;
	generado_en: string;
	/** Vacío = todo bien. 'bd' | 'clima' | 'bing' | 'media'. */
	degradado: string[];
	/** 'bd' si este snapshot se acaba de calcular; 'cache' si se re-sirve viejo. */
	origen: 'bd' | 'cache';
	build: string;

	reportes: {
		total: number;
		firmados: number;
		pendientes: number;
		hoy: number;
		esta_semana: number;
		por_ingeniero: { nombre: string; firmados: number; pendientes: number; total: number }[];
		ultimos: Reporte[];
	};

	kilometros: {
		total_semana: number;
		hoy: number;
		por_vehiculo: VehiculoKm[];
		/** 7 puntos, de más viejo a más nuevo. */
		serie_7dias: { fecha: string; km: number; registros: number }[];
	};

	tickets: {
		total_semana: number;
		ultimos: Ticket[];
		por_vehiculo: { vehiculo: string; total_tickets: number }[];
	};

	legends: {
		ranking: LegendRow[];
		ganador_semana: { nombre: string; puntos: number; desde: string } | null;
		total_puntos: number;
		/** Cuenta regresiva al reinicio semanal (domingo 00:00). */
		reset_en_segundos: number;
	};

	fotos: { ids: { IdReporte: number; Folio: string; Cliente: string; ingeniero: string; Orden: number }[] };

	notas: Nota[];

	cumpleanos: { hoy: Cumpleanero[]; del_mes: Cumpleanero[] };
	aniversarios: { hoy: Aniversariero[]; del_mes: Aniversariero[] };

	metricas: {
		top_cliente: { Cliente: string; total: number } | null;
		top_ingeniero: { nombre: string; reportes: number; horas_totales: number } | null;
		/** Rejilla 7×24: por día de la semana y hora, cuántos eventos hubo. */
		pulso: { dia: number; hora: number; valor: number }[];
		actividad_hora: number;
		ultimo_evento: { texto: string; meta: string } | null;
		top_del_dia: { nombre: string; valor: number; unidad: string } | null;
	};

	clima: {
		actual: {
			temperatura: number | null;
			humedad: number | null;
			viento: number | null;
			codigo_clima: number;
			descripcion: string;
			icono: string;
			es_dia: boolean;
		};
		hoy: { max: number | null; min: number | null; prob_lluvia: number | null };
		manana: { max: number | null; min: number | null; prob_lluvia: number | null };
		leido_en: string | null;
	};

	/** Rutas locales de fondos. Nunca URLs de internet (ver AGENTS.md §Offline). */
	fondos: string[];

	/** Ancho con el que el backend generó los thumbs de fotos. */
	media?: { fotos_w: number };

	eventos: EventoKiosko[];
}

/** Pantallas de la rotación, en orden de presentación en el header. */
export interface PantallaDef {
	id: string;
	icono: string;
	label: string;
}
