// Instancia de Axios con interceptores para autenticacion JWT
// Anade el token de acceso a cada peticion automaticamente
// Si el token caduca intenta refrescarlo y reenviar la peticion
import axios from "axios";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "./constants";

// Crea la instancia de Axios con la URL base del backend
const api = axios.create(
    {
        baseURL: import.meta.env.VITE_API_URL
    }
)

// Interceptor de peticion que anade el token JWT en la cabecera
api.interceptors.request.use((config) => {
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