import React, { useState } from 'react';
import {
    Box, Typography
} from '@mui/material';

import GroupIcon from '@mui/icons-material/Group';


import UserGroup from "../components/UserGroup"

import '../styles/UserGroups.css';

const UserGroups = () => {
    const [groups, setGroups] = useState([
        { id: 1, name: 'Administradores', permissions: [1, 2] },
        { id: 2, name: 'Editores', permissions: [1, 3] },
        { id: 3, name: 'Lectores', permissions: [2] },
        { id: 4, name: 'Soporte', permissions: [5, 2] },
    ]);



    return (
        <div className="groups-container">
            
            <Box className="groups-header">
                <Typography variant="h5" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <GroupIcon sx={{ color: '#8b5cf6' }}/> 
                    Grupos
                </Typography>
            </Box>

            {/* LISTA LINEAL DE ARRIBA A ABAJO */}
            <div className="groups-list">
                {groups.map((group) => (
                    <UserGroup group={group}/>
                ))}
            </div>

        </div>
    );
};

export default UserGroups;