// Store global de las aulas asignadas al usuario autenticado
// Usa nanostores con persistencia en localStorage para evitar llamadas repetidas a la API

import { persistentAtom } from "@nanostores/persistent";

// Array de aulas asignadas: [{id, name}, ...]
export const $userClassrooms = persistentAtom("user-classrooms", [], {
    encode: JSON.stringify,
    decode: JSON.parse,
});

// Establece las aulas asignadas al usuario
export function setUserClassrooms(classrooms) {
    $userClassrooms.set(Array.isArray(classrooms) ? classrooms : []);
}

// Limpia las aulas almacenadas (al cerrar sesion)
export function clearUserClassrooms() {
    $userClassrooms.set([]);
}
