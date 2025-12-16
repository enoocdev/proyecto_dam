import { useEffect, useState } from "react"
import api from "../api"


const useEndpointPermission = (endpoint) => {
    const [permissions, setPermissions] = useState(
        {
            canCreate : false,
            canUpdate : false,
            canDelete : false,
        }
    )
    

    useEffect(() => {

        const fetchPermissions = async () =>{
            const {headers} = await api.options(endpoint)

            
            const allow = headers["allow"]

            

            setPermissions(
                {
                    canRead : allow.includes("GET"),
                    canCreate : allow.includes("POST"),
                    canUpdate : allow.includes("PUT") || allow.includes("PATCH"),
                    canDelete : allow.includes("DELETE"),
                }
            )
        }

        fetchPermissions()
        
    }, [endpoint])

    return permissions
}


export default useEndpointPermission