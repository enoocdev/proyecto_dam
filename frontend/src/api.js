// Instancia de Axios con interceptores para autenticacion JWT
// Anade el token de acceso a cada peticion automaticamente
// Si el token caduca intenta refrescarlo y reenviar la peticion
import axios from "axios";
import { ACCESS_TOKEN, REFRESH_TOKEN, SERVER_URL } from "./constants";

// Obtiene la URL base:
//  En Tauri: usa la URL guardada por el usuario en localStorage
//  En web: siempre usa VITE_API_URL del .env
const isTauri = Boolean(window.__TAURI__);
const getBaseURL = () =>
    isTauri
        ? (localStorage.getItem(SERVER_URL) || import.meta.env.VITE_API_URL || "")
        : (import.meta.env.VITE_API_URL || "");

// Crea la instancia de Axios con la URL base del backend
const api = axios.create({
    baseURL: getBaseURL(),
})

// Interceptor de peticion que anade el token JWT en la cabecera
// y actualiza la baseURL por si el usuario la cambio en ajustes
api.interceptors.request.use((config) => {
    config.baseURL = getBaseURL();

    const token = localStorage.getItem(ACCESS_TOKEN)

    if (token){
        config.headers.Authorization = `Bearer ${token}`
    }

    return config
},
(error) => Promise.reject(error))

// Interceptor de respuesta que refresca el token si recibe un error de autenticacion
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const request = error.config
        if (error.response.status === 401 && !request._retry){
            request._retry = true
            
            try{

                const refreshToken = localStorage.getItem(REFRESH_TOKEN)
                
                const { data } = await axios.post("/token/refresh/", { refresh :  refreshToken},{baseURL: api.defaults.baseURL} )

                localStorage.setItem(ACCESS_TOKEN, data.access)

                const token = localStorage.getItem(ACCESS_TOKEN)

                if (token){
                    request.headers.Authorization = `bearer ${token}`
                }

                return api(request)

            }catch(refreshError){
                localStorage.clear()
                window.location.href = "/login";
                return Promise.reject(refreshError)
            }

        }

        return Promise.reject(error)
    }
    
)

export default api;