// Hook que conecta al WebSocket del dashboard para recibir actualizaciones
// Construye la URL a partir de la variable de entorno y gestiona la reconexion
import { useMemo } from "react";
import useWebSocketLib from "react-use-websocket";
import { ACCESS_TOKEN } from "../constants";
import { setScreenshot } from "../stores/screenshotStore";

const useWebSocket = useWebSocketLib.default || useWebSocketLib;

// Construye la URL del WebSocket a partir de window.location (produccion)
// o la variable de entorno VITE_API_URL (desarrollo local)
function buildWsUrl() {
    let wsProtocol;
    let host;

    const apiUrl = import.meta.env.VITE_API_URL || "";

    if (apiUrl.startsWith("http")) {
        // Desarrollo: URL absoluta definida en .env
        wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
        host = apiUrl.replace(/^https?:\/\//, "").replace(/\/+$/, "");
    } else {
        // Produccion: URL relativa — usar window.location
        wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
        host = window.location.host;
    }

    const token = localStorage.getItem(ACCESS_TOKEN);
    const base = `${wsProtocol}://${host}/ws/dashboard/`;
    return token ? `${base}?token=${token}` : base;
}

// Hook que consume el WebSocket del dashboard y ejecuta el callback al recibir eventos
export default function useDashboardSocket({ onDeviceStatus, onScreenshot } = {}) {

    const socketUrl = useMemo(() => buildWsUrl(), []);

    useWebSocket(socketUrl, {
        shouldReconnect: () => true,
        reconnectAttempts: 10,
        reconnectInterval: (attemptNumber) =>
            Math.min(1000 * 2 ** attemptNumber, 30000),

        onMessage: (event) => {
            try {
                const payload = JSON.parse(event.data);
                console.log(payload);

                // Separa eventos de estado de dispositivo y capturas de pantalla
                if (payload.event === "screenshot") {
                    // Persiste la imagen en el nanostore (sessionStorage)
                    if (payload.mac && payload.image) {
                        setScreenshot(payload.mac, payload.image);
                    }
                    onScreenshot?.(payload);
                } else {
                    onDeviceStatus?.(payload);
                }
            } catch {
                console.warn("[useDashboardSocket] payload no válido:", event.data);
            }
        },

        onError: (event) => console.error("[useDashboardSocket] error:", event),
    });
}
