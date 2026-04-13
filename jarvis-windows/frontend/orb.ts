import * as THREE from 'three'

type OrbState = 'idle' | 'listening' | 'thinking' | 'speaking'
let currentState: OrbState = 'idle'
let particles: THREE.Points
let clock: THREE.Clock

const STATE_COLORS: Record<OrbState, THREE.Color> = {
  idle:      new THREE.Color(0x334466),
  listening: new THREE.Color(0x22aaff),
  thinking:  new THREE.Color(0xffaa22),
  speaking:  new THREE.Color(0x44ffaa),
}

export function setState(s: OrbState) { currentState = s }

export function initOrb(container: HTMLElement, onAnalyser: (a: AnalyserNode) => void) {
  const W = container.clientWidth, H = container.clientHeight
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(W, H)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)

  const scene  = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 1000)
  camera.position.z = 3

  clock = new THREE.Clock()

  const COUNT = 2000
  const positions = new Float32Array(COUNT * 3)
  const colors    = new Float32Array(COUNT * 3)

  for (let i = 0; i < COUNT; i++) {
    const phi   = Math.acos(2 * Math.random() - 1)
    const theta = Math.random() * Math.PI * 2
    const r = 1 + (Math.random() - 0.5) * 0.4
    positions[i*3]   = r * Math.sin(phi) * Math.cos(theta)
    positions[i*3+1] = r * Math.sin(phi) * Math.sin(theta)
    positions[i*3+2] = r * Math.cos(phi)
    colors[i*3] = colors[i*3+1] = colors[i*3+2] = 1
  }

  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3))

  const mat = new THREE.PointsMaterial({
    size: 0.025, vertexColors: true, transparent: true, opacity: 0.85,
    blending: THREE.AdditiveBlending, depthWrite: false
  })

  particles = new THREE.Points(geo, mat)
  scene.add(particles)

  function animate() {
    requestAnimationFrame(animate)
    const t = clock.getElapsedTime()
    const col = STATE_COLORS[currentState]

    const pos = geo.attributes.position.array as Float32Array
    const c   = geo.attributes.color.array as Float32Array
    const speed = currentState === 'speaking' ? 0.6
                : currentState === 'thinking' ? 0.35
                : currentState === 'listening'? 0.2 : 0.05

    for (let i = 0; i < COUNT; i++) {
      const nx = pos[i*3] + Math.sin(t * speed + i * 0.05) * 0.002
      const ny = pos[i*3+1] + Math.cos(t * speed + i * 0.07) * 0.002
      pos[i*3] = nx; pos[i*3+1] = ny
      c[i*3]   = col.r; c[i*3+1] = col.g; c[i*3+2] = col.b
    }
    geo.attributes.position.needsUpdate = true
    geo.attributes.color.needsUpdate    = true

    particles.rotation.y = t * 0.08
    particles.rotation.x = Math.sin(t * 0.05) * 0.1
    renderer.render(scene, camera)
  }
  animate()
}