import { Link, useLocation } from "react-router-dom";
import {
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
} from "@mui/material";
import "../styles/MainLayout.css";
import useEndpointPermission from "../hooks/useEndpointPermissions";
import { useEffect, useState } from "react";
import { ACCESS_TOKEN } from "../constants";

function  ProtecterMenuItem ({ item }){
    const location = useLocation()
    const token = localStorage.getItem(ACCESS_TOKEN)
    const {is_superuser} = token
    // const [mostrar, setMostrar] = useState(true)
    const { canRead } = useEndpointPermission(item.apiPath)
    
    
    
    // useEffect(()=>{
    //     const fetch = async() =>{
    //     try{
    //         await api.get(item.apiPath)

    //     }catch(ex){
    //         console.log(`Ocultando ${item.text} por error:`, ex.response?.status);
    //         setMostrar(false)
    //     }
        
    //     }

    //     fetch()
    // },[item.apiPath])
    

    if (!canRead && !is_superuser) return null;

    return (
        <ListItem disablePadding>
            <ListItemButton
                className="menu-item-btn"
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
            >
                <ListItemIcon>
                    {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
            </ListItemButton>
        </ListItem>
    );
}

export default ProtecterMenuItem