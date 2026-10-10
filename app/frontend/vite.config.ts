import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

// Single self-contained index.html, built straight into app/static/background/
// so Streamlit's static file server can serve it at a real URL (st.iframe with
// a src= URL, not srcdoc -- srcdoc sandboxed iframes were silently freezing
// three.js's render loop under Streamlit; see app/background.py).
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  build: {
    cssCodeSplit: false,
    outDir: '../static/background',
    emptyOutDir: true,
  },
})
