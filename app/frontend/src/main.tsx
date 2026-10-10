import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { enhanceParent } from './enhanceParent.ts'

enhanceParent()
createRoot(document.getElementById('root')!).render(<App />)
