import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'

// A drifting link-analysis graph -- nodes connected by thin edges, like an
// investigator's corkboard of scam postings and how they relate. This is the
// one bold move in the design (per the design-plan critique): it stands in
// for "network of connected fraud," not decoration for its own sake.

const NODE_COUNT = 90
const VOLUME = 9
const LINK_DISTANCE = 2.3
const STEEL_BLUE = new THREE.Color('#5b7a9d')
const AMBER = new THREE.Color('#c98a2c')

function buildGraph() {
  const positions = new Float32Array(NODE_COUNT * 3)
  for (let i = 0; i < NODE_COUNT; i++) {
    positions[i * 3 + 0] = (Math.random() - 0.5) * VOLUME * 1.8
    positions[i * 3 + 1] = (Math.random() - 0.5) * VOLUME
    positions[i * 3 + 2] = (Math.random() - 0.5) * VOLUME
  }

  const linePositions: number[] = []
  const lineColors: number[] = []
  for (let i = 0; i < NODE_COUNT; i++) {
    const ax = positions[i * 3], ay = positions[i * 3 + 1], az = positions[i * 3 + 2]
    for (let j = i + 1; j < NODE_COUNT; j++) {
      const bx = positions[j * 3], by = positions[j * 3 + 1], bz = positions[j * 3 + 2]
      const d = Math.hypot(ax - bx, ay - by, az - bz)
      if (d < LINK_DISTANCE) {
        linePositions.push(ax, ay, az, bx, by, bz)
        // Rare edges read as a flagged cluster (amber) against the quiet steel-blue web.
        const color = Math.random() < 0.06 ? AMBER : STEEL_BLUE
        lineColors.push(color.r, color.g, color.b, color.r, color.g, color.b)
      }
    }
  }

  return {
    nodePositions: positions,
    linePositions: new Float32Array(linePositions),
    lineColors: new Float32Array(lineColors),
  }
}

function Graph() {
  const group = useRef<THREE.Group>(null)
  const { nodePositions, linePositions, lineColors } = useMemo(buildGraph, [])

  useFrame((_, delta) => {
    if (!group.current) return
    group.current.rotation.y += delta * 0.025
    group.current.rotation.x = Math.sin(Date.now() * 0.00005) * 0.08
  })

  return (
    <group ref={group}>
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
          <bufferAttribute attach="attributes-color" args={[lineColors, 3]} />
        </bufferGeometry>
        <lineBasicMaterial vertexColors transparent opacity={0.28} />
      </lineSegments>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[nodePositions, 3]} />
        </bufferGeometry>
        <pointsMaterial color={STEEL_BLUE} size={0.055} sizeAttenuation transparent opacity={0.85} />
      </points>
    </group>
  )
}

export default function Scene() {
  return (
    <Canvas
      camera={{ position: [0, 0, 7], fov: 50 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: false }}
      onCreated={({ gl }) => gl.setClearColor('#0b1220', 1)}
    >
      <Graph />
      <EffectComposer multisampling={0}>
        <Bloom luminanceThreshold={0.15} luminanceSmoothing={0.9} intensity={0.55} mipmapBlur />
      </EffectComposer>
    </Canvas>
  )
}
