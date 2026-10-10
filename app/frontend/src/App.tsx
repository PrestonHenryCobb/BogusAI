import Dither from './components/Dither'

// Ink-navy to match the rest of the UI (app/main.py), not Dither's black default.
const BACKGROUND_COLOR: [number, number, number] = [11 / 255, 18 / 255, 32 / 255]
const WAVE_COLOR: [number, number, number] = [0.3686274509803922, 0.3568627450980392, 0.5176470588235295]

export default function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <Dither
        waveColor={WAVE_COLOR}
        backgroundColor={BACKGROUND_COLOR}
        disableAnimation={false}
        enableMouseInteraction={false}
        mouseRadius={0.1}
        colorNum={5.8}
        waveAmplitude={0.3}
        waveFrequency={3}
        waveSpeed={0.05}
      />
    </div>
  )
}
