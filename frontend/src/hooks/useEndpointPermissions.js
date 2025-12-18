import { useEffect, useState } from "react"
import api from "../api"
import { all } from "axios"


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
                
                // console.log(endpoint)
                // console.log(response)
                const {allow} =  response.headers
                // console.log(allow)
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
                // console.log(err)
                setPermissions({
                    canRead: false,
                    canCreate: false,
                    canUpdate: false,
                    canDelete: false,
                });
            }

            // console.log(permissions)
            
        }

        fetchPermissions()
        
    }, [endpoint])

    return permissions
}


export default useEndpointPermission

