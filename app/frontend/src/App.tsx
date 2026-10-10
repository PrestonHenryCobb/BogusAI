import GhostFibers from './components/GhostFibers'

export default function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <GhostFibers
        glowColor="#4f6fd8"
        lineColor="#c9d3f2"
        speed={0.2}
        scale={1.6}
        rotation={-28}
        rotationSpeed={0.25}
        layers={4}
        waves={0.015}
        twist={0.1}
        threads={1}
        spread={1}
        thickness={1.2}
        glow={3}
        brightness={2}
        vignette={0.6}
        grain={0.03}
        mouseInteraction={false}
        intro={false}
        lightMode={false}
        paused={false}
        dpr={Math.min(window.devicePixelRatio || 1, 1.5)}
      />
    </div>
  )
}
