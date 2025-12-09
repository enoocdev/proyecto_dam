import { useEffect, useState } from "react"
import { jwtDecode } from "jwt-decode";
import { ACCESS_TOKEN } from "../constants";
import api from "../api"


function Profile(){
    const [user,setUser] = useState()

    useEffect(()=>{
        const loadingProfileData = async () => {
            const  token = localStorage.getItem(ACCESS_TOKEN)
            const { user_id } = jwtDecode(token)
            
            const {data} = await api.get(`/users/${user_id}/`)

            console.log(data)
            

            setUser(
                JSON.stringify(data)
            )
        } 

        loadingProfileData()
    },[])

    return(
        <div>
            <p>{user}</p>
        </div>
    )
}

export default Profile