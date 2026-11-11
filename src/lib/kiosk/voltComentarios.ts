// Comentarios hilarantes de Volt segun el tipo de evento/notificacion
// Volt es un robot LED industrial con personalidad sarcastica pero amable

const COMENTARIOS: Record<string, string[]> = {
	// Kilometros registrados
	km: [
		'Otro km mas! El odometro sufre mas que yo...',
		'En serio otro viaje? Mi bateria no aguanta tanto...',
		'Kilometros acumulados: mas que mi paciencia.',
		'El odometro dice que si, mi motivacion dice que no.',
		'Ya van a pedir servicio? El auto ya ni respira.',
		'Mas kilometros que un taxi en hora pico.',
	],

	// Ticket OxxoGas
	ticket: [
		'Combustible para seguir... o para ir a comer?',
		'Gasolina: el combustible del progreso... y de los tacos.',
		'Otro ticket? La tarjeta Go Vale ya no da abasto.',
		'Combustible registrado. Ahora si, a trabajar... o a descansar.',
		'El auto come mas que un adolescente en crecimiento.',
	],

	// Reporte firmado
	firmado: [
		'Firmado! Ahora si, a cobrar...',
		'Otro reporte menos, otra alegria mas.',
		'Firmado y sellado. Como mi destino.',
		'Ya van a pagar? O solo era para presumir...',
		'Reporte firmado. El cliente va a estar feliz... o no.',
		'Exito! Ahora el tecnico puede ir por sus tacos.',
	],

	// Cumpleanos
	cumple: [
		'Feliz cumple! Que te regalen un dia sin reuniones.',
		'Un ano mas de sabiduria... o de arrugas.',
		'Felicidades! El pastel es lo unico que importa.',
		'Un ano mas viejo, pero igual de guapo/a.',
		'Que los anos te traigan mas dias de vacaciones.',
	],

	// Aniversario
	aniversario: [
		'Aniversario! Otro ano sobreviviendo a ECCSA.',
		'Felicidades por el aniversario! Ya casi jubilacion... casi.',
		'Un ano mas en la empresa. El cafe lo celebra contigo.',
	],

	// Entrada - mas hilarantes sobre usuarios
	entrada: [
		'Llego! Ya se puede empezar a trabajar... o a procrastinar.',
		'Buenos dias, el cafe ya esta listo.',
		'Entro alguien. Sera que hoy si trabajan?',
		'Bienvenido/a! El aire acondicionado te estaba esperando.',
		'Ya llego. Ahora si, a fingir que se trabaja.',
		'Otro dia, otra oportunidad de hacer lo mismo de siempre.',
		'Llego el jefe... digo, el companero.',
		'Entrada registrada. Que comience el show.',
		'Ya esta aqui. Ahora si, a simular productividad.',
		'Llego con cara de lunes... y es miercoles.',
		'Biometrico marcado. El sistema cree que trabajas.',
		'Entrada detectada. Alerta: nivel de energia bajo.',
		'Llego. El cafe ya lo estaba esperando... como siempre.',
		'Nuevo dia, mismas caras, mismo cafe.',
		'Llego. El aire acondicionado se emociona.',
	],

	// Salida - mas hilarantes sobre usuarios
	salida: [
		'Se fue! Ahora si, a descansar.',
		'Ya se fue, ahora podemos hablar de el/ella.',
		'Salio. La oficina se queda mas tranquila.',
		'Hasta manana! O hasta el lunes... o nunca.',
		'Se fue a casa. Yo me quedo aqui, como siempre.',
		'Salida registrada. La oficina respira aliviada.',
		'Se fue. Ahora si, a hacer lo que realmente queremos.',
		'Adios! Que disfrute su libertad... temporal.',
		'Salio corriendo. O caminando. No se distingue.',
		'Se fue. El aire acondicionado se pone triste.',
		'Salida detectada. Nivel de productividad: 0%.',
		'Se fue. Ahora la oficina es mia... y del cafe.',
		'Adios companero. Nos vemos manana... o el lunes.',
		'Salio. El silencio reina. Paz.',
	],

	// Usuarios nuevos / registrados
	usuario_nuevo: [
		'Nuevo usuario registrado! Otro mas para la coleccion.',
		'Bienvenido/a al club. El cafe es gratis... el estres no.',
		'Nuevo miembro! Ya veras como se sufre aqui.',
		'Alguien nuevo! Ojala dure mas que el cafe.',
		'Nuevo usuario. Que la fuerza te acompañe... la necesitaras.',
		'Registrado! Ahora ya no hay vuelta atras.',
		'Bienvenido/a. El aire acondicionado te adopta.',
		'Nuevo en el sistema. El sistema te adopta... como a todos.',
		'Un nuevo valiente! O ingenuo. Ya veremos.',
		'Usuario registrado. Que comience la aventura... o la pesadilla.',
	],

	// Usuarios inactivos
	usuario_inactivo: [
		'Alguien no ha venido en dias... se fue de vacaciones o renuncio?',
		'Usuario inactivo detectado. O se fue de vacaciones o se perdio.',
		'Ya no viene. O se fue o se escondio.',
		'Inactivo. Como mi motivacion los lunes.',
		'No viene. El aire acondicionado lo extrana.',
		'Usuario fantasma. Aparece en el sistema pero no en persona.',
		'Ausente. Como mi paciencia en reuniones largas.',
	],

	// Alerta
	alerta: [
		'Atencion, atencion... dice el jefe.',
		'Esto suena importante... o no.',
		'Alerta roja. O ambar. O lo que sea.',
		'Algo paso. Sera grave? Probablemente no.',
		'Notificacion importante: alguien hizo algo.',
	],

	// Sin movimiento
	sinmovimiento: [
		'Alguien sigue vivo ahi?',
		'6 horas sin movimiento... sera que todos se fueron?',
		'Silencio total. Hasta yo me aburro.',
		'Se acabo el trabajo o se acabo la gente?',
		'Oficina fantasma detectada. Activando modo ahorro.',
	],

	// Degradado / error
	degradado: [
		'Algo fallo... como mi bateria al 1%.',
		'Error 404: motivacion no encontrada.',
		'Sistema degradado. Como mi humor los lunes.',
		'Algo no funciona. Sera que es lunes?',
		'Error detectado. Yo tambien estoy cansado.',
	],

	// Aviso generico
	aviso: [
		'Atencion, por favor. O no. Lo que tu digas.',
		'Nuevo aviso. Sera importante? Probablemente.',
		'Mensaje del administrador. Lo lei por ti.',
		'Alguien tiene algo que decir. Escuchemos... o no.',
	],

	// Reporte nuevo
	reporte: [
		'Nuevo reporte. Otro dia, otro documento.',
		'Reporte recibido. Sera de los buenos?',
		'Un reporte mas para la coleccion.',
		'Nuevo reporte de servicio. Que alguien lo revise.',
	],

	// Combustible
	combustible: [
		'El auto necesita combustible. Como yo necesito cafe.',
		'Combustible bajo. Alguien va a cargar?',
		'El tanque esta vacio. Como mi paciencia.',
	],

	// Pantallas del kiosco - comentarios hilarantes por pantalla
	screen_clima: [
		'Clima: el unico tema de conversacion cuando no sabes que decir.',
		'El clima dice que llueve. Yo digo que necesito sombrilla.',
		'Temperatura perfecta para... quedarse en casa.',
		'Clima actualizado. Como si alguien fuera a salir.',
		'Que calor! O que frio! O que... me da igual.',
		'El clima: la unica cosa que nadie puede controlar... excepto yo.',
		'Lluvia detectada. El trafico se duplica. La paciencia se divide.',
		'Soleado! Perfecto para... estar en la oficina con aire acondicionado.',
	],

	screen_asistencia: [
		'Asistencia: quien vino y quien... "trabajo desde casa".',
		'Lista de asistencia. Los que faltan ya saben que se les va a preguntar.',
		'Asistencia registrada. El biometrico miente por todos.',
		'Quien vino hoy? Los valientes. Los demas... "en home office".',
		'Asistencia del dia. Los que no vinieron tienen "cita medica".',
		'Presentes y ausentes. Los ausentes tienen excusa. Los presentes tienen cafe.',
	],

	screen_actividad: [
		'Actividad: lo que hicieron... o lo que dicen que hicieron.',
		'Reporte de actividad. La productividad es un concepto relativo.',
		'Actividad registrada. Alguien si trabajo hoy.',
		'Lo que se hizo hoy. O lo que se deberia haber hecho.',
		'Actividad del dia: reuniones, cafe, y algo de trabajo.',
		'Actividad registrada. El trabajo es... opcional, segun el humor.',
	],

	screen_equipo: [
		'El equipo: los que estan y los que... bueno, estan en el sistema.',
		'Equipo de trabajo. O de... supervivencia.',
		'Nuestro equipo. Cada quien con su rol... y su cafe.',
		'El equipo completo. O casi completo. Los demas estan "en campo".',
		'Equipo reunido... virtualmente. Como siempre.',
		'El equipo: unidos por el cafe y separados por el trafico.',
	],

	screen_portada: [
		'Portada: la cara de ECCSA. Con cafe y aire acondicionado.',
		'Portada del kiosco. La primera impresion... es que hay cafe.',
		'Portada: donde todo empieza... y donde el cafe nunca falta.',
		'La portada. Lo primero que ven. Lo ultimo que recuerdan.',
		'Portada: ECCSA en todo su esplendor... y con cafe.',
	],

	screen_uso_apps: [
		'Uso de apps: quien usa que y por cuanto tiempo. Big Brother is watching.',
		'Uso de aplicaciones. Alguien si trabaja... en las apps.',
		'Apps mas usadas. El navegador gana. Como siempre.',
		'Uso de apps: trabajo o procrastinacion? El sistema no distingue.',
		'Que apps usan? Probablemente Netflix... digo, el ERP.',
		'Uso de aplicaciones. El cafe app no cuenta... pero deberia.',
	],

	screen_sabias_que: [
		'Sabias que... probablemente no. Pero ahora si.',
		'Dato curioso: como el cafe, pero para el cerebro.',
		'Sabias que... el cafe es mejor que los datos curiosos. Pero aun asi.',
		'Dato del dia. Para presumir en la comida.',
		'Sabias que... yo se todo. Pero solo comparto un poco.',
		'Dato curioso: porque el conocimiento es poder... y cafe.',
	],

	screen_combustible: [
		'Combustible: el auto come mas que yo... y eso es mucho decir.',
		'Combustible registrado. El auto es feliz. Yo no tanto.',
		'Gasolina: el eterno gasto. Como el cafe, pero para el auto.',
		'Combustible: porque el auto no funciona con cafe... lamentablemente.',
		'Tanque lleno! El auto. Yo sigo vacio... de cafe.',
	],

	screen_legends: [
		'Legends: los puntos que todos quieren y nadie entiende como se ganan.',
		'Legends: el sistema de puntos que motiva... o desmotiva.',
		'Puntos Legends. Como los puntos del carnet, pero mas cool.',
		'Legends: porque el trabajo sin puntos es solo... trabajo.',
		'Puntos acumulados. El ranking esta que arde.',
	],

	screen_reportes: [
		'Reportes: lo que se hizo, lo que se dice que se hizo, y lo que se va a hacer.',
		'Reportes de servicio. La verdad, la mentira, y el cafe.',
		'Nuevo reporte. Otro documento para la coleccion.',
		'Reportes: porque sin documentacion no paso nada.',
		'El reporte dice que todo bien. El reporte miente.',
	],

	screen_tickets: [
		'Tickets: el combustible del auto... y de la empresa.',
		'Tickets OxxoGas. El auto come, la empresa paga.',
		'Ticket registrado. El auto agradece.',
		'Tickets: porque sin combustible no hay kilómetros.',
		'Otro ticket. El auto esta feliz. La tarjeta no.',
	],

	screen_notas: [
		'Notas: lo que alguien escribio y todos ignoran.',
		'Notas del kiosco. La pizarra digital que nadie lee.',
		'Notas: recordatorios que se olvidan.',
		'Notas: como post-its, pero mas grandes y mas ignoradas.',
		'Alguien dejo una nota. Nadie la leera. Pero esta ahi.',
	],

	screen_celebraciones: [
		'Celebraciones: porque alguien cumplio anos o sobrevivio un ano mas.',
		'Celebraciones! El pastel es lo unico que importa.',
		'Festejando! Porque el trabajo sin fiesta es solo... trabajo.',
		'Celebracion detectada. Que alguien traiga pastel.',
		'Fiesta! El unico momento en que todos estan felices.',
	],

	screen_fotos: [
		'Fotos: los recuerdos que nadie pidio pero todos disfrutan.',
		'Fotos del equipo. Sonriendo porque el jefe dijo "sonrian".',
		'Fotos: porque sin evidencia no paso nada.',
		'Album de fotos. Los recuerdos... y las caras de sueno.',
		'Fotos: el unico lugar donde todos se ven bien... con filtro.',
	],

	screen_metricas: [
		'Metricas: los numeros que el jefe ve y nadie entiende.',
		'Metricas del dia. Los numeros dicen todo... o nada.',
		'KPIs, metricas, indicadores. Palabras que suenan importantes.',
		'Metricas: porque sin numeros no hay junta.',
		'Los numeros del dia. Subieron o bajaron? Depende del humor.',
	],

	screen_pulso: [
		'Pulso: el latido de la oficina. O el eco del silencio.',
		'Pulso: quien esta activo y quien... no.',
		'Pulso del equipo. El corazon de ECCSA.',
		'Pulso: los que estan y los que... bueno.',
		'El pulso: porque saber quien esta vivo es importante.',
	],

	screen_ingenieria_campo: [
		'Ingenieria de campo: los que salen a la calle y los que... se quedan.',
		'Campo: donde el trabajo es real y el cafe es lejos.',
		'Ingenieria de campo. Los valientes que salen de la oficina.',
		'Campo: porque alguien tiene que ir... y no soy yo.',
		'Trabajo de campo: el que se hace lejos del aire acondicionado.',
	],

	// Default / idle
	idle: [
		'Aqui estoy, como siempre. Sin que nadie me haga caso.',
		'Volt en servicio. Nadie me pregunta como estoy.',
		'Funcionando al 100%. O al 80%. No estoy seguro.',
		'Observando, analizando, juzgando... digo, ayudando.',
		'Alguien necesita algo? No, solo pregunto.',
		'Yo aqui, esperando que alguien me hable.',
	],
};

