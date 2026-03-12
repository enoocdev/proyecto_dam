// Store global de capturas de pantalla de los dispositivos
// Usa nanostores con persistencia en sessionStorage para que las imágenes
// sobrevivan a cambios de página dentro de la SPA y a refrescos del navegador

import { persistentMap } from "@nanostores/persistent";

// Mapa persistente: clave = MAC del dispositivo, valor = data URI de la imagen
// Se almacena en sessionStorage (se borra al cerrar la pestaña, no ocupa localStorage)
export const $screenshots = persistentMap("screenshots:", {}, {
    encode: JSON.stringify,
    decode: JSON.parse,
    listen: true,
    storage: typeof window !== "undefined" ? sessionStorage : undefined,
});

// Guarda o actualiza la captura de un dispositivo por su MAC
export function setScreenshot(mac, base64Image) {
    $screenshots.setKey(mac, `data:image/jpeg;base64,${base64Image}`);
}

// Devuelve la captura de un dispositivo concreto (o null si no hay)
export function getScreenshot(mac) {
    return $screenshots.get()[mac] || null;
}

// Limpia todas las capturas almacenadas
export function clearScreenshots() {
    const current = $screenshots.get();
    for (const key of Object.keys(current)) {
        $screenshots.setKey(key, undefined);
    }
}
