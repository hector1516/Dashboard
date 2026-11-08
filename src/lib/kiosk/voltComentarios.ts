// Comentarios hilarantes de Volt según el tipo de evento/notificación
// Volt es un robot LED industrial con personalidad sarcástica pero amable

const COMENTARIOS: Record<string, string[]> = {
	// Kilómetros registrados
	km: [
		'¡Otro km más! El odómetro sufre más que yo...',
		'¿En serio otro viaje? Mi batería no aguanta tanto...',
		'Kilómetros acumulados: más que mi paciencia.',
		'El odómetro dice que sí, mi motivación dice que no.',
		'¿Ya van a pedir servicio? El auto ya ni respira.',
		'Más kilómetros que un taxi en hora pico.',
	],

	// Ticket OxxoGas
	ticket: [
		'Combustible para seguir... ¿o para ir a comer?',
		'Gasolina: el combustible del progreso... y de los tacos.',
		'¿Otro ticket? La tarjeta Go Vale ya no da abasto.',
		'Combustible registrado. Ahora sí, a trabajar... o a descansar.',
		'El auto come más que un adolescente en crecimiento.',
	],

	// Reporte firmado
	firmado: [
		'¡Firmado! Ahora sí, a cobrar...',
		'Otro reporte menos, otra alegría más.',
		'Firmado y sellado. Como mi destino.',
		'¿Ya van a pagar? O solo era para presumir...',
		'Reporte firmado. El cliente va a estar feliz... o no.',
		'¡Éxito! Ahora el técnico puede ir por sus tacos.',
	],

	// Cumpleaños
	cumple: [
		'¡Feliz cumple! Que te regalen un día sin reuniones.',
		'Un año más de sabiduría... o de arrugas.',
		'¡Felicidades! El pastel es lo único que importa.',
		'Un año más viejo, pero igual de guapo/a.',
		'Que los años te traigan más días de vacaciones.',
	],

	// Aniversario
	aniversario: [
		'¡Aniversario! Otro año sobreviviendo a ECCSA.',
		'¡Felicidades por el aniversario! Ya casi jubilación... casi.',
		'Un año más en la empresa. El café lo celebra contigo.',
	],

	// Entrada
	entrada: [
		'¡Llegó! Ya se puede empezar a trabajar... o a procrastinar.',
		'Buenos días, el café ya está listo.',
		'Entró alguien. ¿Será que hoy sí trabajan?',
		'¡Bienvenido/a! El aire acondicionado te estaba esperando.',
		'Ya llegó. Ahora sí, a fingir que se trabaja.',
	],

	// Salida
	salida: [
		'¡Se fue! Ahora sí, a descansar.',
		'Ya se fue, ahora podemos hablar de él/ella.',
		'Salió. La oficina se queda más tranquila.',
		'¡Hasta mañana! O hasta el lunes... o nunca.',
		'Se fue a casa. Yo me quedo aquí, como siempre.',
	],

	// Alerta
	alerta: [
		'Atención, atención... dice el jefe.',
		'Esto suena importante... o no.',
		'Alerta roja. O ámbar. O lo que sea.',
		'Algo pasó. ¿Será grave? Probablemente no.',
		'Notificación importante: alguien hizo algo.',
	],

	// Sin movimiento
	sinmovimiento: [
		'¿Alguien sigue vivo ahí?',
		'6 horas sin movimiento... ¿será que todos se fueron?',
		'Silencio total. Hasta yo me aburro.',
		'¿Se acabó el trabajo o se acabó la gente?',
		'Oficina fantasma detectada. Activando modo ahorro.',
	],

	// Degradado / error
	degradado: [
		'Algo falló... como mi batería al 1%.',
		'Error 404: motivación no encontrada.',
		'Sistema degradado. Como mi humor los lunes.',
		'Algo no funciona. ¿Será que es lunes?',
		'Error detectado. Yo también estoy cansado.',
	],

	// Aviso genérico
	aviso: [
		'Atención, por favor. O no. Lo que tú digas.',
		'Nuevo aviso. ¿Será importante? Probablemente.',
		'Mensaje del administrador. Lo leí por ti.',
		'Alguien tiene algo que decir. Escuchemos... o no.',
	],

	// Reporte nuevo
	reporte: [
		'Nuevo reporte. Otro día, otro documento.',
		'Reporte recibido. ¿Será de los buenos?',
		'Un reporte más para la colección.',
		'Nuevo reporte de servicio. Que alguien lo revise.',
	],

	// Combustible
	combustible: [
		'El auto necesita combustible. Como yo necesito café.',
		'Combustible bajo. ¿Alguien va a cargar?',
		'El tanque está vacío. Como mi paciencia.',
	],

	// Default / idle
	idle: [
		'Aquí estoy, como siempre. Sin que nadie me haga caso.',
		'Volt en servicio. Nadie me pregunta cómo estoy.',
		'Funcionando al 100%. O al 80%. No estoy seguro.',
		'Observando, analizando, juzgando... digo, ayudando.',
		'¿Alguien necesita algo? No, solo pregunto.',
		'Yo aquí, esperando que alguien me hable.',
	],
};

// Función para obtener un comentario aleatorio según el tipo de evento
export function getVoltComentario(tipo: string): string {
	const lista = COMENTARIOS[tipo] || COMENTARIOS['idle'];
	return lista[Math.floor(Math.random() * lista.length)];
}

// Función para determinar el tipo de evento a partir del evento del kiosco
export function getTipoEvento(evento: { titulo?: string; nivel?: string; modulo?: string }): string {
	const titulo = (evento.titulo || '').toLowerCase();
	const nivel = (evento.nivel || '').toLowerCase();
	const modulo = (evento.modulo || '').toLowerCase();

	if (titulo.includes('cumple') || titulo.includes('aniversario')) return 'cumple';
	if (titulo.includes('firmado')) return 'firmado';
	if (titulo.includes('entró') || titulo.includes('entro')) return 'entrada';
	if (titulo.includes('salió') || titulo.includes('salio')) return 'salida';
	if (titulo.includes('km') || titulo.includes('kilómetro') || titulo.includes('kilometro')) return 'km';
	if (titulo.includes('ticket') || titulo.includes('oxxo')) return 'ticket';
	if (titulo.includes('reporte')) return 'reporte';
	if (nivel === 'alerta') return 'alerta';
	if (modulo.includes('combustible')) return 'combustible';
	return 'aviso';
}