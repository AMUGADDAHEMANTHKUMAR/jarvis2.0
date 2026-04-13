import { initOrb, setState } from './orb'

const ws       = new WebSocket('ws://localhost:8000/ws')
const status   = document.getElementById('status')!
const transcript = document.getElementById('transcript')!
const response   = document.getElementById('response')!
const btnListen  = document.getElementById('btn-listen') as HTMLButtonElement
const btnDeep    = document.getElementById('btn-deep')  as HTMLButtonElement

let deepMode = false
let recognition: SpeechRecognition | null = null
let analyser: AnalyserNode | null = null

initOrb(document.getElementById('orb-container')!, (a: AnalyserNode) => { analyser = a })

btnDeep.addEventListener('click', () => {
  deepMode = !deepMode
  btnDeep.classList.toggle('active', deepMode)
  btnDeep.textContent = deepMode ? 'Deep ON' : 'Deep mode'
})

ws.onmessage = async (ev) => {
  const msg = JSON.parse(ev.data)
  if (msg.type === 'thinking') {
    setState('thinking'); status.textContent = 'thinking...'
    return
  }
  if (msg.type === 'response') {
    response.textContent = msg.text
    const audio = new Audio('data:audio/mp3;base64,' + msg.audio)
    setState('speaking')
    status.textContent = 'speaking'
    audio.play()
    audio.onended = () => { setState('idle'); status.textContent = 'idle' }
  }
}

btnListen.addEventListener('mousedown', startListening)
btnListen.addEventListener('mouseup',   stopListening)
btnListen.addEventListener('touchstart', startListening)
btnListen.addEventListener('touchend',   stopListening)

function startListening() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Use Chrome or Edge for voice recognition.')
    return
  }
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  recognition = new SR()
  recognition.continuous = false
  recognition.interimResults = true
  recognition.lang = 'en-US'

  recognition.onresult = (e: any) => {
    const t = Array.from(e.results).map((r: any) => r[0].transcript).join('')
    transcript.textContent = t
  }
  recognition.onend = () => {
    if (transcript.textContent) {
      ws.send(JSON.stringify({ text: transcript.textContent, deep: deepMode }))
      setState('listening'); status.textContent = 'processing...'
    }
  }
  setState('listening'); status.textContent = 'listening...'
  btnListen.classList.add('active')
  recognition.start()
}

function stopListening() {
  recognition?.stop()
  btnListen.classList.remove('active')
}