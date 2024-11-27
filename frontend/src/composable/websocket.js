
import { ref } from 'vue'

export function useWebsocket(url = 'ws://localhost:8000/ws') {
    const dataRef = ref(null)
    const isSocketOpen = ref(false)

    let timer = null
    let socket = null
    function connect(url) {
        socket = new WebSocket(url)
        socket.onerror = (event) => {
            console.error(event)
            socket.close()
        }
        socket.onmessage = (event) => {
            // Expect event.data to be string json
            const jsonData = JSON.parse(event.data)
            dataRef.value = jsonData
        }
        socket.onopen = () => {
            if (timer != null) clearInterval(timer)
            isSocketOpen.value = true
            socket.onclose = () => {
                isSocketOpen.value = false
                timer = setInterval(() => {
                    connect(url)
                }, 5000);
            }
        }
    }
    connect(url)
    return { dataRef, isSocketOpen }
}