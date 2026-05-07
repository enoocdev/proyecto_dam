// Hook que conecta al WebSocket del dashboard para recibir actualizaciones
import { useMemo } from "react";
import useWebSocketLib from "react-use-websocket";
import { ACCESS_TOKEN, SERVER_URL } from "../constants";
import { setScreenshot } from "../stores/screenshotStore";

const useWebSocket = useWebSocketLib.default || useWebSocketLib;

function buildWsUrl() {
    let wsProtocol;
    let hostPath;

    // Obtenemos la URL base del setup (o de la variable de entorno si no hay setup)
    const apiUrl = localStorage.getItem(SERVER_URL) || import.meta.env.VITE_API_URL || "";

    if (apiUrl.startsWith("http")) {
        // Determinar protocolo
        wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";

        hostPath = apiUrl.replace(/^https?:\/\//, "").replace(/\/+$/, "");
    } else {
        // Fallback para produccion relativa
        wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
        hostPath = window.location.host;
    }

    const token = localStorage.getItem(ACCESS_TOKEN);
    const base = `${wsProtocol}://${hostPath}/ws/dashboard/`;
    
    return token ? `${base}?token=${token}` : base;
}

export default function useDashboardSocket({ onDeviceStatus, onScreenshot } = {}) {
    const socketUrl = useMemo(() => buildWsUrl(), []);

    useWebSocket(socketUrl, {
        shouldReconnect: () => true,
        reconnectAttempts: 10,
        reconnectInterval: (attemptNumber) =>
            Math.min(1000 * 2 ** attemptNumber, 30000),

        onMessage: (event) => {
            try {
                console.log(event)
                const payload = JSON.parse(event.data);
                if (payload.event === "screenshot") {
                    if (payload.mac && payload.image) {
                        setScreenshot(payload.mac, payload.image);
                    }
                    onScreenshot?.(payload);
                } else {
                    onDeviceStatus?.(payload);
                }
            } catch {
                console.warn("[useDashboardSocket] payload no valido:", event.data);
            }
        },

        onOpen: () => console.log("[useDashboardSocket] Conectado con exito a:", socketUrl),
        onError: (event) => console.error("[useDashboardSocket] error de conexion:", event),
    });
}