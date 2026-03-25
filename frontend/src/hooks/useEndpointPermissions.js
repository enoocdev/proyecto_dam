// Hook que consulta los permisos disponibles en un endpoint de la API
// Hace una peticion OPTIONS y extrae que acciones puede realizar el usuario
import { useEffect, useState } from "react"
import api from "../api"


const useEndpointPermission = (endpoint) => {
    const [permissions, setPermissions] = useState(
        {
            canRead : false,
            canCreate : false,
            canUpdate : false,
            canDelete : false,
        }
    )
    

    useEffect(() => {

        const fetchPermissions = async () =>{
            try {
                const response = await api.options(endpoint);
                
                const {allow} =  response.headers
                const actions = response.data?.actions;

                if (actions) {
                    setPermissions({
                        canRead: true,
                        canCreate: !!actions.POST,
                        canUpdate: !!(actions.PUT || actions.PATCH),
                        canDelete: !!actions.DELETE,
                    });
                } else {

                    setPermissions({
                        canRead: allow.includes("GET"),
                        canCreate: allow.includes("POST"),
                        canUpdate: allow.includes("PUT") || allow.includes("PATCH"),
                        canDelete: allow.includes("DELETE"),
                    });
                }
                
                
            } catch (err) {
                setPermissions({
                    canRead: false,
                    canCreate: false,
                    canUpdate: false,
                    canDelete: false,
                });
            }

        fetchPermissions()
        
    }}, [endpoint])

    return permissions
}


export default useEndpointPermission

