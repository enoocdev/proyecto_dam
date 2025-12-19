import React from 'react';
import { 
    Avatar, 
    IconButton, 
    Tooltip 
} from '@mui/material';

// Iconos
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import BoltIcon from '@mui/icons-material/Bolt';
import SecurityIcon from '@mui/icons-material/Security';


const UserCard = ({ user, onEdit, onDelete }) => {
    
    const getInitials = () => {
        if (user.first_name) return user.first_name[0].toUpperCase();
        if (user.username) return user.username[0].toUpperCase();
        return "?";
    };

    return (
        <div className="user-card">
            
            <div className="user-info">
                <Avatar 
                    sx={{ 
                        bgcolor: user.is_superuser ? '#f59e0b' : '#333',
                        width: 45, 
                        height: 45, 
                        fontWeight: 'bold',
                        color: '#fff'
                    }}
                    src={user.profile_picture || null}
                >
                    {getInitials()}
                </Avatar>
                
                <div className="user-names">
                    <h4>
                        {user.first_name} {user.last_name}
                    </h4>
                    <span>@{user.username}</span>
                </div>
            </div>

            {/* --- 2. RANGOS Y GRUPOS (CENTRO) --- */}
            <div className="user-roles">
                {/* Rango: Superusuario */}
                {user.is_superuser && (
                    <div className="role-chip admin">
                        <BoltIcon sx={{ fontSize: 16 }} /> GOD MODE
                    </div>
                )}
                
                {/* Rango: Staff */}
                {user.is_staff && (
                    <div className="role-chip staff">
                        <SecurityIcon sx={{ fontSize: 16 }} /> STAFF
                    </div>
                )}
                
                {user.groups && user.groups.map((group, index) => (
                    <div key={index} className="role-chip">
                        {group.name || group}
                    </div>
                ))}

                {!user.is_superuser && !user.is_staff && (!user.groups || user.groups.length === 0) && (
                    <span style={{ fontSize: '0.8rem', color: '#666' }}>Usuario estándar</span>
                )}
            </div>

            <div style={{ display: 'flex', gap: '5px' }}>
                <Tooltip title="Editar Usuario">
                    <IconButton 
                        onClick={() => onEdit(user)}
                        sx={{ color: '#a1a1aa', '&:hover':{ color: '#fff', bgcolor: 'rgba(255,255,255,0.1)'} }}
                    >
                        <EditIcon />
                    </IconButton>
                </Tooltip>

                <Tooltip title="Eliminar Usuario">
                    <IconButton 
                        onClick={() => onDelete(user.id)}
                        sx={{ color: '#ef4444', '&:hover':{ color: '#dc2626', bgcolor: 'rgba(239,68,68,0.1)'} }}
                    >
                        <DeleteIcon />
                    </IconButton>
                </Tooltip>
            </div>

        </div>
    );
};

export default UserCard;