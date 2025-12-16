import React, { use, useEffect, useState } from 'react';
import {
    Paper,
    Typography,
    Avatar,
    Box,
    TextField,
    Button,
    Chip,
    Snackbar,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogContentText,
    DialogActions,
    Grid,
    CircularProgress
} from '@mui/material';

// Iconos
import SaveIcon from '@mui/icons-material/Save';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import BadgeIcon from '@mui/icons-material/Badge';
import KeyIcon from '@mui/icons-material/Key';
import WarningIcon from '@mui/icons-material/Warning';
import BoltIcon from '@mui/icons-material/Bolt';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import RefreshIcon from '@mui/icons-material/Refresh';

import '../styles/Profile.css';
import api from "../api";
import { jwtDecode } from "jwt-decode";
import { ACCESS_TOKEN } from "../constants"

const Profile = () => {

    const token = localStorage.getItem(ACCESS_TOKEN)
    const {user_id, is_superuser} = jwtDecode(token);
    // Estados
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [error, setError] = useState(false);
    const [loading, setloading] = useState(true);

    const [User, setUser] = useState({
        first_name: '',
        last_name: '',
        username: '',
        email: '',
        is_active: true,
        is_superuser: false,
        groups: [],
        password : "",
        password_validator: ""
    });

    const reloadProfile = async () =>{
            setloading(true)
            try{
                const userData = await api.get(`/users/${user_id}/`)
                if (userData.status === 200){
                    
                    setUser({
                        first_name: userData.data["first_name"],
                        last_name:  userData.data["last_name"],
                        username:   userData.data["username"],
                        email:  userData.data["email"],
                        is_active:  userData.data["is_active"],
                        is_superuser: is_superuser,
                        groups:  userData.data["groups"],
                        password : "",
                        password_validator: ""
                    }
                        
                    )
                
                }else{
                    setNotification({ open: true, message: 'No se ha podido cargar el perfil de usuario', severity: 'error' });
                }
            }catch(err){
                setNotification({ open: true, message: 'No se ha podido cargar el perfil de usuario', severity: 'error' });
                setError(true)
            }

            setloading(false)
            
        }
    
    useEffect(()=>{
        reloadProfile()
        
    },[])

    const handleInputChange = (e) => {
        setUser({ ...User, [e.target.name]: e.target.value });
    };

    const handlePreSave = () => {
        if (User.password || User.password_validator) {
            if (User.password !== User.password_validator) {
                setNotification({ open: true, message: 'Las contraseñas no coinciden', severity: 'error' });
                return;
            }
            if (User.password.length < 8) {
                setNotification({ open: true, message: 'La contraseña es muy corta (min 8)', severity: 'warning' });
                return;
            }
        }
        setConfirmOpen(true);
    };

    const handleConfirmSave = () => {
        setConfirmOpen(false);
        const changeProfile = async () =>{
            const patchUser = {...User}
            delete patchUser.groups; 
            delete patchUser.is_active;
            delete patchUser.is_superuser;
            if(!patchUser.password) delete patchUser.password
            if(!patchUser.password_validator) delete patchUser.password_validator

            try{
                const { data, status }  = await api.patch(`/users/${user_id}/`, patchUser)

                if(status === 200){
                    const updatedUser ={
                        ...User,
                        ...data,
                        password : "",
                        password_validator: ""
                    }
                    setUser(updatedUser)
                    setNotification({ open: true, message: 'Perfil actualizado correctamente', severity: 'success' });
                    
                }else{
                    throw new Error('Status no exitoso');
                }
            }catch(err){
                setNotification({ open: true, message: 'Error al guardar el usuario', severity: 'error' })
            }
        }
        
        changeProfile()
        
        
        

    };

    return (
        <div className="profile-container">
            
            {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <CircularProgress sx={{ color: '#8b5cf6' }} />
                </Box>
            )}
            
            {
                error &&
                (<Paper className="error-card" elevation={10}>
                        <CloudOffIcon sx={{ fontSize: 80, color: '#a1a1aa', mb: 3 }} />
                        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2, color: '#fff' }}>
                            Error de Conexión
                        </Typography>
                        <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 4, maxWidth: '320px', lineHeight: 1.6 }}>
                            No se pudo cambiar la Información de tu perfil
                        </Typography>
                        <Button 
                            variant="outlined" 
                            color="error" 
                            startIcon={<RefreshIcon />}
                            onClick={reloadProfile}
                        >
                            Reintentar
                        </Button>
                    </Paper>)
            }

            {!loading && !error && (
                <Paper className="main-card" elevation={10}>
                
                {/* --- PANE IZQUIERDO: VISUAL --- */}
                <div className="left-pane">
                    <Avatar 
                        className="profile-avatar"
                        src="https://i.pravatar.cc/300"
                        sx={{ width: 180, height: 180 }}
                    />
                    
                    <Typography variant="h4" className="white-text" sx={{ fontWeight: 'bold', mt: 1 }}>
                        {User.first_name}
                    </Typography>
                    <Typography variant="h5" className="white-text" sx={{ fontWeight: 300 }}>
                        {User.last_name}
                    </Typography>
                    
                    <Typography variant="body1" className="grey-text" sx={{ mt: 1 }}>
                        @{User.username}
                    </Typography>

                    <Chip 
                        icon={<VerifiedUserIcon />}
                        label={User.is_active ? "Cuenta Activa" : "Inactivo"}
                        className="status-chip"
                    />

                    {/* Lógica del Modo Dios */}
                    {User.is_superuser && (
                        <Chip
                            icon={<BoltIcon />}
                            label="MODO DIOS"
                            className="god-mode-chip"
                        />
                    )}

                    <Box sx={{ width: '100%', mt: 4 }}>
                        <Typography variant="caption" sx={{ color: '#8b5cf6', letterSpacing: 1 }}>
                            ROLES ASIGNADOS
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                            {User.groups.map((group, idx) => (
                                <Chip key={idx} label={group} size="small" className="group-chip" />
                            ))}
                        </Box>
                    </Box>
                </div>

                {/* --- PANE DERECHO: FORMULARIO --- */}
                <div className="right-pane">
                    
                    <div className="form-content">
                        
                        {/* Sección 1 */}
                        <Typography className="section-title">
                            <BadgeIcon /> Información Personal
                        </Typography>
                        
                        <Grid container spacing={3} sx={{ mb: 5 }}>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth className="profile-input"
                                    label="Nombre" name="first_name"
                                    value={User.first_name} onChange={handleInputChange}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth className="profile-input"
                                    label="Apellido" name="last_name"
                                    value={User.last_name} onChange={handleInputChange}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth className="profile-input"
                                    label="Usuario (Username)" name="username"
                                    value={User.username} onChange={handleInputChange}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth className="profile-input"
                                    label="Email" name="email" type="email"
                                    value={User.email} onChange={handleInputChange}
                                />
                            </Grid>
                        </Grid>

                        {/* Sección 2 */}
                        <Typography className="section-title" sx={{ color: '#f87171 !important' }}>
                            <KeyIcon /> Seguridad
                        </Typography>
                        <Typography variant="body2" className="grey-text" sx={{ mb: 2 }}>
                            Deja estos campos vacíos si no deseas cambiar la contraseña.
                        </Typography>

                        <Grid container spacing={3}>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth className="profile-input"
                                    label="Nueva Contraseña" name="password" type="password"
                                    value={User.password} onChange={handleInputChange}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth className="profile-input"
                                    label="Confirmar Contraseña" name="password_validator" type="password"
                                    value={User.password_validator} onChange={handleInputChange}
                                />
                            </Grid>
                        </Grid>
                    </div>

                    <div className="form-actions">
                        <Button 
                            variant="contained" 
                            size="large"
                            onClick={handlePreSave}
                            startIcon={<SaveIcon />}
                            sx={{ 
                                bgcolor: '#8b5cf6', 
                                color: 'white',
                                padding: '10px 30px',
                                fontWeight: 'bold',
                                '&:hover': { bgcolor: '#7c3aed' } 
                            }}
                        >
                            ACTUALIZAR PERFIL
                        </Button>
                    </div>
                </div>

            </Paper>
            )}

            {/* Modal de Confirmación */}
            <Dialog
                open={confirmOpen}
                onClose={() => setConfirmOpen(false)}
                PaperProps={{ style: { backgroundColor: '#1e1e1e', color: 'white', border: '1px solid #333' } }}
            >
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WarningIcon sx={{ color: '#f59e0b' }} /> Confirmar Cambios
                </DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ color: '#ccc' }}>
                        ¿Estás seguro de que deseas guardar los cambios realizados en tu perfil?
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmOpen(false)} sx={{ color: '#ccc' }}>Cancelar</Button>
                    <Button onClick={handleConfirmSave} variant="contained" sx={{ bgcolor: '#8b5cf6' }}>Confirmar</Button>
                </DialogActions>
            </Dialog>

            {/* Notificaciones */}
            <Snackbar 
                open={notification.open} 
                autoHideDuration={4000} 
                onClose={() => setNotification({ ...notification, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert severity={notification.severity} variant="filled" sx={{ width: '100%' }}>
                    {notification.message}
                </Alert>
            </Snackbar>
            
        </div>
    );
};

export default Profile;