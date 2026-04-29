import axios from "axios";
import { ACCESS_TOKEN, REFRESH_TOKEN, USER_PERMISSIONS, SERVER_URL } from "./constants";

// Lee la base URL en el instante exacto del disparo (nunca en el arranque)
// para evitar race conditions con localStorage
const readBase = () => {
    let base = localStorage.getItem(SERVER_URL) || import.meta.env.VITE_API_URL || "";
    if (base && !base.endsWith("/")) base += "/";
    return base;
};

// Instancia sin baseURL: la URL absoluta se construye manualmente en el interceptor
// para evitar el bug de Axios que ignora cambios dinamicos de baseURL
const api = axios.create();

api.interceptors.request.use((config) => {
    const base = readBase();
    console.log("[api] base:", base, "| endpoint:", config.url);

    // Construir URL absoluta manualmente si aun no lo es
    if (config.url && !config.url.startsWith("http")) {
        config.url = base + config.url.replace(/^\//, "");
    }

    const token = localStorage.getItem(ACCESS_TOKEN);
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => Promise.reject(error));

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const request = error.config;
        if (error.response?.status === 401 && !request._retry) {
            request._retry = true;
            try {
                const refreshToken = localStorage.getItem(REFRESH_TOKEN);
                const base = readBase();

                // URL absoluta construida manualmente para el refresh
                const { data } = await axios.post(
                    base + "token/refresh/",
                    { refresh: refreshToken }
                );

                localStorage.setItem(ACCESS_TOKEN, data.access);
                request.headers.Authorization = `Bearer ${data.access}`;
                return api(request);
            } catch (refreshError) {
                // Borrar solo tokens, conservar SERVER_URL para el siguiente login
                localStorage.removeItem(ACCESS_TOKEN);
                localStorage.removeItem(REFRESH_TOKEN);
                localStorage.removeItem(USER_PERMISSIONS);
                window.location.href = "/login";
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export default api;