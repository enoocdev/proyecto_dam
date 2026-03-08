// Tarjeta de usuario que muestra su informacion roles y acciones de edicion y eliminacion
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
                        bgcolor: user.is_superuser ? '#f59e0b' : 'var(--border-color)',
                        width: 45, 
                        height: 45, 
                        fontWeight: 'bold',
                        color: 'var(--text-on-accent)'
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

            {/* Roles y grupos del usuario */}
            <div className="user-roles">
                {/* Rango Superusuario */}
                {user.is_superuser && (
                    <div className="role-chip admin">
                        <BoltIcon sx={{ fontSize: 16 }} /> GOD MODE
                    </div>
                )}
                
                {/* Rango Staff */}
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
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Usuario estándar</span>
                )}
            </div>

            <div style={{ display: 'flex', gap: '5px' }}>
                <Tooltip title="Editar Usuario">
                    <IconButton 
                        onClick={() => onEdit(user)}
                        sx={{ color: 'var(--text-secondary)', '&:hover':{ color: 'var(--text-primary)', bgcolor: 'var(--hover-bg-strong)'} }}
                    >
                        <EditIcon />
                    </IconButton>
                </Tooltip>

                <Tooltip title="Eliminar Usuario">
                    <IconButton 
                        onClick={() => onDelete(user)}
                        sx={{ color: 'var(--danger-color)', '&:hover':{ color: 'var(--danger-hover)', bgcolor: 'var(--danger-bg)'} }}
                    >
                        <DeleteIcon />
                    </IconButton>
                </Tooltip>
            </div>

        </div>
    );
};

export default UserCard;