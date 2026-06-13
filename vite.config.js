import { defineConfig } from 'vite';

export default defineConfig({
  root: 'docs',
  server: {
    port: 5173,
    host: true
  }
});
