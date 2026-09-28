import adapter from '@sveltejs/adapter-static';

/**
 * App de UNA sola página (el kiosco), servida como estático por nginx.
 * `fallback: 'index.html'` porque es SPA: cualquier ruta unknown → el index.
 */
const config = {
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',
			precompress: false,
			strict: true
		})
	}
};

export default config;