// Funcion para obtener un comentario aleatorio segun el tipo de evento
export function getVoltComentario(tipo: string): string {
	const lista = COMENTARIOS[tipo] || COMENTARIOS['idle'];
	return lista[Math.floor(Math.random() * lista.length)];
}

// Funcion para obtener un comentario segun la pantalla actual
export function getVoltComentarioPantalla(screenId: string): string {
	const key = `screen_${screenId}`;
	const lista = COMENTARIOS[key] || COMENTARIOS['idle'];
	return lista[Math.floor(Math.random() * lista.length)];
}

// Funcion para determinar el tipo de evento a partir del evento del kiosco
export function getTipoEvento(evento: { titulo?: string; nivel?: string; modulo?: string }): string {
	const titulo = (evento.titulo || '').toLowerCase();
	const nivel = (evento.nivel || '').toLowerCase();
	const modulo = (evento.modulo || '').toLowerCase();

	if (titulo.includes('cumple') || titulo.includes('aniversario')) return 'cumple';
	if (titulo.includes('firmado')) return 'firmado';
	if (titulo.includes('entro') || titulo.includes('entro')) return 'entrada';
	if (titulo.includes('salio') || titulo.includes('salio')) return 'salida';
	if (titulo.includes('km') || titulo.includes('kilometro') || titulo.includes('kilometro')) return 'km';
	if (titulo.includes('ticket') || titulo.includes('oxxo')) return 'ticket';
	if (titulo.includes('reporte')) return 'reporte';
	if (nivel === 'alerta') return 'alerta';
	if (modulo.includes('combustible')) return 'combustible';
	return 'aviso';
}