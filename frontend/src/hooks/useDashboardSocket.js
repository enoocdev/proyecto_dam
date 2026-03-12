// Hook que conecta al WebSocket del dashboard para recibir actualizaciones
// Construye la URL a partir de la variable de entorno y gestiona la reconexion
import { useMemo } from "react";
import useWebSocketLib from "react-use-websocket";
import { ACCESS_TOKEN } from "../constants";

const useWebSocket = useWebSocketLib.default || useWebSocketLib;

// Construye la URL del WebSocket a partir de la URL de la API
function buildWsUrl() {
    const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
    const host = apiUrl.replace(/^https?:\/\//, "").replace(/\/+$/, "");
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
