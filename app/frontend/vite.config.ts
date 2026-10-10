import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

// Single-file build: Streamlit embeds this as one inlined HTML string via
// components.v1.html, so there's no static file server to point separate
// JS/CSS assets at.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    cssCodeSplit: false,
  },
})
